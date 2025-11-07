/**
 * Main sample view functionality
 * Depends on: sample_core.js, sample_classification.js, sample_nanoplot.js
 */

// View-specific global variables
let qcFailModal = null;

// Page initialization function called by template
function initializeSampleOverview() {
    // Initialize QC modal
    const qcModalElement = document.getElementById('qcFailModal');
    if (qcModalElement) {
        qcFailModal = new bootstrap.Modal(qcModalElement);
    }
    
    // Setup modern event delegation
    setupQCEventListeners();
}


/**
 * Update QC status
 */
async function updateQC(status, comments = '') {
    if (!currentSample) return;

    const url = getSampleApiUrl('qc', currentSample.sample_id);
    if (!url) {
        showError('QC API URL not available');
        return;
    }
    console.log('🔍 QC Update URL:', url);

    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                qc: status,
                comments: comments || ''
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log('QC/comments saved successfully:', result);
            currentSample.qc = status;
            if (comments) {
                currentSample.comments = comments;
                updateElement('generalComments', comments, 'value');
            }

            const qcStatus = document.getElementById('currentQCStatus');
            if (qcStatus) {
                qcStatus.innerHTML = `<span class="badge ${getQCBadgeClass(status)}">${status.toUpperCase()}</span>`;
            }

            showSuccess(`QC status updated to ${status.toUpperCase()}`);
        } else {
            showError('Failed to update QC: ' + result.error);
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Show failure modal
 */
function showFailModal() {
    const failureComments = document.getElementById('failureComments');
    if (failureComments) {
        failureComments.value = '';
    }
    if (qcFailModal) {
        qcFailModal.show();
    }
}

/**
 * Confirm QC failure
 */
function confirmFailQC() {
    const failureComments = document.getElementById('failureComments');
    const comments = failureComments ? failureComments.value.trim() : '';

    if (!comments) {
        alert('Please provide a reason for the QC failure.');
        return;
    }

    if (qcFailModal) {
        qcFailModal.hide();
    }
    updateQC('failed', comments);
}

/**
 * Save comments
 */
async function saveComments() {
    if (!currentSample) return;

    const commentsElement = document.getElementById('generalComments');
    const comments = commentsElement ? commentsElement.value : '';

    const url = getSampleApiUrl('comment', currentSample.sample_id);
    if (!url) {
        showError('Comment API URL not available');
        return;
    }
    console.log('🔍 Comments Update URL:', url);

    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
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

/**
 * Setup QC event listeners using modern event delegation
 */
function setupQCEventListeners() {
    // QC button event delegation
    document.addEventListener('click', function(event) {
        const qcButton = event.target.closest('.qc-btn');
        if (!qcButton) return;
        
        event.preventDefault();
        event.stopPropagation();
        
        const status = qcButton.dataset.qcStatus;
        console.log('QC button clicked:', status);
        
        if (status === 'failed') {
            showFailModal();
        } else {
            updateQC(status);
        }
    });
    
    // QC fail modal confirm button
    const confirmButton = document.getElementById('confirmFailQCBtn');
    if (confirmButton) {
        confirmButton.addEventListener('click', function() {
            confirmFailQC();
        });
    }
}

/**
 * Show QC failure modal
 */
function showFailModal() {
    if (qcFailModal) {
        // Clear previous comments
        const failureComments = document.getElementById('failureComments');
        if (failureComments) {
            failureComments.value = '';
        }
        qcFailModal.show();
    }
}

/**
 * Confirm QC failure with comments
 */
function confirmFailQC() {
    const failureComments = document.getElementById('failureComments');
    const comments = failureComments ? failureComments.value.trim() : '';
    
    if (!comments) {
        showError('Please provide a reason for the QC failure');
        return;
    }
    
    // Close modal and update QC
    if (qcFailModal) {
        qcFailModal.hide();
    }
    updateQC('failed', comments);
}
