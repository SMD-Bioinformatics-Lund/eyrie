from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from functools import wraps
from typing import Callable, Any
import os
import json

# Global variables that will be set in create_app()
db = None
USE_MONGO = False
sessions = {}
users_db = {}
samples_db = []

# Custom JSON encoder for MongoDB ObjectId and datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Authentication models
class TokenObject:
    """Token object for authentication"""
    def __init__(self, token: str, type: str = "Bearer"):
        self.token = token
        self.type = type

# Pydantic-like models (simple classes for Flask)
class LoginRequest:
    def __init__(self, data):
        self.username = data.get('username')
        self.password = data.get('password')

class UserCreate:
    def __init__(self, data):
        self.username = data.get('username')
        self.email = data.get('email')
        self.password = data.get('password')
        self.role = data.get('role', 'user')

class UserUpdate:
    def __init__(self, data):
        self.email = data.get('email')
        self.password = data.get('password')
        self.role = data.get('role')
        self.is_active = data.get('is_active')

class QCUpdate:
    def __init__(self, data):
        self.qc = data.get('qc')
        self.comments = data.get('comments', '')

class CommentUpdate:
    def __init__(self, data):
        self.comments = data.get('comments')

# Database helper functions
def init_default_user():
    """Initialize default admin user"""
    global db, USE_MONGO, users_db, samples_db

    if USE_MONGO:
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
    else:
        if 'admin' not in users_db:
            users_db['admin'] = {
                '_id': 'admin_id',
                'username': 'admin',
                'email': 'admin@example.com',
                'password_hash': generate_password_hash('admin'),
                'role': 'admin',
                'created_date': datetime.now(),
                'is_active': True
            }
            # Add sample data for demo
            samples_db.extend([
                {
                    'sample_id': 'S001',
                    'sample_name': 'Test Sample 1',
                    'sequencing_run_id': 'RUN001',
                    'lims_id': 'LIMS001',
                    'classification': '16S',
                    'qc': 'passed',
                    'comments': 'Test sample',
                    'created_date': datetime.now(),
                    'updated_date': datetime.now(),
                    'krona_file': None,
                    'quality_plot': None,
                    'pipeline_files': [],
                    'statistics': {
                        'total_reads': 10000,
                        'quality_passed': 8500,
                        'avg_length': 150,
                        'avg_quality': 35.2
                    }
                },
                {
                    'sample_id': 'S002',
                    'sample_name': 'Test Sample 2',
                    'sequencing_run_id': 'RUN002',
                    'lims_id': 'LIMS002',
                    'classification': 'ITS',
                    'qc': 'unprocessed',
                    'comments': '',
                    'created_date': datetime.now(),
                    'updated_date': datetime.now(),
                    'krona_file': None,
                    'quality_plot': None,
                    'pipeline_files': [],
                    'statistics': {
                        'total_reads': 12000,
                        'quality_passed': 9600,
                        'avg_length': 145,
                        'avg_quality': 33.8
                    }
                }
            ])
            print("Default admin user and sample data created: admin/admin")

def find_user(query):
    """Find user by query"""
    global db, USE_MONGO, users_db

    if USE_MONGO:
        return db.users.find_one(query)
    else:
        username = query.get('username')
        if username and username in users_db:
            user = users_db[username]
            if query.get('is_active', True) and user.get('is_active', True):
                return user
        return None

def find_user_by_id(user_id):
    """Find user by ID"""
    global db, USE_MONGO, users_db

    if USE_MONGO:
        return db.users.find_one({'_id': ObjectId(user_id)})
    else:
        for user in users_db.values():
            if user['_id'] == user_id:
                return user
        return None

# Authentication helper functions
def get_current_user():
    global sessions
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None

    user_id = sessions[session_id].get("user_id")
    user = find_user_by_id(user_id)
    return user

def get_admin_user():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return None
    return user

def api_authentication(func: Callable[..., Any]) -> Callable[..., Any]:
    """Use authentication token for api.

    :param func: API function to wrap with API auth headers
    :type func: Callable
    :return: Wrapped API function
    :rtype: Callable
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Add authentication headers to API requests.

        :return: Wrapped API call function
        :rtype: Callable
        """
        # Check for session-based authentication (cookies)
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401

        # Add user to kwargs for the decorated function
        kwargs['current_user'] = user
        return func(*args, **kwargs)

    return wrapper

