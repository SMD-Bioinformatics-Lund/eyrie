from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from datetime import datetime
from werkzeug.exceptions import HTTPException
from functools import wraps
from typing import Callable, Any
import os
import json
import urllib.request
import urllib.parse
import requests

# Global variables for sessions (frontend only handles sessions, all data from API)
sessions = {}
backend_url = None

# Custom JSON encoder for datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Authentication models
class TokenObject:
    """Token object for authentication"""
    def __init__(self, token: str, type: str = "Bearer"):
        self.token = token
        self.type = type




# Authentication helper functions
def get_current_user():
    """Get current user info from backend API"""
    global sessions, backend_url
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None

    session_data = sessions[session_id]
    backend_token = session_data.get('backend_token')
    
    if not backend_token:
        return None
    
    try:
        # Get user info from backend API
        response = requests.get(
            f"{backend_url}/api/auth/me",
            headers={'Authorization': f'Bearer {backend_token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException:
        return None

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
    from .blueprints.trends.views import trends_bp

    app.register_blueprint(samples_bp)
    app.register_blueprint(sample_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(trends_bp)

def create_app():
    """Create and configure Flask application"""
    global sessions

    app = Flask(__name__)

    # CORS configuration
    CORS(app, origins=["*"], supports_credentials=True)

    # Configure backend API connection with fallback URLs
    global backend_url, sessions
    
    # Primary backend URL from environment
    primary_backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie_backend:5000')
    
    # Fallback URLs to try in production environments
    fallback_urls = [
        primary_backend_url,
        'http://eyrie-backend:5000',  # Different naming convention
        'http://localhost:8000',      # Local fallback
        'http://127.0.0.1:8000',      # IP fallback
    ]
    
    backend_url = None
    
    # Initialize session storage (frontend only handles sessions)
    sessions = {}
    
    print(f"🔍 Testing backend connectivity...")
    print(f"   Primary URL: {primary_backend_url}")
    
    # Test backend connectivity and find working URL
    import requests
    for test_url in fallback_urls:
        try:
            print(f"   Testing: {test_url}")
            response = requests.get(f"{test_url}/health", timeout=3)
            if response.status_code == 200:
                backend_url = test_url
                print(f"✓ Backend connectivity successful: {backend_url} (status: {response.status_code})")
                break
        except Exception as e:
            print(f"   Failed: {test_url} - {e}")
    
    if not backend_url:
        backend_url = primary_backend_url  # Use primary as fallback
        print(f"⚠️  No backend connectivity established. Using primary URL: {backend_url}")
        print(f"   This may cause issues during operation")
    
    print("ℹ️  Frontend will handle sessions only, all data comes from backend API")

    # Register blueprints
    register_blueprints(app)

    # Authentication endpoints
    @app.route("/api/auth/login", methods=['POST'])
    def login():
        """Authenticate with backend API and store session locally"""
        global sessions
        try:
            data = request.get_json()
            
            # Forward login request to backend API
            backend_login_url = f"{backend_url}/api/auth/login"
            
            response = requests.post(
                backend_login_url,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                backend_data = response.json()
                backend_token = backend_data.get('access_token')
                user_data = backend_data.get('user', {})
                
                # Create frontend session
                session_id = f"session_{len(sessions)}_{datetime.now().timestamp()}"
                sessions[session_id] = {
                    'user_id': user_data.get('id'),  # Store user ID for compatibility
                    'username': user_data.get('username'),
                    'role': user_data.get('role'),
                    'backend_token': backend_token
                }

                response_data = jsonify({
                    'success': True,
                    'user': user_data
                })
                response_data.set_cookie(key="session_id", value=session_id, httponly=True)
                return response_data
            else:
                return jsonify({'error': 'Invalid credentials'}), response.status_code

        except requests.RequestException as e:
            return jsonify({'error': f'Backend connection failed: {str(e)}'}), 500
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
        """Get current user info from backend API"""
        try:
            # current_user is already fetched from backend API in get_current_user()
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
        """Proxy admin users request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            response = requests.get(
                f"{backend_url}/api/admin/users",
                headers={'Authorization': f'Bearer {backend_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/admin/users", methods=['POST'])
    @admin_required
    def create_user(current_user=None):
        """Proxy admin create user request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            data = request.get_json()
            
            response = requests.post(
                f"{backend_url}/api/admin/users",
                headers={'Authorization': f'Bearer {backend_token}'},
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/admin/users/<user_id>", methods=['PUT'])
    @admin_required
    def update_user(user_id, current_user=None):
        """Proxy admin update user request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            data = request.get_json()
            
            response = requests.put(
                f"{backend_url}/api/admin/users/{user_id}",
                headers={'Authorization': f'Bearer {backend_token}'},
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/admin/users/<user_id>", methods=['DELETE'])
    @admin_required
    def delete_user(user_id, current_user=None):
        """Proxy admin delete user request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            response = requests.delete(
                f"{backend_url}/api/admin/users/{user_id}",
                headers={'Authorization': f'Bearer {backend_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Sample endpoints
    @app.route("/api/samples", methods=['GET'])
    @api_authentication
    def get_samples(current_user=None):
        """Proxy samples request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            response = requests.get(
                f"{backend_url}/api/samples",
                headers={'Authorization': f'Bearer {backend_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/samples/<sample_id>", methods=['GET'])
    @api_authentication
    def get_sample(sample_id, current_user=None):
        """Proxy sample request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            response = requests.get(
                f"{backend_url}/api/samples/{sample_id}",
                headers={'Authorization': f'Bearer {backend_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/samples/<sample_id>/qc", methods=['PUT'])
    @api_authentication
    def update_qc(sample_id, current_user=None):
        """Proxy QC update request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            data = request.get_json()
            
            response = requests.put(
                f"{backend_url}/api/samples/{sample_id}/qc",
                headers={'Authorization': f'Bearer {backend_token}'},
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/samples/<sample_id>/comment", methods=['PUT'])
    @api_authentication
    def update_comment(sample_id, current_user=None):
        """Proxy comment update request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            data = request.get_json()
            
            response = requests.put(
                f"{backend_url}/api/samples/{sample_id}/comment",
                headers={'Authorization': f'Bearer {backend_token}'},
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/samples/<sample_id>/species-flags", methods=['PUT'])
    @api_authentication
    def update_species_flags(sample_id, current_user=None):
        """Proxy species flags update request to backend API"""
        try:
            session_id = request.cookies.get("session_id")
            backend_token = sessions[session_id].get('backend_token') if session_id in sessions else None
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            data = request.get_json()
            
            response = requests.put(
                f"{backend_url}/api/samples/{sample_id}/species-flags",
                headers={'Authorization': f'Bearer {backend_token}'},
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Backend request failed'}), response.status_code
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Static file serving for data files
    @app.route("/data/<path:file_path>", methods=['GET'])
    def serve_data_file(file_path):
        file_full_path = f"/app/data/{file_path}"
        if os.path.exists(file_full_path):
            return send_file(file_full_path)
        return jsonify({'error': 'File not found'}), 404

    # Static file serving for shared assets
    @app.route("/shared/static/<path:filename>", methods=['GET'])
    def serve_shared_static(filename):
        from flask import current_app
        static_dir = os.path.join(current_app.root_path, 'shared', 'static')
        return send_from_directory(static_dir, filename)

    # Static file serving for blueprint assets
    @app.route("/blueprints/<blueprint>/<path:filename>", methods=['GET'])
    def serve_blueprint_static(blueprint, filename):
        from flask import current_app
        static_dir = os.path.join(current_app.root_path, 'blueprints', blueprint)
        return send_from_directory(static_dir, filename)

    # Trends API proxy to backend
    @app.route("/api/trends/data", methods=['GET'])
    @api_authentication
    def trends_data_proxy(current_user=None):
        """Proxy trends data requests to FastAPI backend"""
        try:
            # Get the backend token from the current session
            session_id = request.cookies.get("session_id")
            backend_token = None
            
            if session_id and session_id in sessions:
                backend_token = sessions[session_id].get('backend_token')
            
            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401
            
            # Get query parameters from the request
            query_params = request.args.to_dict()
            query_string = urllib.parse.urlencode(query_params)
            
            # Forward request to FastAPI backend with authentication
            backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie_backend:5000')
            full_url = f"{backend_url}/api/trends/data?{query_string}"
            
            # Create request with Authorization header
            req = urllib.request.Request(
                full_url,
                headers={'Authorization': f'Bearer {backend_token}'}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return jsonify(data)
                else:
                    return jsonify({'error': 'Backend request failed'}), response.status
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Health check
    @app.route("/health", methods=['GET'])
    def health_check():
        """Health check endpoint with backend connectivity details"""
        try:
            import os
            # Check if backend is reachable
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                return jsonify({
                    'status': 'healthy', 
                    'backend': 'connected',
                    'backend_url': backend_url,
                    'container_name': os.getenv('HOSTNAME', 'unknown'),
                    'environment': os.getenv('ENVIRONMENT', 'unknown')
                })
            else:
                return jsonify({
                    'status': 'unhealthy', 
                    'backend': 'unreachable',
                    'backend_url': backend_url,
                    'backend_status': response.status_code
                }), 500
        except Exception as e:
            return jsonify({
                'status': 'unhealthy', 
                'error': str(e),
                'backend_url': backend_url,
                'container_name': os.getenv('HOSTNAME', 'unknown')
            }), 500

    return app

if __name__ == "__main__":
    # For development only - use wsgi.py for production
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
