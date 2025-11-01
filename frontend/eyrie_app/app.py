from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from datetime import datetime
import os
import json

from .config import settings
from .eyrie import test_backend_connectivity, health_check, health_check_base_path
from .blueprints.login.views import unauthorized_handler, load_user, bp as login_bp
from .blueprints.sample.views import bp as sample_bp
from .blueprints.admin.views import bp as admin_bp
from .blueprints.samples.views import bp as samples_bp
from .blueprints.trends.views import trends_bp


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

    # Register direct routes before blueprints
    @app.route('/api/test')
    def test_route():
        return "Test route works!"

    @app.route('/api/files/data/<path:file_path>')
    def api_files_data(file_path):
        """Proxy data file requests to backend API"""
        from .eyrie import serve_data_file_from_backend
        from flask_login import current_user

        # Check if user is authenticated
        if not current_user.is_authenticated:
            return "Authentication required", 401

        try:
            return serve_data_file_from_backend(file_path)
        except ValueError as e:
            return "Authentication required", 401
        except Exception as e:
            return f"Error serving file: {str(e)}", 500

    @app.route("/health", methods=['GET'])
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
    @app.template_filter('format_number')
    def format_number_filter(num):
        """Format number with locale formatting"""
        if not num:
            return '--'
        return f"{num:,}"
    
    @app.template_filter('format_bases') 
    def format_bases_filter(bases):
        """Format bases with appropriate unit"""
        if not bases:
            return '--'
        if bases >= 1e9:
            return f"{bases / 1e9:.1f} Gb"
        elif bases >= 1e6:
            return f"{bases / 1e6:.1f} Mb"
        elif bases >= 1e3:
            return f"{bases / 1e3:.1f} Kb"
        return f"{bases} bp"
    
    @app.template_filter('format_quality')
    def format_quality_filter(quality):
        """Format quality score"""
        if not quality:
            return '--'
        return f"Q{quality:.1f}"
    
    @app.template_filter('format_length')
    def format_length_filter(length):
        """Format length in bp"""
        if not length:
            return '--'
        return f"{round(length):,} bp"
    
    @app.template_filter('qc_badge_class')
    def qc_badge_class_filter(qc):
        """Get CSS class for QC badge"""
        qc_classes = {
            'passed': 'bg-success',
            'failed': 'bg-danger', 
            'unprocessed': 'bg-secondary'
        }
        return qc_classes.get(qc, 'bg-secondary')

    # Register all blueprints
    register_blueprints(app, settings.external_base_path)

    return app

if __name__ == "__main__":
    # For development only - use wsgi.py for production
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=settings.debug)
