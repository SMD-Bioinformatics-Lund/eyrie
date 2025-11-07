from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from ...eyrie import (
    get_sample_from_backend, update_sample_qc, update_sample_comment,
    update_sample_species_flags, serve_analysis_file
)

bp = Blueprint('sample', __name__, url_prefix='', template_folder='templates')

@bp.route("/sample/<sample_id>")
@login_required
def sample_overview(sample_id):
    try:
        # Get sample data for server-side rendering
        sample = get_sample_from_backend(sample_id)
        return render_template('sample_overview.html', sample_id=sample_id, sample=sample, current_user=current_user)
    except Exception as e:
        # If sample data can't be loaded, still render the template but with empty sample
        print(f"Error loading sample data for overview: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('sample_overview.html', sample_id=sample_id, sample=None, current_user=current_user)

@bp.route("/sample/<sample_id>/classification")
@login_required
def sample_classification(sample_id):
    try:
        # Get sample data for server-side rendering
        sample = get_sample_from_backend(sample_id)
        return render_template('sample_classification.html', sample_id=sample_id, sample=sample, current_user=current_user)
    except Exception as e:
        # If sample data can't be loaded, still render the template but with empty sample
        print(f"Error loading sample data for classification view: {e}")
        return render_template('sample_classification.html', sample_id=sample_id, sample=None, current_user=current_user)

@bp.route("/sample/<sample_id>/nanoplot")
@login_required
def sample_nanoplot(sample_id):
    try:
        # Get sample data for server-side rendering
        sample = get_sample_from_backend(sample_id)
        return render_template('sample_nanoplot.html', sample_id=sample_id, sample=sample, current_user=current_user)
    except Exception as e:
        # If sample data can't be loaded, still render the template but with empty sample
        print(f"Error loading sample data for nanoplot: {e}")
        return render_template('sample_nanoplot.html', sample_id=sample_id, sample=None, current_user=current_user)

# API Routes
@bp.route("/api/sample/<sample_id>")
@login_required
def get_sample_api(sample_id):
    """Get sample data from backend API"""
    try:
        data = get_sample_from_backend(sample_id)
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route("/api/sample/<sample_id>/qc", methods=['PUT'])
@login_required
def update_qc_api(sample_id):
    """Update sample QC status"""
    try:
        from flask import request
        data = request.get_json()
        result = update_sample_qc(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route("/api/sample/<sample_id>/comment", methods=['PUT'])
@login_required
def update_comment_api(sample_id):
    """Update sample comment"""
    try:
        from flask import request
        data = request.get_json()
        result = update_sample_comment(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route("/api/sample/<sample_id>/species-flags", methods=['PUT'])
@login_required
def update_species_flags_api(sample_id):
    """Update sample species flags"""
    try:
        from flask import request
        data = request.get_json()
        result = update_sample_species_flags(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Analysis file serving endpoint
@login_required
@bp.route("/analysis-files/<path:file_path>", methods=['GET'])
def serve_data_file_endpoint(file_path):
    """Serve analysis files from /app/analysis-files directory with authentication"""
    return serve_analysis_file(file_path)
