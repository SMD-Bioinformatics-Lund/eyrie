from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import generate_password_hash
import os

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/eyrie?authSource=eyrie')
client = MongoClient(mongo_uri)
db = client.eyrie

def init_default_user():
    """Initialize default admin user if none exists"""
    if db.users.count_documents({}) == 0:
        admin_user = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password_hash': generate_password_hash('admin'),
            'role': 'admin',
            'created_date': datetime.now(),
            'is_active': True
        }
        db.users.insert_one(admin_user)
        print("Default admin user created: admin/admin")
