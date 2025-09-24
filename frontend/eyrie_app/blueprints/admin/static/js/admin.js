let createUserModal = null;
let editUserModal = null;

document.addEventListener('DOMContentLoaded', function() {
    createUserModal = new bootstrap.Modal(document.getElementById('createUserModal'));
    editUserModal = new bootstrap.Modal(document.getElementById('editUserModal'));
    
    // Load current user info
    loadCurrentUser();
    
    // Load users
    loadUsers();
});

async function loadCurrentUser() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/current-user`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('currentUsername').textContent = user.username;
            
            // Check if user is admin, if not redirect
            if (user.role !== 'admin') {
                window.location.href = '/samples';
            }
        } else {
            // User not authenticated, redirect to login
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading current user:', error);
        window.location.href = '/login';
    }
}

async function loadUsers() {
    try {
        const response = await fetch(`${window.API_BASE}/admin/users`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const users = await response.json();
            renderUsersTable(users);
        } else {
            const error = await response.json();
            showError('Failed to load users: ' + error.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>
                <span class="badge ${getRoleBadgeClass(user.role)}">${user.role.toUpperCase()}</span>
            </td>
            <td>
                <span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">${user.is_active ? 'Active' : 'Inactive'}</span>
            </td>
            <td>${formatDate(user.created_date)}</td>
            <td>
                <button class="btn btn-outline-primary btn-sm me-2" onclick="editUser('${user._id}')">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteUser('${user._id}', '${user.username}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getRoleBadgeClass(role) {
    switch (role) {
        case 'admin': return 'bg-danger';
        case 'uploader': return 'bg-warning';
        case 'user': return 'bg-info';
        default: return 'bg-secondary';
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function showCreateUserModal() {
    document.getElementById('createUserForm').reset();
    document.getElementById('createUserMessage').innerHTML = '';
    createUserModal.show();
}

async function createUser() {
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;
    
    if (!username || !email || !password) {
        showMessage('createUserMessage', 'Please fill in all required fields.', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${window.API_BASE}/admin/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password,
                role: role
            }),
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            createUserModal.hide();
            showSuccess('User created successfully');
            loadUsers(); // Reload the users table
        } else {
            showMessage('createUserMessage', result.error, 'danger');
        }
    } catch (error) {
        showMessage('createUserMessage', 'Network error: ' + error.message, 'danger');
    }
}

async function editUser(userId) {
    try {
        // Get current users to find the one to edit
        const response = await fetch(`${window.API_BASE}/admin/users`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const users = await response.json();
            const user = users.find(u => u._id === userId);
            
            if (user) {
                document.getElementById('editUserId').value = user._id;
                document.getElementById('editUsername').value = user.username;
                document.getElementById('editEmail').value = user.email;
                document.getElementById('editPassword').value = '';
                document.getElementById('editRole').value = user.role;
                document.getElementById('editIsActive').checked = user.is_active;
                document.getElementById('editUserMessage').innerHTML = '';
                
                editUserModal.show();
            }
        }
    } catch (error) {
        showError('Error loading user details: ' + error.message);
    }
}

async function updateUser() {
    const userId = document.getElementById('editUserId').value;
    const email = document.getElementById('editEmail').value;
    const password = document.getElementById('editPassword').value;
    const role = document.getElementById('editRole').value;
    const isActive = document.getElementById('editIsActive').checked;
    
    const updateData = {
        email: email,
        role: role,
        is_active: isActive
    };
    
    if (password) {
        updateData.password = password;
    }
    
    try {
        const response = await fetch(`${window.API_BASE}/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData),
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            editUserModal.hide();
            showSuccess('User updated successfully');
            loadUsers(); // Reload the users table
        } else {
            showMessage('editUserMessage', result.error, 'danger');
        }
    } catch (error) {
        showMessage('editUserMessage', 'Network error: ' + error.message, 'danger');
    }
}

async function deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.API_BASE}/admin/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess('User deleted successfully');
            loadUsers(); // Reload the users table
        } else {
            showError('Failed to delete user: ' + result.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

async function logout() {
    try {
        await fetch(`${window.API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/login';
    }
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-${type} mt-3">${message}</div>`;
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}
