"""Database utility functions for async MongoDB operations."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from .async_db import AsyncMongoDatabase, db_instance

LOG = logging.getLogger(__name__)


async def get_database() -> AsyncMongoDatabase:
    """Get the database instance, ensuring it's connected and initialized."""
    await db_instance.ensure_connected()

    if not hasattr(db_instance, '_initialized'):
        try:
            await _init_default_user_lazy()
            db_instance._initialized = True
        except Exception as e:
            LOG.warning(f"Failed to initialize default user: {e}")
            db_instance._initialized = True

    return db_instance


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncMongoDatabase, None]:
    """
    Context manager for database connections.

    Usage:
        async with get_db_connection() as db:
            result = await db.users.find_one({"username": "admin"})
    """
    try:
        db = await get_database()
        yield db
    except Exception as e:
        LOG.error(f"Database operation failed: {e}")
        raise


async def _init_default_user_lazy() -> None:
    """Initialize default admin user if none exists (internal lazy version)."""
    try:
        await db_instance.ensure_connected()
        user_count = await db_instance.users.count_documents({})

        if user_count == 0:
            from datetime import datetime
            from werkzeug.security import generate_password_hash

            admin_user = {
                'username': 'admin',
                'email': 'admin@example.com',
                'password_hash': generate_password_hash('admin'),
                'role': 'admin',
                'created_date': datetime.now(),
                'is_active': True
            }

            await db_instance.users.insert_one(admin_user)
            LOG.info("Default admin user created lazily: admin/admin")
        else:
            LOG.info("Default admin user already exists, skipping creation")

    except Exception as e:
        LOG.error(f"Failed to initialize default user: {e}")
        raise


async def init_default_user() -> None:
    """Initialize default admin user if none exists (public interface)."""
    try:
        async with get_db_connection() as db:
            user_count = await db.users.count_documents({})

            if user_count == 0:
                from datetime import datetime
                from werkzeug.security import generate_password_hash

                admin_user = {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'password_hash': generate_password_hash('admin'),
                    'role': 'admin',
                    'created_date': datetime.now(),
                    'is_active': True
                }

                await db.users.insert_one(admin_user)
                LOG.info("Default admin user created: admin/admin")
            else:
                LOG.info("Default admin user already exists, skipping creation")

    except Exception as e:
        LOG.error(f"Failed to initialize default user: {e}")
        raise


async def close_database() -> None:
    """Close the database connection."""
    await db_instance.close()

