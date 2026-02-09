from flask import Blueprint, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
from ...auth import jwt_required
from ...eyrie import get_samples_from_backend, get_sample_from_backend, update_sample_qc, update_sample_comment, update_sample_species_flags, create_sample

bp = Blueprint('samples', __name__, url_prefix='', template_folder='templates')

@bp.route("/")
@jwt_required
def root():
    """Redirect to samples page"""
    try:
        samples = get_samples_from_backend()
        return render_template('samples.html', samples=samples)
    except HTTPException:
        raise  # Let Flask handle HTTP errors (401, 403, etc.)
    except Exception as e:
        # If backend is unavailable, show page with error message
        return render_template('samples.html', samples=[], error=str(e))

@bp.route("/samples")
@jwt_required
def samples_page():
    """Display samples page"""
    try:
        samples = get_samples_from_backend()
        return render_template('samples.html', samples=samples)
    except HTTPException:
        raise  # Let Flask handle HTTP errors (401, 403, etc.)
    except Exception as e:
        # If backend is unavailable, show page with error message
        return render_template('samples.html', samples=[], error=str(e))


# API Endpoints
@bp.route("/api/samples", methods=['GET'])
@jwt_required
def get_samples_api():
    """Get samples from backend API"""
    try:
        data = get_samples_from_backend()
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples", methods=['POST'])
@jwt_required
def create_sample_api():
    """Create a new sample"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        result = create_sample(data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>", methods=['GET'])
@jwt_required
def get_sample_api(sample_id):
    """Get specific sample from backend API"""
    try:
        data = get_sample_from_backend(sample_id)
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>/qc", methods=['PUT'])
@jwt_required
def update_qc_api(sample_id):
    """Update sample QC status"""
    try:
        data = request.get_json()
        result = update_sample_qc(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>/comment", methods=['PUT'])
@jwt_required
def update_comment_api(sample_id):
    """Update sample comment"""
    try:
        data = request.get_json()
        result = update_sample_comment(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>/species-flags", methods=['PUT'])
@jwt_required
def update_species_flags_api(sample_id):
    """Update sample species flags"""
    try:
        data = request.get_json()
        result = update_sample_species_flags(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
