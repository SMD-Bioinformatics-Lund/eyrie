from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from ...auth import jwt_required, admin_required, get_current_user, get_jwt_from_cookie
import requests
import os
from ...eyrie import get_admin_users, create_admin_user, update_admin_user, delete_admin_user

bp = Blueprint('admin', __name__, url_prefix='', template_folder='templates')

@bp.route("/admin")
@jwt_required
@admin_required
def dashboard():
    """Admin dashboard with user management"""
    return render_template('dashboard.html', current_user=get_current_user())

@bp.route("/admin/users")
@jwt_required
@admin_required
def users():
    """User management page"""
    try:
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = get_jwt_from_cookie()

        if not backend_token:
            flash('Backend authentication required.', 'error')
            return redirect(url_for('admin.dashboard'))

        response = requests.get(
            f"{backend_url}/api/admin/users",
            headers={'Authorization': f'Bearer {backend_token}'},
            timeout=10
        )

        if response.status_code == 200:
            users_data = response.json()
            return render_template('users.html', users=users_data, current_user=get_current_user())
        else:
            flash(f'Failed to load users: {response.status_code}', 'error')
            return render_template('users.html', users=[], current_user=get_current_user())

    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return render_template('users.html', users=[], current_user=get_current_user())

@bp.route("/admin/users/new", methods=['GET', 'POST'])
@jwt_required
@admin_required
def create_user():
    """Create new user"""
    if request.method == 'GET':
        return render_template('create_user.html', current_user=get_current_user())

    try:
        data = {
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'role': request.form.get('role', 'user')
        }

        if not all([data['username'], data['email'], data['password']]):
            flash('Please fill in all required fields.', 'error')
            return render_template('create_user.html', current_user=get_current_user(), form_data=data)

        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = get_jwt_from_cookie()

        if not backend_token:
            flash('Backend authentication required.', 'error')
            return redirect(url_for('admin.dashboard'))

        response = requests.post(
            f"{backend_url}/api/admin/users",
            headers={'Authorization': f'Bearer {backend_token}'},
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            flash(f'User {data["username"]} created successfully.', 'success')
            return redirect(url_for('admin.users'))
        else:
            result = response.json() if response.content else {}
            error_msg = result.get('error', f'Failed to create user (status: {response.status_code})')
            flash(error_msg, 'error')
            return render_template('create_user.html', current_user=get_current_user(), form_data=data)

    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
        return render_template('create_user.html', current_user=get_current_user(), form_data=request.form)

@bp.route("/admin/users/<user_id>/edit", methods=['GET', 'POST'])
@jwt_required
@admin_required
def edit_user(user_id):
    """Edit existing user"""
    try:
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = get_jwt_from_cookie()

        if not backend_token:
            flash('Backend authentication required.', 'error')
            return redirect(url_for('admin.dashboard'))

        if request.method == 'GET':
            response = requests.get(
                f"{backend_url}/api/admin/users",
                headers={'Authorization': f'Bearer {backend_token}'},
                timeout=10
            )

            if response.status_code == 200:
                users = response.json()
                user = next((u for u in users if u['_id'] == user_id), None)
                if user:
                    return render_template('edit_user.html', user=user, current_user=get_current_user())
                else:
                    flash('User not found.', 'error')
                    return redirect(url_for('admin.users'))
            else:
                flash('Failed to load user data.', 'error')
                return redirect(url_for('admin.users'))

        data = {
            'email': request.form.get('email'),
            'role': request.form.get('role'),
            'is_active': 'is_active' in request.form
        }

        password = request.form.get('password')
        if password:
            data['password'] = password

        response = requests.put(
            f"{backend_url}/api/admin/users/{user_id}",
            headers={'Authorization': f'Bearer {backend_token}'},
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        else:
            result = response.json() if response.content else {}
            error_msg = result.get('error', f'Failed to update user (status: {response.status_code})')
            flash(error_msg, 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))

    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('admin.users'))

@bp.route("/admin/users/<user_id>/delete", methods=['POST'])
@jwt_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    try:
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = get_jwt_from_cookie()

        if not backend_token:
            flash('Backend authentication required.', 'error')
            return redirect(url_for('admin.dashboard'))

        response = requests.delete(
            f"{backend_url}/api/admin/users/{user_id}",
            headers={'Authorization': f'Bearer {backend_token}'},
            timeout=10
        )

        if response.status_code == 200:
            flash('User deleted successfully.', 'success')
        else:
            result = response.json() if response.content else {}
            error_msg = result.get('error', f'Failed to delete user (status: {response.status_code})')
            flash(error_msg, 'error')

    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')

    return redirect(url_for('admin.users'))


@bp.route("/api/admin/users", methods=['GET'])
@jwt_required
@admin_required
def get_users_api():
    """Get admin users from backend API"""
    try:
        data = get_admin_users()
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/admin/users", methods=['POST'])
@jwt_required
@admin_required
def create_user_api():
    """Create admin user"""
    try:
        data = request.get_json()
        result = create_admin_user(data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/admin/users/<user_id>", methods=['PUT'])
@jwt_required
@admin_required
def update_user_api(user_id):
    """Update admin user"""
    try:
        data = request.get_json()
        result = update_admin_user(user_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/admin/users/<user_id>", methods=['DELETE'])
@jwt_required
@admin_required
def delete_user_api(user_id):
    """Delete admin user"""
    try:
        result = delete_admin_user(user_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
