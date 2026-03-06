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

from flask import jsonify, send_file, current_app, send_from_directory, request, abort

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


# JWT Cookie name (should match auth.py)
JWT_COOKIE_NAME = 'eyrie_jwt'


def api_authentication(func):
    """
    Decorator for API functions that adds authentication headers.
    Gets JWT token from cookie instead of session.
    Catches 401 errors from the backend and triggers Flask's 401 handler.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get backend token from JWT cookie
        backend_token = request.cookies.get(JWT_COOKIE_NAME)
        if not backend_token:
            abort(401)

        # Create headers dictionary
        headers = CaseInsensitiveDict()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        headers['Authorization'] = f'Bearer {backend_token}'

        # Add headers as first argument and catch 401 errors
        try:
            return func(headers, *args, **kwargs)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                abort(401)
            raise

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
def get_seqrun_from_backend(headers: CaseInsensitiveDict, seqrun_id: str) -> Optional[Dict[str, Any]]:
    """Get specific sequencing run from backend API"""
    try:
        url = f"{backend_url}/api/seqruns/{seqrun_id}"
        print(f"🌐 DEBUG: Making API call to: {url}")
        print(f"🔑 DEBUG: Using headers: {dict(headers)}")
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"📡 DEBUG: API response status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ DEBUG: API returned data with keys: {list(data.keys())}")
            return data
        elif resp.status_code == 404:
            print(f"❌ DEBUG: API returned 404 - seqrun not found")
            return None
        else:
            print(f"❌ DEBUG: API returned error status: {resp.status_code}")
            print(f"❌ DEBUG: API error response: {resp.text}")
            resp.raise_for_status()
    except Exception as e:
        print(f"❌ DEBUG: API call exception: {type(e).__name__}: {e}")
        return None


@api_authentication
def get_seqruns_from_backend(headers: CaseInsensitiveDict) -> List[Dict[str, Any]]:
    """Get all sequencing runs from backend API"""
    url = f"{backend_url}/api/seqruns"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_negative_controls_from_backend(headers: CaseInsensitiveDict, sample_id: str) -> List[Dict[str, Any]]:
    """Get negative control samples from the same sequencing run"""
    url = f"{backend_url}/api/sample/{sample_id}/negative-controls"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


@api_authentication
def get_contamination_analysis_from_backend(headers: CaseInsensitiveDict, seqrun_id: str) -> Dict[str, Any]:
    """Get contamination analysis for a specific sequencing run"""
    try:
        url = f"{backend_url}/api/seqruns/{seqrun_id}/contamination"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            return {'message': 'Unable to retrieve contamination analysis data', 'contaminating_species': []}
    except Exception as e:
        return {'message': f'Error analyzing contamination: {str(e)}', 'contaminating_species': []}


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


def get_analysis_path(data: Dict[str, Any]) -> str:
    """Get the correct analysis results path based on pipeline_software (works for both samples and seqruns)"""

    pipeline_software = data.get('pipeline_software', 'trana')
    analysis_path = settings.analysis_results_paths.get(pipeline_software,
                                                       settings.analysis_results_paths['trana'])

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


@api_authentication
def get_qc_overview_from_backend(headers: CaseInsensitiveDict, seqrun_id: str) -> Dict[str, Any]:
    """Get QC overview analysis for a specific sequencing run"""
    try:
        url = f"{backend_url}/api/seqruns/{seqrun_id}/qc/overview"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {'message': 'Unable to retrieve QC overview data'}
    except Exception as e:
        return {'message': 'Unable to retrieve QC overview data'}


@api_authentication  
def get_read_quality_from_backend(headers: CaseInsensitiveDict, seqrun_id: str) -> Dict[str, Any]:
    """Get read quality analysis for a specific sequencing run"""
    try:
        url = f"{backend_url}/api/seqruns/{seqrun_id}/qc/read-quality"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {'message': 'Unable to retrieve read quality data'}
    except Exception as e:
        return {'message': 'Unable to retrieve read quality data'}


@api_authentication
def get_taxonomic_diversity_from_backend(headers: CaseInsensitiveDict, seqrun_id: str) -> Dict[str, Any]:
    """Get taxonomic diversity analysis for a specific sequencing run"""
    try:
        url = f"{backend_url}/api/seqruns/{seqrun_id}/qc/taxonomic-diversity"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {'message': 'Unable to retrieve taxonomic diversity data'}
    except Exception as e:
        return {'message': 'Unable to retrieve taxonomic diversity data'}


@api_authentication
def get_positive_control_validation_from_backend(headers: CaseInsensitiveDict, seqrun_id: str) -> Dict[str, Any]:
    """Get positive control validation for a specific sequencing run"""
    try:
        url = f"{backend_url}/api/seqruns/{seqrun_id}/qc/positive-controls"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {'message': 'Unable to retrieve positive control validation data'}
    except Exception as e:
        return {'message': 'Unable to retrieve positive control validation data'}
