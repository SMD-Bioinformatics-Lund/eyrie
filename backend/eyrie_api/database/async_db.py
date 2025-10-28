"""Async MongoDB database connection using PyMongo native async."""

import logging
from typing import Optional
import os

# Use PyMongo native async API (no threading)
try:
    from pymongo.asynchronous.mongo_client import AsyncMongoClient
    from pymongo.asynchronous.collection import AsyncCollection
    from pymongo.asynchronous.database import AsyncDatabase
    PYMONGO_ASYNC_AVAILABLE = True
except ImportError as e:
    logging.error(f"PyMongo async not available: {e}")
    PYMONGO_ASYNC_AVAILABLE = False
    # Create dummy types for type hints
    AsyncMongoClient = None
    AsyncCollection = None
    AsyncDatabase = None

LOG = logging.getLogger(__name__)


class AsyncMongoDatabase:
    """Container for async database connection and collections."""

    def __init__(self) -> None:
        """Initialize the database container."""
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[AsyncDatabase] = None
        self.users: Optional[AsyncCollection] = None
        self.samples: Optional[AsyncCollection] = None

    async def connect(self) -> None:
        """Establish database connection and setup collections."""
        if not PYMONGO_ASYNC_AVAILABLE:
            raise RuntimeError("PyMongo async not available - cannot connect to database")

        if self.client is None:
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/eyrie?authSource=eyrie')
            LOG.info("=== MONGODB CONNECTION ATTEMPT ===")
            LOG.info("Connecting to MongoDB with PyMongo native async - NO THREADING!")
            LOG.info(f"MongoDB URI: {mongo_uri[:50]}...")  # Log partial URI for debugging
            LOG.info(f"PyMongo async client type: {type(AsyncMongoClient)}")

            try:
                # Create async client with PyMongo native async - disable monitoring threads
                self.client = AsyncMongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,  # Shorter timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    maxPoolSize=1,  # Minimize pool
                    minPoolSize=0,  # No minimum pool
                    heartbeatFrequencyMS=999999999,  # Disable periodic heartbeat
                    serverMonitoringMode='stream',  # Use stream monitoring instead of polling
                    # Disable background monitoring threads
                    directConnection=True,  # Direct connection to single server
                )
                LOG.info("PyMongo async client created successfully")

                # Test the connection
                LOG.info("Testing MongoDB connection with ping...")
                await self.client.admin.command('ping')
                LOG.info("MongoDB ping successful")

                # Setup database and collections
                self.db = self.client.eyrie
                self.users = self.db.users
                self.samples = self.db.samples

                LOG.info("=== MONGODB CONNECTION SUCCESSFUL ===")

            except Exception as e:
                LOG.error(f"=== MONGODB CONNECTION FAILED ===")
                LOG.error(f"Error type: {type(e).__name__}")
                LOG.error(f"Error message: {str(e)}")
                import traceback
                LOG.error(f"Traceback: {traceback.format_exc()}")
                # Re-raise to let caller handle the error
                raise

    async def close(self) -> None:
        """Close database connection."""
        if self.client:
            LOG.info("Closing MongoDB connection")
            self.client.close()
            self.client = None
            self.db = None
            self.users = None
            self.samples = None

    async def ensure_connected(self) -> None:
        """Ensure database connection is established."""
        if self.client is None:
            await self.connect()

# Global database instance
db_instance = AsyncMongoDatabase()
