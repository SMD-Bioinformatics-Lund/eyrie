document.addEventListener('DOMContentLoaded', function() {
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
                <a href="${getSampleUrl(sample.sample_id)}" class="btn btn-primary btn-sm">
                    <i class="bi bi-eye"></i>
                </a>
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


function getSampleUrl(sampleId) {
    // Use Flask URL template provided by the template
    if (window.SAMPLE_URL_TEMPLATE) {
        return window.SAMPLE_URL_TEMPLATE.replace('__SAMPLE_ID__', sampleId);
    }
    // Fallback to manual construction if template not available
    const basePath = window.API_BASE.replace('/api', '');
    return `${basePath}/sample/${sampleId}`;
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


function showError(message) {
    const tbody = document.getElementById('samplesTableBody');
    tbody.innerHTML = `<tr><td colspan="12" class="text-center py-4 text-danger">${message}</td></tr>`;
}
