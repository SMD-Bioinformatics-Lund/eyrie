from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.exceptions import HTTPException
from ...auth import jwt_required, admin_required, get_current_user, get_jwt_from_cookie
import requests
import os
from ...eyrie import get_admin_users, create_admin_user, update_admin_user, delete_admin_user

bp = Blueprint('admin', __name__, url_prefix='', template_folder='templates')

ROLES = ['user', 'uploader', 'admin']

@bp.route("/admin")
@jwt_required
@admin_required
def dashboard():
    return redirect(url_for('admin.users'))

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
            return render_template('users.html', users=[], current_user=get_current_user())

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

    except HTTPException:
        raise  # Let Flask handle HTTP errors (401, 403, etc.)
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
            return redirect(url_for('admin.users'))

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

    except HTTPException:
        raise  # Let Flask handle HTTP errors (401, 403, etc.)
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
            return redirect(url_for('admin.users'))

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

    except HTTPException:
        raise  # Let Flask handle HTTP errors (401, 403, etc.)
    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('admin.users'))

def selected_user_ids():
    """Selected users, leaving out the signed-in admin so they cannot lock themselves out."""
    current_user = get_current_user()
    own_id = current_user.user_id if current_user else None
    selected = request.form.getlist('user_ids')
    skipped_self = own_id in selected
    return [user_id for user_id in selected if user_id != own_id], skipped_self


def apply_to_selected_users(action, past_tense):
    user_ids, skipped_self = selected_user_ids()
    if not user_ids:
        flash('No other users selected.' if skipped_self else 'No users selected.', 'warning')
        return redirect(url_for('admin.users'))
    failed = 0
    for user_id in user_ids:
        try:
            action(user_id)
        except Exception:
            failed += 1
    done = len(user_ids) - failed
    flash(f"{past_tense} {done} user{'' if done == 1 else 's'}."
          + (' Your own account was skipped.' if skipped_self else '')
          + (f' {failed} failed.' if failed else ''), 'warning' if failed else 'success')
    return redirect(url_for('admin.users'))


@bp.route("/admin/users/update", methods=['POST'])
@jwt_required
@admin_required
def update_users():
    """Update the role and/or status of the selected users"""
    data = {}
    role = request.form.get('role')
    if role in ROLES:
        data['role'] = role
    status = request.form.get('status')
    if status in ('active', 'inactive'):
        data['is_active'] = status == 'active'
    if not data:
        flash('Nothing to update: choose a role or status.', 'warning')
        return redirect(url_for('admin.users'))
    return apply_to_selected_users(lambda user_id: update_admin_user(user_id, data), 'Updated')


@bp.route("/admin/users/activate", methods=['POST'])
@jwt_required
@admin_required
def activate_users():
    """Activate the selected users"""
    return apply_to_selected_users(lambda user_id: update_admin_user(user_id, {'is_active': True}), 'Activated')


@bp.route("/admin/users/deactivate", methods=['POST'])
@jwt_required
@admin_required
def deactivate_users():
    """Deactivate the selected users"""
    return apply_to_selected_users(lambda user_id: update_admin_user(user_id, {'is_active': False}), 'Deactivated')


@bp.route("/admin/users/delete", methods=['POST'])
@jwt_required
@admin_required
def delete_users():
    """Delete the selected users"""
    return apply_to_selected_users(delete_admin_user, 'Deleted')


SPIKE_SETTINGS_PATH = "/api/admin/settings/spike-species"


def spike_settings_request(method, path='', json=None):
    backend_url = os.getenv('INTERNAL_BACKEND_URL', 'http://eyrie-backend:5000')
    try:
        return requests.request(
            method,
            f"{backend_url}{SPIKE_SETTINGS_PATH}{path}",
            headers={'Authorization': f'Bearer {get_jwt_from_cookie()}'},
            json=json,
            timeout=10
        )
    except requests.RequestException:
        return None


def spike_settings_failed(response, action):
    if response is not None and response.status_code == 200:
        return False
    status = response.status_code if response is not None else 'no response'
    flash(f'Failed to {action} (status: {status})', 'error')
    return True


@bp.route("/admin/settings/spike-species")
@jwt_required
@admin_required
def spike_species():
    response = spike_settings_request('GET')
    settings = {'species': [], 'normaliser': None}
    if not spike_settings_failed(response, 'load spike species'):
        settings = response.json()
    return render_template('spike_species.html', settings=settings, current_user=get_current_user())


@bp.route("/admin/settings/spike-species/add", methods=['POST'])
@jwt_required
@admin_required
def add_spike_species():
    species = request.form.get('species', '').strip()
    if not species:
        flash('Enter a species name.', 'warning')
        return redirect(url_for('admin.spike_species'))
    response = spike_settings_request('POST', '/add', {'species': species})
    if not spike_settings_failed(response, f'add {species}'):
        if response.json().get('added'):
            flash(f'Added {species}.', 'success')
        else:
            flash(f'{species} is already a spike species.', 'warning')
    return redirect(url_for('admin.spike_species'))


@bp.route("/admin/settings/spike-species/remove", methods=['POST'])
@jwt_required
@admin_required
def remove_spike_species():
    species = request.form.getlist('species')
    if not species:
        flash('No species selected.', 'warning')
        return redirect(url_for('admin.spike_species'))
    response = spike_settings_request('POST', '/remove', {'species': species})
    if not spike_settings_failed(response, 'remove spike species'):
        flash(f"Removed {', '.join(species)}.", 'success')
    return redirect(url_for('admin.spike_species'))


def save_spike_normaliser(normaliser, message):
    response = spike_settings_request('PUT', '/normaliser', {'normaliser': normaliser})
    if not spike_settings_failed(response, 'update the normalising species'):
        flash(message, 'success')
    return redirect(url_for('admin.spike_species'))


@bp.route("/admin/settings/spike-species/normaliser", methods=['POST'])
@jwt_required
@admin_required
def set_spike_normaliser():
    species = request.form.getlist('species')
    if len(species) != 1:
        flash('Select exactly one species to use as the normaliser.', 'warning')
        return redirect(url_for('admin.spike_species'))
    return save_spike_normaliser(species[0], f'{species[0]} is now the normalising species.')


@bp.route("/admin/settings/spike-species/normaliser/clear", methods=['POST'])
@jwt_required
@admin_required
def clear_spike_normaliser():
    return save_spike_normaliser(None, 'Cleared the normalising species.')


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
