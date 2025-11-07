"""Manage user authentication."""

import logging
import os
import requests
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import UserMixin, login_required, login_user, logout_user
from ...eyrie import get_current_user_api, serve_shared_static, serve_blueprint_static

LOG = logging.getLogger(__name__)

# Blueprint definition matching Bonsai pattern
bp = Blueprint(
    "login",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/login",
)


class TokenObject:
    """Token object for authentication"""
    def __init__(self, token: str, type: str = "Bearer"):
        self.token = token
        self.type = type

    def dict(self):
        return {"token": self.token, "type": self.type}


class LoginUser(UserMixin):
    """Container for user data and perform login."""

    def __init__(self, user_data, token_data):
        """Create a new user object."""
        self.roles = []
        for key, value in user_data.items():
            setattr(self, key, value)
        # store token
        self.token = token_data

    def get_id(self):
        """Get user ID for Flask-Login"""
        return str(getattr(self, 'username', '')) or self.token.token

    @property
    def is_admin(self):
        """Check if the user is admin."""
        return getattr(self, 'role', '') == 'admin'


def get_backend_url():
    """Get the backend URL for API calls"""
    return os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')


def get_auth_token(username: str, password: str):
    """Authenticate with backend API and get token"""
    try:
        backend_url = get_backend_url()
        response = requests.post(
            f"{backend_url}/api/auth/login",
            json={'username': username, 'password': password},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'user': data.get('user', {}),
                'token': TokenObject(data.get('access_token', ''))
            }
        else:
            return None

    except requests.RequestException as e:
        LOG.error(f"Authentication failed: {str(e)}")
        return None


def unauthorized_handler():
    """Handle unauthorized access with proper URL generation"""
    # Always use Flask's url_for which respects APPLICATION_ROOT and base_path
    return redirect(url_for('login.login', next=request.url))


def load_user(user_id):
    """Load user from session data"""
    try:
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
            return user
    except Exception as e:
        LOG.error(f"User loader error: {e}")
    return None




@bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Logout user."""
    logout_user()
    session.pop("email", None)
    session.pop("fname", None)
    session.pop("lname", None)
    session.pop("locale", None)
    session.pop("username", None)
    session.pop("role", None)
    session.pop("backend_token", None)
    session.clear()  # Clear all session data
    return redirect(url_for("login.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login a user."""
    if "next" in request.args:
        session["next_url"] = request.args["next"]

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required", "error")
            return redirect(url_for("login.login"))

        try:
            auth_data = get_auth_token(username, password)

            if auth_data:
                user_data = auth_data['user']
                token_data = auth_data['token']

                # Create user object
                user = LoginUser(user_data, token_data)

                # Login user
                login_user(user)

                # Store additional session data
                session["email"] = user_data.get("email", "")
                session["username"] = user_data.get("username", "")
                session["role"] = user_data.get("role", "")
                session["backend_token"] = token_data.token

                LOG.info(f"User {username} logged in successfully")

                # Redirect to next URL or samples page
                next_url = session.pop("next_url", None)
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect(url_for('samples.samples_page'))

            else:
                flash("Invalid username or password", "error")
                return redirect(url_for("login.login"))

        except Exception as e:
            LOG.error(f"Login error: {str(e)}")
            flash("Login failed. Please try again.", "error")
            return redirect(url_for("login.login"))

    # GET request - show login page
    return render_template("login.html", title="Login")


# API Endpoints
@bp.route("/api/auth/current-user", methods=['GET'])
@login_required
def current_user_api():
    """Get current user info from Flask-Login session"""
    try:
        user_data = get_current_user_api()
        return jsonify(user_data)
    except ValueError as e:
        return jsonify({'error': 'Not authenticated'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Static file serving endpoints
@bp.route("/shared/static/<path:filename>", methods=['GET'])
def serve_shared_static_endpoint(filename):
    """Serve shared static assets"""
    return serve_shared_static(filename)


@bp.route("/blueprints/<blueprint>/<path:filename>", methods=['GET'])
def serve_blueprint_static_endpoint(blueprint, filename):
    """Serve blueprint-specific static assets"""
    return serve_blueprint_static(blueprint, filename)
