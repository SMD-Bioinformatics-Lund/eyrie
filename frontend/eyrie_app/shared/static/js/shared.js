/**
 * Shared JavaScript functions for Eyrie Sample Manager
 * These functions are used across multiple pages/blueprints
 */

/**
 * Get base path from API_BASE
 * Removes the '/api' suffix to get the application base path
 */
window.getBasePath = function() {
    if (!window.API_BASE) {
        console.warn('API_BASE not available');
        return '';
    }
    // Remove '/api' suffix if present, otherwise return as-is
    return window.API_BASE.replace(/\/api$/, '');
};

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
     * Note: This is overridden by template-generated logout functions that use proper Flask URLs
     */
    logout: async function() {
        try {
            // Use base path aware URL construction
            const basePath = window.getBasePath();
            await fetch(`${basePath}/login/logout`, { method: 'POST' });
            window.location.href = `${basePath}/login`;
        } catch (error) {
            console.error('Logout error:', error);
            const basePath = window.getBasePath();
            window.location.href = `${basePath}/login`;
        }
    },

    /**
     * Load current user - centralized authentication function
     */
    loadCurrentUser: async function() {
        try {
            // Use the same endpoint as templates - this ensures proper base path handling
            const currentUserUrl = window.CURRENT_USER_URL || `${window.API_BASE}/auth/current-user`;
            const response = await fetch(currentUserUrl, {
                credentials: 'include'
            });
            if (response.ok) {
                const user = await response.json();
                document.getElementById('currentUsername').textContent = user.username;

                // Show admin menu if user is admin
                if (user.role === 'admin') {
                    const adminNav = document.getElementById('navAdmin');
                    if (adminNav) {
                        adminNav.style.display = 'inline-block';
                    }
                }

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
// Only set logout if not already defined by template (templates have proper Flask URLs)
if (typeof window.logout === 'undefined') {
    window.logout = window.EyrieShared.logout;
}
window.loadCurrentUser = window.EyrieShared.loadCurrentUser;
