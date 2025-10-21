/**
 * Shared JavaScript functions for Eyrie Sample Manager
 * These functions are used across multiple pages/blueprints
 */

/**
 * Common API and utility functions
 */
window.EyrieShared = {
    /**
     * Show error notification
     */
    showError: function(message) {
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
    },

    /**
     * Show success notification
     */
    showSuccess: function(message) {
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
    },

    /**
     * Format date for display
     */
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    },

    /**
     * Logout user - centralized logout function
     */
    logout: async function() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/login';
        }
    },

    /**
     * Load current user - centralized authentication function
     */
    loadCurrentUser: async function() {
        try {
            const response = await fetch('/api/auth/current-user', {
                credentials: 'include'
            });
            if (response.ok) {
                const user = await response.json();
                document.getElementById('currentUsername').textContent = user.username;
                return user;
            } else {
                document.getElementById('currentUsername').textContent = 'Unknown';
                return null;
            }
        } catch (error) {
            console.error('Failed to load user:', error);
            document.getElementById('currentUsername').textContent = 'Unknown';
            return null;
        }
    },

};

// Make functions available globally for backward compatibility
window.showError = window.EyrieShared.showError;
window.showSuccess = window.EyrieShared.showSuccess;
window.formatDate = window.EyrieShared.formatDate;
window.logout = window.EyrieShared.logout;
window.loadCurrentUser = window.EyrieShared.loadCurrentUser;
