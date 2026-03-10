/**
 * QC Analysis JavaScript
 * Handles QC analysis navigation and content loading for sequencing runs
 */

function loadQCAnalysis(analysisType) {
    // Update the title using server-side provided mappings
    const titleElement = document.getElementById('qc-analysis-title');
    const titleMeta = document.querySelector(`meta[name="qc-title-${analysisType}"]`);
    const iconMeta = document.querySelector(`meta[name="qc-icon-${analysisType}"]`);

    if (titleMeta && iconMeta) {
        const title = titleMeta.getAttribute('content');
        const icon = iconMeta.getAttribute('content');
        titleElement.innerHTML = `<i class="${icon} me-2"></i>${title}`;
    }

    // Clear active state from all buttons
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });

    // Set active state on clicked button
    const buttonId = `btn-${analysisType === 'positive-controls' ? 'positive-controls' : analysisType.replace('_', '-')}`;
    const activeBtn = document.getElementById(buttonId);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Load pre-rendered content from hidden server-side elements
    const container = document.getElementById('qcAnalysisContainer');
    const dataElement = document.getElementById(`qc-data-${analysisType}`);
    if (dataElement) {
        container.innerHTML = dataElement.innerHTML;

        // Initialize plots after they become visible
        setTimeout(() => {
            if (analysisType === 'read-quality' && window.initReadQualityPlot) {
                window.initReadQualityPlot();
            }
            if (analysisType === 'contamination' && window.initContaminationPlot) {
                window.initContaminationPlot();
            }
        }, 100); // Small delay to ensure DOM updates complete
    } else {
        container.innerHTML = displayError(`No ${analysisType.replace('-', ' ')} data available`);
    }
}

// Helper function for displaying errors
function displayError(message) {
    return `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center">
                <i class="bi bi-exclamation-circle text-warning" style="font-size: 4rem;"></i>
                <p class="text-muted mt-3">${escapeHtml(message)}</p>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-load the first available QC analysis on page load
document.addEventListener('DOMContentLoaded', function() {
    // Try to load QC analyses in priority order
    const autoLoadOrder = [
        'overview',
        'contamination',
        'read-quality',
        'taxonomic-diversity',
        'positive-controls'
    ];

    for (const analysisType of autoLoadOrder) {
        const dataElement = document.getElementById(`qc-data-${analysisType}`);
        if (dataElement) {
            loadQCAnalysis(analysisType);
            break;
        }
    }
});
