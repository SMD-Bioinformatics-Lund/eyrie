/**
 * Core utilities shared across sample views
 */

// Constants
window.API_BASE = window.API_BASE || '/api';

// Global variables
let currentSample = null;

/**
 * Load sample data from API
 */
async function loadSample(sampleId) {
    try {
        const apiUrl = `${window.API_BASE}/samples/${sampleId}`;
        const response = await fetch(apiUrl);
        const sample = await response.json();
        
        if (response.ok) {
            currentSample = sample;
            return sample;
        } else {
            showError('Failed to load sample: ' + sample.error);
            return null;
        }
    } catch (error) {
        showError('Network error: ' + error.message);
        return null;
    }
}

/**
 * Load current user information
 */
async function loadCurrentUser() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/current-user`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('currentUsername').textContent = user.username;
            
            // Show/hide admin button based on role
            const adminButton = document.querySelector('a[href="/admin"]');
            if (adminButton && user.role !== 'admin') {
                adminButton.style.display = 'none';
            }
            return user;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        window.location.href = '/login';
    }
}

/**
 * Logout user
 */
async function logout() {
    try {
        await fetch(`${window.API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/login';
    } catch (error) {
        window.location.href = '/login';
    }
}

/**
 * Update sample title in navbar
 */
function updateSampleTitle(sample) {
    const titleElement = document.getElementById('sampleTitle');
    if (titleElement) {
        titleElement.textContent = `${sample.sample_name} (${sample.sample_id})`;
    }
}

/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

/**
 * Format number with locale formatting
 */
function formatNumber(num) {
    if (!num) return null;
    return new Intl.NumberFormat().format(num);
}

/**
 * Format length in bp
 */
function formatLength(length) {
    if (!length) return null;
    return `${Math.round(length)} bp`;
}

/**
 * Format quality score
 */
function formatQuality(quality) {
    if (!quality) return null;
    return `${quality.toFixed(1)}`;
}

/**
 * Format bases with appropriate unit
 */
function formatBases(bases) {
    if (!bases) return null;
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
