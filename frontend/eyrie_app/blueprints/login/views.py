"""Manage user authentication."""

import logging
import os
import requests

from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from ...auth import jwt_required, get_current_user, set_jwt_cookie, clear_jwt_cookie
from ...eyrie import serve_shared_static, serve_blueprint_static

LOG = logging.getLogger(__name__)

bp = Blueprint(
    "login",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/login",
)


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
                'token': data.get('access_token', '')
            }
        else:
            return None

    except requests.RequestException as e:
        LOG.error(f"Authentication failed: {str(e)}")
        return None




@bp.route("/logout", methods=["GET", "POST"])
@jwt_required
def logout():
    """Logout user by clearing JWT cookie."""
    response = make_response(redirect(url_for("login.login")))
    clear_jwt_cookie(response)
    return response


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
                token = auth_data['token']

                LOG.info(f"User {username} logged in successfully")

                # Determine redirect URL
                next_url = session.pop("next_url", None)
                if next_url:
                    response = make_response(redirect(next_url))
                else:
                    response = make_response(redirect(url_for('samples.samples_page')))

                # Set JWT cookie
                set_jwt_cookie(response, token)

                return response

            else:
                flash("Invalid username or password", "error")
                return redirect(url_for("login.login"))

        except Exception as e:
            LOG.error(f"Login error: {str(e)}")
            flash("Login failed. Please try again.", "error")
            return redirect(url_for("login.login"))

    return render_template("login.html", title="Login")


@bp.route("/api/auth/current-user", methods=['GET'])
@jwt_required
def current_user_api():
    """Get current user info from JWT cookie"""
    try:
        user = get_current_user()
        if user:
            return jsonify({
                'username': user.username,
                'email': user.email,
                'role': user.role
            })
        return jsonify({'error': 'Not authenticated'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/shared/static/<path:filename>", methods=['GET'])
def serve_shared_static_endpoint(filename):
    """Serve shared static assets"""
    return serve_shared_static(filename)


@bp.route("/blueprints/<blueprint>/<path:filename>", methods=['GET'])
def serve_blueprint_static_endpoint(blueprint, filename):
    """Serve blueprint-specific static assets"""
    return serve_blueprint_static(blueprint, filename)
