document.addEventListener('DOMContentLoaded', function() {
    loadCurrentUser();
    loadSamples();

    // Setup search functionality
    const searchInput = document.getElementById('tableSearch');
    searchInput.addEventListener('input', filterTable);
});

async function loadSamples() {
    try {
        const response = await fetch(`${window.API_BASE}/samples`);
        const samples = await response.json();

        if (response.ok) {
            renderSamplesTable(samples);
        } else {
            showError('Failed to load samples: ' + samples.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function renderSamplesTable(samples) {
    const tbody = document.getElementById('samplesTableBody');

    if (samples.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center py-4">No samples found</td></tr>';
        return;
    }

    tbody.innerHTML = samples.map(sample => `
        <tr>
            <td>
                <button class="btn btn-primary btn-sm" onclick="openSample('${sample.sample_id}')">
                    <i class="bi bi-eye"></i>
                </button>
            </td>
            <td>${sample.sample_name}</td>
            <td>${sample.sample_id}</td>
            <td>${sample.sequencing_run_id}</td>
            <td>${sample.lims_id}</td>
            <td>
                <span class="badge ${sample.classification === '16S' ? 'bg-primary' : 'bg-info'}">${sample.classification}</span>
            </td>
            <td>${renderFlaggedSpecies(sample.flagged_top_hits, 'success')}</td>
            <td>${renderFlaggedSpecies(sample.flagged_contaminants, 'warning')}</td>
            <td>
                <span class="badge ${getQCBadgeClass(sample.qc)}">${sample.qc.toUpperCase()}</span>
            </td>
            <td>${sample.comments || '-'}</td>
            <td>${formatDate(sample.created_date)}</td>
            <td>${formatDate(sample.updated_date)}</td>
        </tr>
    `).join('');
}

function renderFlaggedSpecies(flaggedSpecies, badgeType) {
    if (!flaggedSpecies || flaggedSpecies.length === 0) {
        return '<span class="text-muted">None</span>';
    }

    const count = flaggedSpecies.length;
    const badgeClass = `bg-${badgeType}`;
    const textClass = badgeType === 'warning' ? 'text-dark' : '';

    if (count <= 2) {
        return `
            <div>
                <span class="badge ${badgeClass} ${textClass} mb-1">${count}</span><br>
                <small class="text-muted">${flaggedSpecies.join(', ')}</small>
            </div>
        `;
    } else {
        return `
            <div>
                <span class="badge ${badgeClass} ${textClass} mb-1">${count}</span><br>
                <small class="text-muted" title="${flaggedSpecies.join(', ')}">
                    ${flaggedSpecies.slice(0, 2).join(', ')}...
                </small>
            </div>
        `;
    }
}


function getQCBadgeClass(qc) {
    switch (qc) {
        case 'passed': return 'bg-success';
        case 'failed': return 'bg-danger';
        case 'unprocessed': return 'bg-secondary';
        default: return 'bg-secondary';
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function openSample(sampleId) {
    window.location.href = `/sample/${sampleId}`;
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

function filterTable() {
    const searchTerm = document.getElementById('tableSearch').value.toLowerCase();
    const tbody = document.getElementById('samplesTableBody');
    const rows = tbody.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let shouldShow = false;

        // Skip the loading/error rows
        if (cells.length === 1) continue;

        // Search through all text content in the row
        for (let j = 0; j < cells.length; j++) {
            const cellText = cells[j].textContent.toLowerCase();
            if (cellText.includes(searchTerm)) {
                shouldShow = true;
                break;
            }
        }

        row.style.display = shouldShow ? '' : 'none';
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

function showError(message) {
    const tbody = document.getElementById('samplesTableBody');
    tbody.innerHTML = `<tr><td colspan="12" class="text-center py-4 text-danger">${message}</td></tr>`;
}
