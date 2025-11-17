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
                comments: comments ? {
                    qc: [...(currentSample.comments?.qc || []), {
                        timestamp: new Date().toISOString(),
                        user: 'current_user',  // Will be replaced by backend
                        comment: comments
                    }],
                    other: currentSample.comments?.other || ''
                } : currentSample.comments
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log('QC/comments saved successfully:', result);
            currentSample.qc = status;
            if (comments) {
                // Update comments structure
                if (!currentSample.comments) {
                    currentSample.comments = {qc: [], other: ''};
                }
                currentSample.comments.qc = currentSample.comments.qc || [];
                currentSample.comments.qc.push({
                    timestamp: new Date().toISOString(),
                    user: 'current_user',
                    comment: comments
                });
            }

            const qcStatus = document.getElementById('currentQCStatus');
            if (qcStatus) {
                qcStatus.innerHTML = `<span class="badge ${getQCBadgeClass(status)}">${status.toUpperCase()}</span>`;
            }

            // Refresh QC comments display if a comment was added
            if (comments) {
                refreshQCComments();
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
 * Add QC comment
 */
async function addQCComment() {
    if (!currentSample) return;

    const qcCommentInput = document.getElementById('qcCommentInput');
    const comment = qcCommentInput ? qcCommentInput.value.trim() : '';

    if (!comment) {
        showError('Please enter a QC comment');
        return;
    }

    const url = getSampleApiUrl('qc', currentSample.sample_id);
    if (!url) {
        showError('QC API URL not available');
        return;
    }
    console.log('🔍 QC Comment Update URL:', url);

    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                qc: currentSample.qc,
                comments: {
                    qc: [...(currentSample.comments?.qc || []), {
                        timestamp: new Date().toISOString(),
                        user: 'current_user',  // Will be replaced by backend
                        comment: comment
                    }],
                    other: currentSample.comments?.other || ''
                }
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log('QC comment saved successfully:', result);
            
            // Update local sample data
            if (!currentSample.comments) {
                currentSample.comments = {qc: [], other: ''};
            }
            currentSample.comments.qc = currentSample.comments.qc || [];
            currentSample.comments.qc.push({
                timestamp: new Date().toISOString(),
                user: 'current_user',
                comment: comment
            });

            // Clear input
            if (qcCommentInput) {
                qcCommentInput.value = '';
            }

            // Refresh QC comments display
            refreshQCComments();
            showSuccess('QC comment added successfully');
        } else {
            const result = await response.json();
            showError('Failed to add QC comment: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

/**
 * Save general comments
 */
async function saveGeneralComments() {
    if (!currentSample) return;

    const commentsElement = document.getElementById('generalComments');
    const comments = commentsElement ? commentsElement.value : '';

    const url = getSampleApiUrl('comment', currentSample.sample_id);
    if (!url) {
        showError('Comment API URL not available');
        return;
    }
    console.log('🔍 General Comments Update URL:', url);

    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                comments: {
                    qc: currentSample.comments?.qc || [],
                    other: comments
                }
            })
        });

        const result = await response.json();

        if (response.ok) {
            if (!currentSample.comments) {
                currentSample.comments = {qc: [], other: ''};
            }
            currentSample.comments.other = comments;
            showSuccess('General comments saved successfully');
        } else {
            showError('Failed to save general comments: ' + (result.error || 'Unknown error'));
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

/**
 * Refresh QC comments display
 */
function refreshQCComments() {
    const container = document.getElementById('qcCommentsContainer');
    if (!container || !currentSample?.comments?.qc) return;

    const qcComments = currentSample.comments.qc;
    
    if (qcComments.length === 0) {
        container.innerHTML = `
            <div class="text-muted fst-italic">
                <small>No QC comments yet</small>
            </div>
        `;
        return;
    }

    // Display comments in chronological order (oldest first)
    const commentsHtml = qcComments
        .slice()
        .map(comment => `
            <div class="qc-comment-item mb-2 p-2 bg-light rounded border-start border-warning border-3">
                <div class="qc-comment-text mb-1">${escapeHtml(comment.comment)}</div>
                <div class="qc-comment-meta">
                    <small class="text-muted">
                        <i class="bi bi-person me-1"></i>${escapeHtml(comment.user)}
                        <span class="mx-1">•</span>
                        <i class="bi bi-clock me-1"></i>${formatDate(comment.timestamp)}
                    </small>
                </div>
            </div>
        `)
        .join('');

    container.innerHTML = commentsHtml;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date for display
 */
function formatDate(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (e) {
        return timestamp?.slice(0, 16) || 'Unknown';
    }
}
