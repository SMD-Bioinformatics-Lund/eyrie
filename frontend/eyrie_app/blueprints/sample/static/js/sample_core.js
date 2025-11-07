/**
 * Core utilities shared across sample views
 */

// Global variables
let currentSample = null;

// Simple client-side formatting functions (to be replaced by server-side pre-formatted data)
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function formatNumber(num) {
    if (!num) return '--';
    return new Intl.NumberFormat().format(num);
}

function formatLength(length) {
    if (!length) return '--';
    return `${Math.round(length).toLocaleString()} bp`;
}

function formatQuality(quality) {
    if (!quality) return '--';
    return `Q${quality.toFixed(1)}`;
}

function formatBases(bases) {
    if (!bases) return '--';
    if (bases >= 1e9) {
        return `${(bases / 1e9).toFixed(1)} Gb`;
    } else if (bases >= 1e6) {
        return `${(bases / 1e6).toFixed(1)} Mb`;
    } else if (bases >= 1e3) {
        return `${(bases / 1e3).toFixed(1)} Kb`;
    }
    return `${bases} bp`;
}

/**
 * Show error message
 */
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

/**
 * Show success message
 */
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

/**
 * Get QC badge class for styling
 */
function getQCBadgeClass(qc) {
    switch (qc) {
        case 'passed': return 'bg-success';
        case 'failed': return 'bg-danger';
        case 'unprocessed': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}


/**
 * Update DOM element with value
 */
function updateElement(elementId, value, property = 'textContent') {
    const element = document.getElementById(elementId);
    if (element) {
        if (property === 'value') {
            element.value = value;
        } else if (property === 'innerHTML') {
            element.innerHTML = value;
        } else {
            element.textContent = value;
        }
    }
}
