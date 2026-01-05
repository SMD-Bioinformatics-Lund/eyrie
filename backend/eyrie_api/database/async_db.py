"""Async MongoDB database connection using PyMongo native async."""

import logging
from typing import Optional
import os

try:
    from pymongo.asynchronous.mongo_client import AsyncMongoClient
    from pymongo.asynchronous.collection import AsyncCollection
    from pymongo.asynchronous.database import AsyncDatabase
    PYMONGO_ASYNC_AVAILABLE = True
except ImportError as e:
    logging.error(f"PyMongo async not available: {e}")
    PYMONGO_ASYNC_AVAILABLE = False
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
        self.seqruns: Optional[AsyncCollection] = None

    async def connect(self) -> None:
        """Establish database connection and setup collections."""
        if not PYMONGO_ASYNC_AVAILABLE:
            raise RuntimeError("PyMongo async not available - cannot connect to database")

        if self.client is None:
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/eyrie')
            LOG.info("=== MONGODB CONNECTION ATTEMPT ===")
            LOG.info("Connecting to MongoDB with PyMongo native async - NO THREADING!")
            LOG.info(f"MongoDB URI: {mongo_uri[:50]}...")
            LOG.info(f"PyMongo async client type: {type(AsyncMongoClient)}")

            try:
                self.client = AsyncMongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    maxPoolSize=1,
                    minPoolSize=0,
                    heartbeatFrequencyMS=999999999,
                    serverMonitoringMode='stream',
                    directConnection=True,
                )
                LOG.info("PyMongo async client created successfully")

                LOG.info("Testing MongoDB connection with ping...")
                await self.client.admin.command('ping')
                LOG.info("MongoDB ping successful")

                self.db = self.client.eyrie
                self.users = self.db.users
                self.samples = self.db.samples
                self.seqruns = self.db.seqruns

                LOG.info("=== MONGODB CONNECTION SUCCESSFUL ===")

            except Exception as e:
                LOG.error(f"=== MONGODB CONNECTION FAILED ===")
                LOG.error(f"Error type: {type(e).__name__}")
                LOG.error(f"Error message: {str(e)}")
                import traceback
                LOG.error(f"Traceback: {traceback.format_exc()}")
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
            self.seqruns = None

    async def ensure_connected(self) -> None:
        """Ensure database connection is established."""
        if self.client is None:
            await self.connect()

db_instance = AsyncMongoDatabase()
