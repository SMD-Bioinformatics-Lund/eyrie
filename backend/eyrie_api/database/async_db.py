"""Async MongoDB database connection using Motor."""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
import motor
import os

LOG = logging.getLogger(__name__)


class AsyncMongoDatabase:
    """Container for async database connection and collections."""

    def __init__(self) -> None:
        """Initialize the database container."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.users: Optional[AsyncIOMotorCollection] = None
        self.samples: Optional[AsyncIOMotorCollection] = None

    async def connect(self) -> None:
        """Establish database connection and setup collections."""
        if self.client is None:
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/eyrie?authSource=eyrie')
            
            LOG.info("=== MONGODB CONNECTION ATTEMPT ===")
            LOG.info("Connecting to MongoDB with async Motor client - NO THREADING!")
            LOG.info(f"MongoDB URI: {mongo_uri[:50]}...")  # Log partial URI for debugging
            LOG.info(f"Using Motor version: {getattr(motor, '__version__', 'unknown')}")
            LOG.info(f"Motor client type: {type(AsyncIOMotorClient)}")
            
            try:
                # Create async client with minimal settings to avoid threading issues
                self.client = AsyncIOMotorClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,  # Shorter timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    maxPoolSize=1,  # Minimize pool to reduce thread creation
                    minPoolSize=0,  # No minimum pool
                    # Disable all background operations that might create threads
                    heartbeatFrequencyMS=60000,  # Reduce heartbeat frequency
                    # Motor handles async operations without background threads
                )
                LOG.info("Motor client created successfully")
                
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