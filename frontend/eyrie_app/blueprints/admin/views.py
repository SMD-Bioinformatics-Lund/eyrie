from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_required, current_user
import requests
import os

bp = Blueprint('admin', __name__, url_prefix='', template_folder='templates')

def admin_required(func):
    """Decorator to require admin privileges"""
    from functools import wraps
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required.', 'error')
            return redirect(url_for('samples.samples_page'))
        return func(*args, **kwargs)
    return decorated_function

@bp.route("/admin")
@login_required
@admin_required
def dashboard():
    """Admin dashboard with user management"""
    return render_template('dashboard.html', current_user=current_user)

@bp.route("/admin/users")
@login_required
@admin_required
def users():
    """User management page"""
    try:
        # Get users from backend API
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = session.get('backend_token')
        
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
            return render_template('users.html', users=users_data, current_user=current_user)
        else:
            flash(f'Failed to load users: {response.status_code}', 'error')
            return render_template('users.html', users=[], current_user=current_user)
            
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return render_template('users.html', users=[], current_user=current_user)

@bp.route("/admin/users/new", methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    if request.method == 'GET':
        return render_template('create_user.html', current_user=current_user)
    
    # Handle POST request
    try:
        data = {
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'role': request.form.get('role', 'user')
        }
        
        # Validate required fields
        if not all([data['username'], data['email'], data['password']]):
            flash('Please fill in all required fields.', 'error')
            return render_template('create_user.html', current_user=current_user, form_data=data)
        
        # Create user via backend API
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = session.get('backend_token')
        
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
            return render_template('create_user.html', current_user=current_user, form_data=data)
            
    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
        return render_template('create_user.html', current_user=current_user, form_data=request.form)

@bp.route("/admin/users/<user_id>/edit", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit existing user"""
    try:
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = session.get('backend_token')
        
        if not backend_token:
            flash('Backend authentication required.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        if request.method == 'GET':
            # Get current user data
            response = requests.get(
                f"{backend_url}/api/admin/users",
                headers={'Authorization': f'Bearer {backend_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                users = response.json()
                user = next((u for u in users if u['_id'] == user_id), None)
                if user:
                    return render_template('edit_user.html', user=user, current_user=current_user)
                else:
                    flash('User not found.', 'error')
                    return redirect(url_for('admin.users'))
            else:
                flash('Failed to load user data.', 'error')
                return redirect(url_for('admin.users'))
        
        # Handle POST request
        data = {
            'email': request.form.get('email'),
            'role': request.form.get('role'),
            'is_active': 'is_active' in request.form
        }
        
        # Include password if provided
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
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    try:
        backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
        backend_token = session.get('backend_token')
        
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
