#!/usr/bin/env python3
"""
Local development server for Eyrie Sample Manager
This runs the Flask app with an in-memory database for quick testing
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'dev-secret-key-for-local-testing'
CORS(app, supports_credentials=True)

# In-memory database for local testing
users_db = {
    'admin': {
        '_id': 'admin_id',
        'username': 'admin',
        'email': 'admin@example.com',
        'password_hash': generate_password_hash('admin'),
        'role': 'admin',
        'created_date': datetime.now(),
        'is_active': True
    }
}

samples_db = [
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
    }
]

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        username = session.get('username')
        user = users_db.get(username)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        print(f"Login attempt: username={username}")
        
        user = users_db.get(username)
        
        if user and check_password_hash(user['password_hash'], password) and user.get('is_active'):
            session['user_id'] = user['_id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            print(f"Login successful for {username}")
            
            return jsonify({
                'success': True,
                'user': {
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
        else:
            print(f"Login failed for {username}: invalid credentials")
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/current-user', methods=['GET'])
@login_required
def current_user():
    try:
        username = session.get('username')
        user = users_db.get(username)
        if user:
            return jsonify({
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            })
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sample endpoints
@app.route('/api/samples', methods=['GET'])
def get_samples():
    return jsonify(samples_db)

@app.route('/api/samples/<sample_id>', methods=['GET'])
def get_sample(sample_id):
    sample = next((s for s in samples_db if s['sample_id'] == sample_id), None)
    if not sample:
        return jsonify({'error': 'Sample not found'}), 404
    return jsonify(sample)

# Admin endpoints
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    # Return users without password hashes
    users = []
    for user in users_db.values():
        user_copy = user.copy()
        del user_copy['password_hash']
        users.append(user_copy)
    return jsonify(users)

# Static file serving for frontend
@app.route('/')
def root():
    return send_from_directory('frontend/blueprints/samples/templates', 'index.html')

@app.route('/samples')
def samples_page():
    return send_from_directory('frontend/blueprints/samples/templates', 'index.html')

@app.route('/sample/<sample_id>')
def sample_detail(sample_id):
    return send_from_directory('frontend/blueprints/sample/templates', 'detail.html')

@app.route('/admin')
def admin_page():
    return send_from_directory('frontend/blueprints/admin/templates', 'dashboard.html')

@app.route('/login')
def login_page():
    return send_from_directory('frontend/blueprints/login/templates', 'index.html')

# Static assets
@app.route('/shared/static/<path:filename>')
def shared_static(filename):
    return send_from_directory('frontend/shared/static', filename)

@app.route('/blueprints/<path:filename>')
def blueprint_static(filename):
    return send_from_directory('frontend/blueprints', filename)

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'mode': 'local_development'})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Eyrie Sample Manager (Local Mode)")
    print("=" * 50)
    print("📍 URL: http://localhost:5000")
    print("🔐 Login: admin / admin")
    print("💡 This is a local development server with in-memory data")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
