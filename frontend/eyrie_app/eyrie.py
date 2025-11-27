"""
Core Eyrie functionality for API communication and backend connectivity
"""
import os
import requests
import time
import urllib.parse
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from requests.structures import CaseInsensitiveDict

from flask import redirect, url_for, jsonify, send_file, current_app, send_from_directory, session
from flask_login import current_user

from .config import settings


# Global backend URL storage
backend_url: Optional[str] = None


class TokenObject:
    """Token object for authentication"""
    def __init__(self, token: str, type: str = "Bearer"):
        self.token = token
        self.type = type


def test_backend_connectivity() -> str:
    """Test backend connectivity and return working URL"""
    global backend_url

    print(f"🔍 Testing backend connectivity...")
    print(f"   Primary URL: {settings.internal_backend_url}")

    max_retries = 3
    for attempt in range(max_retries):
        for test_url in settings.backend_fallback_urls:
            try:
                print(f"   Testing: {test_url} (attempt {attempt + 1}/{max_retries})")
                response = requests.get(f"{test_url}/api/system/health", timeout=5)
                if response.status_code == 200:
                    backend_url = test_url
                    print(f"✓ Backend connectivity successful: {backend_url} (status: {response.status_code})")
                    return backend_url
            except Exception as e:
                print(f"   Failed: {test_url} - {e}")

        if backend_url:
            break

        if attempt < max_retries - 1:
            print(f"   Retrying in 2 seconds...")
            time.sleep(2)

    if not backend_url:
        backend_url = settings.internal_backend_url  # Use primary as fallback
        print(f"⚠️  No backend connectivity established. Using primary URL: {backend_url}")
        print(f"   This may cause issues during operation")

    return backend_url


# Authentication decorators for view routes (redirects)
def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require authentication for view routes.
    Uses Flask-Login for authentication.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            return redirect(url_for('login.login'))

        # Add user to kwargs for the decorated function
        kwargs['current_user'] = current_user
        return func(*args, **kwargs)

    return wrapper


