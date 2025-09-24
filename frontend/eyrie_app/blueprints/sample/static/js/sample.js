let currentSample = null;
let qcFailModal = null;

document.addEventListener('DOMContentLoaded', function() {
    qcFailModal = new bootstrap.Modal(document.getElementById('qcFailModal'));
    
    loadCurrentUser();
    
    // Extract sample ID from URL path: /sample/S001
    const pathParts = window.location.pathname.split('/');
    const sampleId = pathParts[pathParts.length - 1]; // Get last part
    
    console.log('URL path:', window.location.pathname);
    console.log('Path parts:', pathParts);
    console.log('Sample ID:', sampleId);
    
    if (sampleId) {
        loadSample(sampleId);
    } else {
        showError('No sample ID provided');
    }
});

async function loadSample(sampleId) {
    try {
        console.log('Loading sample:', sampleId);
        console.log('API_BASE:', window.API_BASE);
        const apiUrl = `${window.API_BASE}/samples/${sampleId}`;
        console.log('Full API URL:', apiUrl);
        const response = await fetch(apiUrl);
        console.log('Response status:', response.status);
        const sample = await response.json();
        console.log('Sample data:', sample);
        
        if (response.ok) {
            currentSample = sample;
            renderSampleDetail(sample);
        } else {
            showError('Failed to load sample: ' + sample.error);
        }
    } catch (error) {
        console.error('Error loading sample:', error);
        showError('Network error: ' + error.message);
    }
}

function renderSampleDetail(sample) {
    document.getElementById('sampleTitle').textContent = `${sample.sample_name} (${sample.sample_id})`;
    
    // Update general information
    document.getElementById('infoSampleName').textContent = sample.sample_name || '--';
    document.getElementById('infoSampleId').textContent = sample.sample_id || '--';
    document.getElementById('infoSequencingRun').textContent = sample.sequencing_run_id || '--';
    document.getElementById('infoLimsId').textContent = sample.lims_id || '--';
    
    const classificationElement = document.getElementById('infoClassification');
    if (sample.classification) {
        classificationElement.innerHTML = `<span class="badge ${sample.classification === '16S' ? 'bg-primary' : 'bg-info'}">${sample.classification}</span>`;
    } else {
        classificationElement.textContent = '--';
    }
    
    document.getElementById('infoCreatedDate').textContent = formatDate(sample.created_date);
    document.getElementById('infoUpdatedDate').textContent = formatDate(sample.updated_date);
    
    const qcStatus = document.getElementById('currentQCStatus');
    qcStatus.innerHTML = `<span class="badge ${getQCBadgeClass(sample.qc)}">${sample.qc.toUpperCase()}</span>`;
    
    document.getElementById('generalComments').value = sample.comments || '';
    
    if (sample.krona_file) {
        document.getElementById('kronaFrame').src = `/data/krona/${sample.krona_file}`;
    } else {
        document.getElementById('kronaFrame').srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No Krona plot available</i></div>';
    }
    
    if (sample.quality_plot) {
        document.getElementById('qualityFrame').src = `/data/quality/${sample.quality_plot}`;
    } else {
        document.getElementById('qualityFrame').srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No quality plot available</i></div>';
    }
    
    renderPipelineFiles(sample.pipeline_files || []);
    renderStatistics(sample.statistics || {});
}

function renderStatistics(stats) {
    // Update statistics display
    const statsElements = {
        total_reads: document.querySelector('.stats-card .row .col-6:nth-child(1) .h4'),
        quality_passed: document.querySelector('.stats-card .row .col-6:nth-child(2) .h4'),
        avg_length: document.querySelector('.stats-card .row .col-6:nth-child(3) .h4'),
        avg_quality: document.querySelector('.stats-card .row .col-6:nth-child(4) .h4')
    };
    
    if (statsElements.total_reads) {
        statsElements.total_reads.textContent = stats.total_reads ? stats.total_reads.toLocaleString() : '--';
    }
    if (statsElements.quality_passed) {
        const passed = stats.quality_passed || 0;
        const total = stats.total_reads || 0;
        const percentage = total > 0 ? Math.round((passed / total) * 100) : 0;
        statsElements.quality_passed.textContent = passed ? `${passed.toLocaleString()} (${percentage}%)` : '--';
    }
    if (statsElements.avg_length) {
        statsElements.avg_length.textContent = stats.avg_length ? `${stats.avg_length} bp` : '--';
    }
    if (statsElements.avg_quality) {
        statsElements.avg_quality.textContent = stats.avg_quality ? stats.avg_quality.toFixed(1) : '--';
    }
}

function renderPipelineFiles(files) {
    const container = document.getElementById('pipelineFilesList');
    
    if (files.length === 0) {
        container.innerHTML = '<div class="list-group-item text-center py-3 text-muted">No pipeline files available</div>';
        return;
    }
    
    container.innerHTML = files.map(file => `
        <a href="/data/pipeline/${file}" 
           target="_blank" 
           class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
            <span>
                <i class="bi bi-file-earmark-text me-2"></i>${file}
            </span>
            <i class="bi bi-box-arrow-up-right"></i>
        </a>
    `).join('');
}

function getQCBadgeClass(qc) {
    switch (qc) {
        case 'passed': return 'bg-success';
        case 'failed': return 'bg-danger';
        case 'unprocessed': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

async function updateQC(status, comments = '') {
    if (!currentSample) return;
    
    try {
        const response = await fetch(`${window.API_BASE}/samples/${currentSample.sample_id}/qc`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                qc: status,
                comments: comments
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentSample.qc = status;
            if (comments) {
                currentSample.comments = comments;
                document.getElementById('generalComments').value = comments;
            }
            
            const qcStatus = document.getElementById('currentQCStatus');
            qcStatus.innerHTML = `<span class="badge ${getQCBadgeClass(status)}">${status.toUpperCase()}</span>`;
            
            showSuccess(`QC status updated to ${status.toUpperCase()}`);
        } else {
            showError('Failed to update QC: ' + result.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function showFailModal() {
    document.getElementById('failureComments').value = '';
    qcFailModal.show();
}

function confirmFailQC() {
    const comments = document.getElementById('failureComments').value.trim();
    
    if (!comments) {
        alert('Please provide a reason for the QC failure.');
        return;
    }
    
    qcFailModal.hide();
    updateQC('failed', comments);
}

async function saveComments() {
    if (!currentSample) return;
    
    const comments = document.getElementById('generalComments').value;
    
    try {
        const response = await fetch(`${window.API_BASE}/samples/${currentSample.sample_id}/comment`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                comments: comments
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentSample.comments = comments;
            showSuccess('Comments saved successfully');
        } else {
            showError('Failed to save comments: ' + result.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
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
            if (user.role !== 'admin') {
                adminButton.style.display = 'none';
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

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
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
