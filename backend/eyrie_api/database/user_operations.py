from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash
from .connection import db

def find_user(query):
    """Find user by query"""
    return db.users.find_one(query)

def find_user_by_id(user_id):
    """Find user by ID"""
    return db.users.find_one({'_id': ObjectId(user_id)})

def get_all_users():
    """Get all users excluding password hash"""
    return list(db.users.find({}, {'password_hash': 0}))

def create_user(user_data):
    """Create a new user"""
    user = {
        'username': user_data.username,
        'email': user_data.email,
        'password_hash': generate_password_hash(user_data.password),
        'role': user_data.role,
        'created_date': datetime.now(),
        'is_active': True
    }

    result = db.users.insert_one(user)
    user['_id'] = str(result.inserted_id)
    del user['password_hash']  # Don't return password hash

    return user

def update_user(user_id, update_data):
    """Update user by ID"""
    if 'password' in update_data:
        update_data['password_hash'] = generate_password_hash(update_data['password'])
        del update_data['password']

    update_data['updated_date'] = datetime.now()

    result = db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )

    return result.matched_count > 0

def delete_user(user_id):
    """Delete user by ID"""
    result = db.users.delete_one({'_id': ObjectId(user_id)})
    return result.deleted_count > 0

def user_exists(username=None, email=None):
    """Check if user exists by username or email"""
    if username and db.users.find_one({'username': username}):
        return True
    if email and db.users.find_one({'email': email}):
        return True
    return False