def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Require admin privileges for API endpoint.

    :param func: API function to wrap with admin auth
    :type func: Callable
    :return: Wrapped API function
    :rtype: Callable
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Check admin privileges for API requests.

        :return: Wrapped API call function
        :rtype: Callable
        """
        # Check for admin user
        admin_user = get_admin_user()
        if not admin_user:
            return jsonify({'error': 'Admin privileges required'}), 403

        # Add admin user to kwargs for the decorated function
        kwargs['current_user'] = admin_user
        return func(*args, **kwargs)

    return wrapper

def register_blueprints(app):
    """Register all Flask blueprints"""
    from .blueprints.samples.views import bp as samples_bp
    from .blueprints.sample.views import bp as sample_bp
    from .blueprints.admin.views import bp as admin_bp
    from .blueprints.login.views import bp as login_bp

    app.register_blueprint(samples_bp)
    app.register_blueprint(sample_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(login_bp)

def create_app():
    """Create and configure Flask application"""
    global db, USE_MONGO, sessions

    app = Flask(__name__)

    # CORS configuration
    CORS(app, origins=["*"], supports_credentials=True)

    # MongoDB connection with fallback to in-memory storage
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/eyrie?authSource=eyrie')
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        # Test connection
        client.server_info()
        db = client.eyrie
        print("✓ Connected to MongoDB")
        USE_MONGO = True
    except Exception as e:
        print(f"⚠️  MongoDB not available ({e}), using in-memory storage")
        USE_MONGO = False

    # Initialize session storage
    sessions = {}

    # Initialize default user on startup
    init_default_user()

    # Register blueprints
    register_blueprints(app)

    return app

# Authentication endpoints
@app.route("/api/auth/login", methods=['POST'])
def login():
    global sessions, USE_MONGO
    try:
        data = request.get_json()
        login_data = LoginRequest(data)

        user = find_user({'username': login_data.username, 'is_active': True})

        if user and check_password_hash(user['password_hash'], login_data.password):
            # Create session
            session_id = str(ObjectId()) if USE_MONGO else f"session_{len(sessions)}"
            sessions[session_id] = {
                'user_id': str(user['_id']),
                'username': user['username'],
                'role': user['role']
            }

            response = jsonify({
                'success': True,
                'user': {
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
            response.set_cookie(key="session_id", value=session_id, httponly=True)
            return response
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/auth/logout", methods=['POST'])
def logout():
    global sessions
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response = jsonify({'success': True})
    response.set_cookie(key="session_id", value='', expires=0)
    return response

@app.route("/api/auth/current-user", methods=['GET'])
@api_authentication
def current_user(current_user=None):
    try:
        return jsonify({
            'username': current_user['username'],
            'email': current_user['email'],
            'role': current_user['role']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User management endpoints (admin only)
@app.route("/api/admin/users", methods=['GET'])
@admin_required
def get_users(current_user=None):
    global db
    try:
        users = list(db.users.find({}, {'password_hash': 0}))  # Exclude password hash
        return json.loads(JSONEncoder().encode(users))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/users", methods=['POST'])
@admin_required
def create_user(current_user=None):
    global db
    try:
        data = request.get_json()
        user_data = UserCreate(data)

        # Validate input
        if not user_data.username or not user_data.email or not user_data.password:
            return jsonify({'error': 'Username, email, and password are required'}), 400

        if user_data.role not in ['user', 'admin', 'uploader']:
            return jsonify({'error': 'Invalid role'}), 400

        # Check if user already exists
        if db.users.find_one({'username': user_data.username}):
            return jsonify({'error': 'Username already exists'}), 400

        if db.users.find_one({'email': user_data.email}):
            return jsonify({'error': 'Email already exists'}), 400

        # Create user
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

        return jsonify({'success': True, 'user': user})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/users/<user_id>", methods=['PUT'])
@admin_required
def update_user(user_id, current_user=None):
    global db
    try:
        data = request.get_json()
        user_data = UserUpdate(data)

        update_data = {}
        if user_data.email is not None:
            update_data['email'] = user_data.email
        if user_data.role is not None:
            if user_data.role not in ['user', 'admin', 'uploader']:
                return jsonify({'error': 'Invalid role'}), 400
            update_data['role'] = user_data.role
        if user_data.is_active is not None:
            update_data['is_active'] = user_data.is_active
        if user_data.password:
            update_data['password_hash'] = generate_password_hash(user_data.password)

        update_data['updated_date'] = datetime.now()

        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/users/<user_id>", methods=['DELETE'])
@admin_required
def delete_user(user_id, current_user=None):
    global db
    try:
        # Prevent deleting the current user
        if str(current_user['_id']) == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400

        result = db.users.delete_one({'_id': ObjectId(user_id)})

        if result.deleted_count == 0:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sample endpoints
@app.route("/api/samples", methods=['GET'])
def get_samples():
    global db, USE_MONGO, samples_db
    try:
        if USE_MONGO:
            samples = list(db.samples.find())
            return json.loads(JSONEncoder().encode(samples))
        else:
            return json.loads(JSONEncoder().encode(samples_db))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/samples/<sample_id>", methods=['GET'])
def get_sample(sample_id):
    global db, USE_MONGO, samples_db
    try:
        if USE_MONGO:
            sample = db.samples.find_one({'sample_id': sample_id})
        else:
            sample = next((s for s in samples_db if s['sample_id'] == sample_id), None)

        if not sample:
            return jsonify({'error': 'Sample not found'}), 404
        return json.loads(JSONEncoder().encode(sample))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/samples/<sample_id>/qc", methods=['PUT'])
def update_qc(sample_id):
    global db
    try:
        data = request.get_json()
        qc_data = QCUpdate(data)

        if qc_data.qc not in ['passed', 'failed', 'unprocessed']:
            return jsonify({'error': 'Invalid QC status'}), 400

        result = db.samples.update_one(
            {'sample_id': sample_id},
            {
                '$set': {
                    'qc': qc_data.qc,
                    'comments': qc_data.comments,
                    'updated_date': datetime.now()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Sample not found'}), 404

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/samples/<sample_id>/comment", methods=['PUT'])
def update_comment(sample_id):
    global db
    try:
        data = request.get_json()
        comment_data = CommentUpdate(data)

        result = db.samples.update_one(
            {'sample_id': sample_id},
            {
                '$set': {
                    'comments': comment_data.comments,
                    'updated_date': datetime.now()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Sample not found'}), 404

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Static file serving for data files
@app.route("/data/<path:file_path>", methods=['GET'])
def serve_data_file(file_path):
    file_full_path = f"/app/data/{file_path}"
    if os.path.exists(file_full_path):
        return send_file(file_full_path)
    return jsonify({'error': 'File not found'}), 404

# Health check
@app.route("/health", methods=['GET'])
def health_check():
    global db
    try:
        db.samples.count_documents({})
        return jsonify({'status': 'healthy'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == "__main__":
    # For development only - use wsgi.py for production
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
