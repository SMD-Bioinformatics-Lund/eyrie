from flask import Flask, Blueprint, request, jsonify, send_file, send_from_directory, redirect, render_template, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user as flask_current_user
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

def register_blueprints(app, base_path=None):
    """Register all Flask blueprints with optional base path"""
    # Register login blueprint
    from .blueprints.login.views import bp as login_bp
    app.register_blueprint(login_bp, url_prefix=base_path)
    
    # Register individual sample views blueprint
    from .blueprints.sample.views import bp as sample_bp
    app.register_blueprint(sample_bp, url_prefix=base_path)
    
    # Register admin blueprint
    from .blueprints.admin.views import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix=base_path)
    
    # Register samples blueprint 
    from .blueprints.samples.views import bp as samples_bp
    app.register_blueprint(samples_bp, url_prefix=base_path)
    
    # Register trends blueprint
    from .blueprints.trends.views import trends_bp
    app.register_blueprint(trends_bp, url_prefix=base_path)

def create_app():
    """Create and configure Flask application"""
    global sessions

    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # CORS configuration
    CORS(app, origins=["*"], supports_credentials=True)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access with proper URL generation"""
        from flask import request, redirect, url_for
        # Always use Flask's url_for which respects APPLICATION_ROOT and base_path
        return redirect(url_for('login.login', next=request.url))

    @login_manager.user_loader
    def load_user(user_id):
        """Load user from session data"""
        from .blueprints.login.views import LoginUser, TokenObject
        try:
            print(f"User loader called with user_id: {user_id}")
            # user_id should be a string (session ID), not token dict
            from flask import session
            print(f"Session data: {dict(session)}")
            if user_id and session.get('username'):
                # Reconstruct user from session data
                user_data = {
                    'username': session.get('username', ''),
                    'email': session.get('email', ''),
                    'role': session.get('role', '')
                }
                # Create a dummy token (actual token stored in session during API calls)
                token_data = TokenObject(user_id, 'Bearer')
                user = LoginUser(user_data, token_data)
                print(f"User loaded successfully: {user_data}")
                return user
        except Exception as e:
            print(f"User loader error: {e}")
        print("User loader returning None")
        return None

    # Get base path from environment for Apache proxy setup
    base_path = os.getenv('EXTERNAL_BASE_PATH', '').rstrip('/')
    print(f"🔍 EXTERNAL_BASE_PATH: '{os.getenv('EXTERNAL_BASE_PATH', 'NOT SET')}'")
    print(f"🔍 base_path: '{base_path}'")
    
    # Set APPLICATION_ROOT for proper URL generation with base path
    if base_path:
        app.config['APPLICATION_ROOT'] = base_path
        # Configure session cookie to work with base path
        app.config['SESSION_COOKIE_PATH'] = base_path or '/'
        print(f"✅ Set APPLICATION_ROOT to: '{base_path}'")
        print(f"✅ Set SESSION_COOKIE_PATH to: '{base_path or '/'}'")
    else:
        app.config['SESSION_COOKIE_PATH'] = '/'
    
    # Create main blueprint with dynamic URL prefix
    main_bp = Blueprint('main', __name__, url_prefix=base_path or None)

    # Configure backend API connection with fallback URLs
    global backend_url, sessions

    # Primary backend URL from environment
    primary_backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie_backend:5000')

    # Fallback URLs to try in different deployment environments
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

    # Test backend connectivity and find working URL with retries
    import requests
    import time
    
    max_retries = 3
    for attempt in range(max_retries):
        for test_url in fallback_urls:
            try:
                print(f"   Testing: {test_url} (attempt {attempt + 1}/{max_retries})")
                response = requests.get(f"{test_url}/health", timeout=5)
                if response.status_code == 200:
                    backend_url = test_url
                    print(f"✓ Backend connectivity successful: {backend_url} (status: {response.status_code})")
                    break
            except Exception as e:
                print(f"   Failed: {test_url} - {e}")
        
        if backend_url:
            break
        
        if attempt < max_retries - 1:
            print(f"   Retrying in 2 seconds...")
            time.sleep(2)

    if not backend_url:
        backend_url = primary_backend_url  # Use primary as fallback
        print(f"⚠️  No backend connectivity established. Using primary URL: {backend_url}")
        print(f"   This may cause issues during operation")

    print("ℹ️  Frontend will handle sessions only, all data comes from backend API")


    @main_bp.route("/api/auth/current-user", methods=['GET'])
    @login_required
    def current_user_api():
        """Get current user info from Flask-Login session"""
        try:
            if flask_current_user.is_authenticated:
                return jsonify({
                    'username': flask_current_user.username,
                    'email': flask_current_user.email,
                    'role': flask_current_user.role
                })
            else:
                return jsonify({'error': 'Not authenticated'}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # User management endpoints (admin only)
    @main_bp.route("/api/admin/users", methods=['GET'])
    @login_required
    def get_users():
        """Proxy admin users request to backend API"""
        try:
            # Check if user is admin
            if not flask_current_user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403

            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/admin/users", methods=['POST'])
    @login_required
    def create_user():
        """Proxy admin create user request to backend API"""
        try:
            # Check if user is admin
            if not flask_current_user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403

            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/admin/users/<user_id>", methods=['PUT'])
    @admin_required
    def update_user(user_id, current_user=None):
        """Proxy admin update user request to backend API"""
        try:
            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/admin/users/<user_id>", methods=['DELETE'])
    @admin_required
    def delete_user(user_id, current_user=None):
        """Proxy admin delete user request to backend API"""
        try:
            backend_token = session.get('backend_token')

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
    @main_bp.route("/api/samples", methods=['GET'])
    @login_required
    def get_samples():
        """Proxy samples request to backend API"""
        try:
            from flask import session
            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/samples/<sample_id>", methods=['GET'])
    @login_required
    def get_sample(sample_id):
        """Proxy sample request to backend API"""
        try:
            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/samples/<sample_id>/qc", methods=['PUT'])
    @login_required
    def update_qc(sample_id):
        """Proxy QC update request to backend API"""
        try:
            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/samples/<sample_id>/comment", methods=['PUT'])
    @login_required
    def update_comment(sample_id):
        """Proxy comment update request to backend API"""
        try:
            backend_token = session.get('backend_token')

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

    @main_bp.route("/api/samples/<sample_id>/species-flags", methods=['PUT'])
    @login_required
    def update_species_flags(sample_id):
        """Proxy species flags update request to backend API"""
        try:
            backend_token = session.get('backend_token')

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
    @main_bp.route("/data/<path:file_path>", methods=['GET'])
    def serve_data_file(file_path):
        file_full_path = f"/app/data/{file_path}"
        if os.path.exists(file_full_path):
            return send_file(file_full_path)
        return jsonify({'error': 'File not found'}), 404

    # Static file serving for shared assets
    @main_bp.route("/shared/static/<path:filename>", methods=['GET'])
    def serve_shared_static(filename):
        from flask import current_app
        static_dir = os.path.join(current_app.root_path, 'shared', 'static')
        return send_from_directory(static_dir, filename)

    # Static file serving for blueprint assets
    @main_bp.route("/blueprints/<blueprint>/<path:filename>", methods=['GET'])
    def serve_blueprint_static(blueprint, filename):
        from flask import current_app
        static_dir = os.path.join(current_app.root_path, 'blueprints', blueprint)
        return send_from_directory(static_dir, filename)

    # Trends API proxy to backend
    @main_bp.route("/api/trends/data", methods=['GET'])
    @login_required
    def trends_data_proxy():
        """Proxy trends data requests to FastAPI backend"""
        try:
            backend_token = session.get('backend_token')

            if not backend_token:
                return jsonify({'error': 'Backend authentication required'}), 401

            # Get query parameters from the request
            query_params = request.args.to_dict()
            query_string = urllib.parse.urlencode(query_params)

            # Forward request to FastAPI backend with authentication
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

    # Frontend page routes using blueprint - only keep root redirect
    # Other page routes are now handled by their respective blueprints


    # Health check (also add to main blueprint for base path support)
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

    # Health check for base path support
    @main_bp.route("/health", methods=['GET'])
    def health_check_base_path():
        """Health check endpoint with backend connectivity details (base path version)"""
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
                    'environment': os.getenv('ENVIRONMENT', 'unknown'),
                    'base_path': base_path
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
                'container_name': os.getenv('HOSTNAME', 'unknown'),
                'base_path': base_path
            }), 500

    # Register other blueprints first with base path
    register_blueprints(app, base_path)
    
    # Register main blueprint with base path after all routes are defined
    app.register_blueprint(main_bp)

    return app

if __name__ == "__main__":
    # For development only - use wsgi.py for production
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
