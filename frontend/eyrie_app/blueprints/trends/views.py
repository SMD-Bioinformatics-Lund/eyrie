"""Views for trends analysis."""

from flask import Blueprint, render_template, request, jsonify
from ...auth import jwt_required
from ...eyrie import get_trends_data
from ...config import settings

trends_bp = Blueprint('trends', __name__,
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='')


@trends_bp.route('/trends')
@jwt_required
def index():
    """Display trends dashboard."""
    return render_template('trends.html', config=settings.trends_config)


# API Endpoints
@trends_bp.route("/api/trends/data", methods=['GET'])
@jwt_required
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
