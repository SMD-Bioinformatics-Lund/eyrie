"""Views for trends analysis."""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from ...eyrie import get_trends_data, get_metadata_filters
from ...config import settings

trends_bp = Blueprint('trends', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='')


@trends_bp.route('/trends')
@login_required
def index():
    """Display trends dashboard with server-side populated data."""
    try:
        dynamic_filters = get_metadata_filters()

        return render_template('trends.html',
                             config=settings.trends_config,
                             dynamic_filters=dynamic_filters)

    except Exception as e:
        current_app.logger.warning(f"Failed to load metadata filters: {e}")
        empty_filters = {'tissues': [], 'extraction_kits': [], 'genera': []}
        return render_template('trends.html',
                             config=settings.trends_config,
                             dynamic_filters=empty_filters)


# API Endpoints
@trends_bp.route("/api/trends/data", methods=['GET'])
@login_required
def trends_data_api():
    """Get trends data from backend API"""
    try:
        query_params = request.args.to_dict()
        data = get_trends_data(query_params)
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