def role_required(allowed_roles: List[str]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to require specific roles for view routes.
    Uses Flask-Login for authentication.

    Args:
        allowed_roles: List of roles that are allowed to access the view
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                return redirect(url_for('login.login'))

            if current_user.role not in allowed_roles:
                # Redirect to samples page if user doesn't have required role
                return redirect(url_for('samples.samples'))

            # Add user to kwargs for the decorated function
            kwargs['current_user'] = current_user
            return func(*args, **kwargs)

        return wrapper
    return decorator


def admin_required_view(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require admin role for view routes.
    Shorthand for @role_required(['admin'])
    """
    return role_required(['admin'])(func)


def uploader_or_admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require uploader or admin role for view routes.
    Shorthand for @role_required(['admin', 'uploader'])
    """
    return role_required(['admin', 'uploader'])(func)


# API-specific decorators (return JSON errors instead of redirects)
def api_authentication_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Use Flask-Login authentication for API endpoints.
    Returns JSON error responses instead of redirects.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        # Add user to kwargs for the decorated function
        kwargs['current_user'] = current_user
        return func(*args, **kwargs)

    return wrapper


def admin_required_api(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Require admin privileges for API endpoints.
    Returns JSON error responses instead of redirects.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        if not current_user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403

        # Add user to kwargs for the decorated function
        kwargs['current_user'] = current_user
        return func(*args, **kwargs)

    return wrapper


def get_admin_user():
    """Get admin user using Flask-Login"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return None
    return current_user


def api_authentication(func):
    """
    Decorator for API functions that adds authentication headers
    Inspired by Bonsai pattern
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get backend token from session
        backend_token = session.get('backend_token')
        if not backend_token:
            raise ValueError("Backend authentication token not available")

        # Create headers dictionary
        headers = CaseInsensitiveDict()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = f'Bearer {backend_token}'

        # Add headers as first argument
        return func(headers, *args, **kwargs)

    return wrapper


@api_authentication
def get_current_user_from_backend(headers: CaseInsensitiveDict) -> Dict[str, Any]:
    """Get current user info from backend API"""
    url = f"{backend_url}/api/auth/current-user"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_samples_from_backend(headers: CaseInsensitiveDict) -> Dict[str, Any]:
    """Get samples from backend API"""
    url = f"{backend_url}/api/samples"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def create_sample(headers: CaseInsensitiveDict, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new sample"""
    url = f"{backend_url}/api/samples"
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_sample_from_backend(headers: CaseInsensitiveDict, sample_id: str) -> Dict[str, Any]:
    """Get specific sample from backend API"""
    url = f"{backend_url}/api/sample/{sample_id}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def update_sample_qc(headers: CaseInsensitiveDict, sample_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update sample QC status"""
    url = f"{backend_url}/api/sample/{sample_id}/qc"
    resp = requests.put(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def update_sample_comment(headers: CaseInsensitiveDict, sample_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update sample comment"""
    url = f"{backend_url}/api/sample/{sample_id}/comment"
    resp = requests.put(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def update_sample_species_flags(headers: CaseInsensitiveDict, sample_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update sample species flags"""
    url = f"{backend_url}/api/sample/{sample_id}/species-flags"
    resp = requests.put(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_admin_users(headers: CaseInsensitiveDict) -> Dict[str, Any]:
    """Get admin users from backend API"""
    url = f"{backend_url}/api/admin/users"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def create_admin_user(headers: CaseInsensitiveDict, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create admin user"""
    url = f"{backend_url}/api/admin/users"
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def update_admin_user(headers: CaseInsensitiveDict, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update admin user"""
    url = f"{backend_url}/api/admin/users/{user_id}"
    resp = requests.put(url, headers=headers, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def delete_admin_user(headers: CaseInsensitiveDict, user_id: str) -> Dict[str, Any]:
    """Delete admin user"""
    url = f"{backend_url}/api/admin/users/{user_id}"
    resp = requests.delete(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_trends_data(headers: CaseInsensitiveDict, query_params: Dict[str, str]) -> Dict[str, Any]:
    """Get trends data from backend API"""
    query_string = urllib.parse.urlencode(query_params)
    url = f"{backend_url}/api/trends/data?{query_string}"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_metadata_filters(headers: CaseInsensitiveDict) -> Dict[str, Any]:
    """Get metadata filters from backend API"""
    url = f"{backend_url}/api/trends/metadata/filters"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


# Additional API functions for Flask-Login user management
def get_current_user_api() -> Dict[str, Any]:
    """Get current user info from Flask-Login session"""
    if current_user.is_authenticated:
        return {
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role
        }
    else:
        raise ValueError("User not authenticated")


# Static file serving functions
def serve_analysis_file(file_path: str):
    """Serve analysis files from /app/analysis-files directory"""
    try:
        # Ensure the path is safe and within the analysis-files directory
        safe_path = os.path.normpath(file_path).lstrip('/')
        file_full_path = os.path.join('/app/analysis-files', safe_path)

        # Check if the file exists and is within the allowed directory
        if not file_full_path.startswith('/app/analysis-files/'):
            return jsonify({'error': 'Invalid file path'}), 400

        if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
            return send_file(file_full_path)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500


def serve_shared_static(filename: str):
    """Serve shared static assets"""
    static_dir = os.path.join(current_app.root_path, 'shared', 'static')
    return send_from_directory(static_dir, filename)


def serve_blueprint_static(blueprint: str, filename: str):
    """Serve blueprint-specific static assets"""
    static_dir = os.path.join(current_app.root_path, 'blueprints', blueprint)
    return send_from_directory(static_dir, filename)


# Health check functions
def health_check() -> Dict[str, Any]:
    """Health check with backend connectivity details"""
    try:
        # Check if backend is reachable
        response = requests.get(f"{backend_url}/api/system/health", timeout=5)
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'backend': 'connected',
                'backend_url': backend_url,
                'container_name': os.getenv('HOSTNAME', 'unknown'),
                'environment': settings.environment
            }
        else:
            return {
                'status': 'unhealthy',
                'backend': 'unreachable',
                'backend_url': backend_url,
                'backend_status': response.status_code
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'backend_url': backend_url,
            'container_name': os.getenv('HOSTNAME', 'unknown')
        }


def get_analysis_path_for_sample(sample_data: Dict[str, Any]) -> str:
    """Get the correct analysis results path for a sample based on pipeline_software"""
    
    pipeline_software = sample_data.get('pipeline_software', 'trana')
    analysis_path = settings.analysis_results_paths.get(pipeline_software, 
                                                       settings.analysis_results_paths['trana'])
    
    # Return path without /app/analysis-files prefixes for URL construction  
    if analysis_path.startswith('/app/analysis-files/'):
        result_path = analysis_path[len('/app/analysis-files/'):]
    else:
        # Fallback for unexpected paths
        result_path = 'results/trana' if pipeline_software == 'trana' else f'results/{pipeline_software}'
    
    return result_path


def health_check_base_path() -> Dict[str, Any]:
    """Health check with base path support"""
    try:
        # Check if backend is reachable
        response = requests.get(f"{backend_url}/api/system/health", timeout=5)
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'backend': 'connected',
                'backend_url': backend_url,
                'container_name': os.getenv('HOSTNAME', 'unknown'),
                'environment': settings.environment,
                'base_path': settings.external_base_path
            }
        else:
            return {
                'status': 'unhealthy',
                'backend': 'unreachable',
                'backend_url': backend_url,
                'backend_status': response.status_code
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'backend_url': backend_url,
            'container_name': os.getenv('HOSTNAME', 'unknown'),
            'base_path': settings.external_base_path
        }
