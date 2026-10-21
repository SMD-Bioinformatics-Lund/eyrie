/**
 * Shared JavaScript functions for Eyrie
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
};

// Make functions available globally for backward compatibility
window.showError = window.EyrieShared.showError;
window.showSuccess = window.EyrieShared.showSuccess;
window.formatDate = window.EyrieShared.formatDate;


// Row selection: the header checkbox selects or clears every row, and "Selected" counts follow the row checkboxes
document.addEventListener('change', function(event) {
    const target = event.target;
    const table = target.closest('table');
    if (!table) return;
    const rows = table.querySelectorAll('.row-select');
    if (target.classList.contains('select-all')) {
        rows.forEach(function(row) { row.checked = target.checked; });
    } else if (target.classList.contains('row-select')) {
        const checked = table.querySelectorAll('.row-select:checked').length;
        const header = table.querySelector('.select-all');
        if (header) {
            header.checked = checked > 0 && checked === rows.length;
            header.indeterminate = checked > 0 && checked < rows.length;
        }
    } else {
        return;
    }
    const count = table.querySelectorAll('.row-select:checked').length;
    document.querySelectorAll('[data-selected-count]').forEach(function(element) {
        element.textContent = count;
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.info-blob').forEach(function(element) {
        bootstrap.Tooltip.getOrCreateInstance(element, {animation: false});
    });
});
