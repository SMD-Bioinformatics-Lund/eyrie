"""Async user database operations."""

from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash
from typing import Optional, Dict, Any, List
from .utils import get_db_connection


async def find_user(query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find user by query."""
    async with get_db_connection() as db:
        return await db.users.find_one(query)


async def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Find user by ID."""
    async with get_db_connection() as db:
        return await db.users.find_one({'_id': ObjectId(user_id)})


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all users excluding password hash."""
    async with get_db_connection() as db:
        cursor = db.users.find({}, {'password_hash': 0})
        return await cursor.to_list(length=None)


async def create_user(user_data: Any) -> Dict[str, Any]:
    """Create a new user."""
    async with get_db_connection() as db:
        user = {
            'username': user_data.username,
            'email': user_data.email,
            'password_hash': generate_password_hash(user_data.password),
            'role': user_data.role,
            'created_date': datetime.now(),
            'is_active': True
        }

        result = await db.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
        del user['password_hash']  # Don't return password hash

        return user


async def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
    """Update user by ID."""
    async with get_db_connection() as db:
        if 'password' in update_data:
            update_data['password_hash'] = generate_password_hash(update_data['password'])
            del update_data['password']

        update_data['updated_date'] = datetime.now()

        result = await db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

        return result.matched_count > 0


async def delete_user(user_id: str) -> bool:
    """Delete user by ID."""
    async with get_db_connection() as db:
        result = await db.users.delete_one({'_id': ObjectId(user_id)})
        return result.deleted_count > 0


async def user_exists(username: Optional[str] = None, email: Optional[str] = None) -> bool:
    """Check if user exists by username or email."""
    async with get_db_connection() as db:
        if username and await db.users.find_one({'username': username}):
            return True
        if email and await db.users.find_one({'email': email}):
            return True
        return False