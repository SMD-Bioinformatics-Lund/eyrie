from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from datetime import datetime
import os
import json

from .config import settings
from .eyrie import test_backend_connectivity, health_check
from .__version__ import __version__
from .utils.template_filters import (
    format_number_filter, format_bases_filter, format_quality_filter,
    format_length_filter, qc_badge_class_filter, format_date_filter,
    shannon_diversity_filter, dominant_species_filter, library_concentration_class_filter
)
from .blueprints.login.views import unauthorized_handler, load_user, bp as login_bp
from .blueprints.sample.views import bp as sample_bp
from .blueprints.admin.views import bp as admin_bp
from .blueprints.samples.views import bp as samples_bp
from .blueprints.trends.views import trends_bp
from .blueprints.seqruns.views import bp as seqruns_bp


# Custom JSON encoder for datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def register_blueprints(app, base_path=None):
    """Register all Flask blueprints with optional base path"""
    # Register login blueprint
    app.register_blueprint(login_bp, url_prefix=base_path)

    # Register individual sample views blueprint
    app.register_blueprint(sample_bp, url_prefix=base_path)

    # Register admin blueprint
    app.register_blueprint(admin_bp, url_prefix=base_path)

    # Register samples blueprint
    app.register_blueprint(samples_bp, url_prefix=base_path)

    # Register trends blueprint
    app.register_blueprint(trends_bp, url_prefix=base_path)

    # Register sequencing runs blueprint
    app.register_blueprint(seqruns_bp, url_prefix=base_path)


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.secret_key = settings.secret_key

    # CORS configuration
    CORS(app, origins=settings.cors_origins, supports_credentials=True)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.unauthorized_handler(unauthorized_handler)
    login_manager.user_loader(load_user)

    # Configure Flask settings from config
    print(f"🔍 EXTERNAL_BASE_PATH: '{settings.external_base_path}'")
    print(f"🔍 base_path: '{settings.external_base_path}'")

    # Set APPLICATION_ROOT for proper URL generation with base path
    if settings.external_base_path:
        app.config['APPLICATION_ROOT'] = settings.external_base_path
        app.config['SESSION_COOKIE_PATH'] = settings.session_cookie_path
        print(f"✅ Set APPLICATION_ROOT to: '{settings.external_base_path}'")
        print(f"✅ Set SESSION_COOKIE_PATH to: '{settings.session_cookie_path}'")
    else:
        app.config['SESSION_COOKIE_PATH'] = '/'

    # Test backend connectivity on startup
    test_backend_connectivity()
    print("ℹ️  Frontend will handle sessions only, all data comes from backend API")

    # Register direct routes with base path
    base_path = settings.external_base_path or ''
    
    @app.route(f'{base_path}/api/test')
    def test_route():
        return "Test route works!"


    @app.route(f'{base_path}/health', methods=['GET'])
    def health_check_endpoint():
        """Health check endpoint with backend connectivity details"""
        try:
            health_data = health_check()
            if health_data['status'] == 'healthy':
                return jsonify(health_data)
            else:
                return jsonify(health_data), 500
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'container_name': os.getenv('HOSTNAME', 'unknown')
            }), 500


    # Register Jinja template filters
    app.jinja_env.filters['format_number'] = format_number_filter
    app.jinja_env.filters['format_bases'] = format_bases_filter
    app.jinja_env.filters['format_quality'] = format_quality_filter
    app.jinja_env.filters['format_length'] = format_length_filter
    app.jinja_env.filters['qc_badge_class'] = qc_badge_class_filter
    app.jinja_env.filters['format_date'] = format_date_filter
    app.jinja_env.filters['shannon_diversity'] = shannon_diversity_filter
    app.jinja_env.filters['dominant_species'] = dominant_species_filter
    app.jinja_env.filters['library_concentration_class'] = library_concentration_class_filter

    # Add template context processor for version information
    @app.context_processor
    def inject_version():
        return {
            'app_version': __version__,
            'app_name': 'Eyrie'
        }

    # Register all blueprints
    register_blueprints(app, settings.external_base_path)

    return app

if __name__ == "__main__":
    # For development only - use wsgi.py for production
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=settings.debug)
