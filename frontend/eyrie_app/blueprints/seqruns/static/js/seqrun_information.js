/**
 * Seqrun information page JavaScript
 * Pipeline file loading and structured data display
 */

let currentPipelineFileUrl = null;
let currentNewTabUrl = null;

// Make seqrun data available to JavaScript (will be set by template)
let currentSeqrun = null;

function initSeqrunInformation(seqrunData) {
    currentSeqrun = seqrunData;
}

function loadPipelineFile(fileType, fileUrl) {
    // Update the title
    const titleMap = {
        'execution_report': 'Execution Report',
        'execution_timeline': 'Execution Timeline', 
        'pipeline_dag': 'Pipeline DAG',
        'params': 'Parameters JSON',
        'execution_trace': 'Execution Trace',
        'software_versions': 'Software Versions'
    };

    const title = titleMap[fileType] || 'Pipeline File';
    document.getElementById('pipeline-file-title').innerHTML = `<i class="bi bi-file-earmark me-2"></i>${title}`;

    // Store current URLs for "Open in New Tab" button  
    currentPipelineFileUrl = fileUrl;

    // Get the new tab URL from the button's data attribute
    const activeBtn = document.getElementById(`btn-${fileType.replace('_', '-')}`);
    if (activeBtn) {
        currentNewTabUrl = activeBtn.getAttribute('data-new-tab-url');
    }

    // Show the "Open in New Tab" button
    document.getElementById('btn-open-new-tab').style.display = 'inline-block';

    // Clear active state from all buttons
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });

    // Set active state on clicked button
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Load the file content in the iframe
    const container = document.getElementById('pipelineFileContainer');
    if (!container) {
        console.error('Pipeline file container not found');
        return;
    }

    console.log(`Loading pipeline file: ${fileType} from ${fileUrl}`);

    // All remaining files are HTML files for iframe display
    container.innerHTML = `
        <iframe style="width: 100%; height: 600px; border: none;" 
                src="${fileUrl}"
                onload="console.log('Iframe loaded successfully: ${fileType}')"
                onerror="console.error('Iframe failed to load: ${fileType}')">
            <p>Your browser does not support iframes. <a href="${fileUrl}" target="_blank">Click here to view the file</a>.</p>
        </iframe>
    `;
}

function loadPipelineStructuredData(dataType) {
    const container = document.getElementById('pipelineFileContainer');
    if (!container) return;

    // Update the title using server-side provided mappings
    const titleElement = document.getElementById('pipeline-file-title');
    const titleMeta = document.querySelector(`meta[name="pipeline-title-${dataType}"]`);
    const iconMeta = document.querySelector(`meta[name="pipeline-icon-${dataType}"]`);

    if (titleMeta && iconMeta) {
        const title = titleMeta.getAttribute('content');
        const icon = iconMeta.getAttribute('content');
        titleElement.innerHTML = `<i class="${icon} me-2"></i>${title}`;
    }

    // Hide the "Open in New Tab" button for structured data
    document.getElementById('btn-open-new-tab').style.display = 'none';
    currentPipelineFileUrl = null;
    currentNewTabUrl = null;

    // Clear active state from all buttons
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });

    // Set active state on clicked button
    const buttonId = `btn-${dataType === 'execution_trace' ? 'execution-trace' : dataType.replace('_', '-')}`;
    const activeBtn = document.getElementById(buttonId);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Load pre-rendered content from hidden server-side elements
    const dataElement = document.getElementById(`pipeline-data-${dataType}`);
    if (dataElement) {
        container.innerHTML = dataElement.innerHTML;
    } else {
        container.innerHTML = displayError(`No ${dataType} data available`);
    }
}

// Helper functions for generating structured data tables (following nanoplot pattern)
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

function openInNewTab() {
    if (currentNewTabUrl) {
        // Use the new template route for proper favicon and branding
        window.open(currentNewTabUrl, '_blank');
    } else if (currentPipelineFileUrl) {
        // Fallback to direct file URL if new tab URL not available
        window.open(currentPipelineFileUrl, '_blank');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-load the first available file on page load
document.addEventListener('DOMContentLoaded', function() {
    // Try to load HTML files first, then structured data
    const autoLoadOrder = [
        'execution-report', 
        'execution-timeline', 
        'pipeline-dag',
        'pipeline-parameters',
        'execution-trace', 
        'software-versions'
    ];

    for (const fileType of autoLoadOrder) {
        const button = document.getElementById(`btn-${fileType}`);
        if (button && !button.classList.contains('disabled')) {
            button.click();
            break;
        }
    }
});
