/**
 * Main sample view functionality
 * Depends on: sample_core.js, sample_classification.js, sample_nanoplot.js
 */

// View-specific global variables
let qcFailModal = null;
let currentView = 'overview';

// Page initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize QC modal
    const qcModalElement = document.getElementById('qcFailModal');
    if (qcModalElement) {
        qcFailModal = new bootstrap.Modal(qcModalElement);
    }
    
    // Load user and sample data
    loadCurrentUser();
    
    // Extract sample ID from URL path: /sample/S001
    const pathParts = window.location.pathname.split('/');
    const sampleId = pathParts[pathParts.length - 1]; // Get last part
    
    if (sampleId) {
        loadSample(sampleId).then(sample => {
            if (sample) {
                renderSampleDetail(sample);
                setupNavigationLinks(sampleId);
            }
        });
    } else {
        showError('No sample ID provided');
    }
});

/**
 * Setup navigation links for sample views
 */
function setupNavigationLinks(sampleId) {
    const classificationLink = document.getElementById('classificationLink');
    const nanoplotLink = document.getElementById('nanoplotLink');
    
    if (classificationLink) {
        classificationLink.href = `/sample/${sampleId}/classification`;
    }
    if (nanoplotLink) {
        nanoplotLink.href = `/sample/${sampleId}/nanoplot`;
    }
}

/**
 * Render sample detail information
 */
function renderSampleDetail(sample) {
    // Update title
    updateSampleTitle(sample);
    
    // Update general information
    updateElement('infoSampleName', sample.sample_name);
    updateElement('infoSampleId', sample.sample_id);
    updateElement('infoSequencingRun', sample.sequencing_run_id);
    updateElement('infoLimsId', sample.lims_id);
    
    // Update classification badge
    const classificationElement = document.getElementById('infoClassification');
    if (classificationElement && sample.classification) {
        const badgeClass = sample.classification === '16S' ? 'bg-primary' : 'bg-info';
        classificationElement.innerHTML = `<span class="badge ${badgeClass}">${sample.classification}</span>`;
    } else if (classificationElement) {
        classificationElement.textContent = '--';
    }
    
    // Update dates
    updateElement('infoCreatedDate', formatDate(sample.created_date));
    updateElement('infoUpdatedDate', formatDate(sample.updated_date));
    
    // Update QC status
    const qcStatus = document.getElementById('currentQCStatus');
    if (qcStatus) {
        qcStatus.innerHTML = `<span class="badge ${getQCBadgeClass(sample.qc)}">${sample.qc.toUpperCase()}</span>`;
    }
    
    // Update comments
    updateElement('generalComments', sample.comments, 'value');
    
    // Update Krona frame
    const kronaFrame = document.getElementById('kronaFrame');
    if (kronaFrame) {
        if (sample.krona_file) {
            kronaFrame.src = `/data/${sample.krona_file}`;
        } else {
            kronaFrame.srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No Krona plot available</i></div>';
        }
    }
    
    // Set quality frame to show length vs quality scatter plot
    const qualityFrame = document.getElementById('qualityFrame');
    if (qualityFrame) {
        // Use length vs quality scatter plot from nanoplot data (prefer processed, fallback to unprocessed)
        let qualityPlotPath = null;
        if (sample.nanoplot?.processed?.length_quality_scatter) {
            qualityPlotPath = sample.nanoplot.processed.length_quality_scatter;
        } else if (sample.nanoplot?.unprocessed?.length_quality_scatter) {
            qualityPlotPath = sample.nanoplot.unprocessed.length_quality_scatter;
        } else if (sample.quality_plot) {
            // Fallback to quality_plot if nanoplot data not available
            qualityPlotPath = sample.quality_plot;
        }
        
        if (qualityPlotPath) {
            qualityFrame.src = `/data/${qualityPlotPath}`;
        } else {
            qualityFrame.srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No quality plot available</i></div>';
        }
    }
    
    // Render statistics
    renderStatistics(sample.statistics || {});
    
    // Render classification summary
    renderOverviewClassificationSummary();
}

/**
 * Helper function to update element content
 */
function updateElement(elementId, value, property = 'textContent') {
    const element = document.getElementById(elementId);
    if (element) {
        if (property === 'value') {
            element.value = value || '';
        } else {
            element[property] = value || '--';
        }
    }
}

/**
 * Render statistics section
 */
function renderStatistics(stats) {
    // Use processed NanoStats data for Summary Statistics (prioritize processed over unprocessed)
    const nanoStats = currentSample?.nano_stats_processed || currentSample?.nano_stats_unprocessed || {};
    
    // Update statistics elements
    updateElement('statNumberReads', nanoStats.number_of_reads ? formatNumber(nanoStats.number_of_reads) : '--');
    updateElement('statMeanLength', nanoStats.mean_read_length ? `${formatNumber(Math.round(nanoStats.mean_read_length))} bp` : '--');
    updateElement('statMeanQuality', nanoStats.mean_read_quality ? `Q${nanoStats.mean_read_quality.toFixed(1)}` : '--');
    updateElement('statMedianLength', nanoStats.median_read_length ? `${formatNumber(Math.round(nanoStats.median_read_length))} bp` : '--');
    updateElement('statMedianQuality', nanoStats.median_read_quality ? `Q${nanoStats.median_read_quality.toFixed(1)}` : '--');
    updateElement('statReadN50', nanoStats.read_length_n50 ? `${formatNumber(Math.round(nanoStats.read_length_n50))} bp` : '--');
    updateElement('statStdevLength', nanoStats.stdev_read_length ? `${formatNumber(Math.round(nanoStats.stdev_read_length))} bp` : '--');
    
    // Format total bases with appropriate unit
    if (nanoStats.total_bases) {
        updateElement('statTotalBases', formatBases(nanoStats.total_bases));
    } else {
        updateElement('statTotalBases', '--');
    }
}

/**
 * Update QC status
 */
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

/**
 * Render classification summary for overview
 */
function renderOverviewClassificationSummary() {
    if (!currentSample || !currentSample.taxonomic_data) {
        updateElement('overviewTotalSpecies', '0');
        updateElement('overviewDominantSpecies', '-');
        updateElement('overviewFlaggedContaminants', '0');
        updateElement('overviewFlaggedTopHits', '0');
        
        const topHitsList = document.getElementById('overviewTopHitsList');
        const contaminantsList = document.getElementById('overviewContaminantsList');
        if (topHitsList) topHitsList.style.display = 'none';
        if (contaminantsList) contaminantsList.style.display = 'none';
        return;
    }

    const data = currentSample.taxonomic_data;
    const flaggedContaminants = currentSample.flagged_contaminants || [];
    const flaggedTopHits = currentSample.flagged_top_hits || [];
    
    // Update total species
    updateElement('overviewTotalSpecies', data.total_species || (data.hits ? data.hits.length : 0));
    
    // Update dominant species
    if (data.hits && data.hits.length > 0) {
        const dominant = data.hits.reduce((prev, current) => 
            (prev.abundance > current.abundance) ? prev : current
        );
        updateElement('overviewDominantSpecies', dominant.species);
    } else {
        updateElement('overviewDominantSpecies', '-');
    }
    
    // Update flagged counts
    updateElement('overviewFlaggedContaminants', flaggedContaminants.length);
    updateElement('overviewFlaggedTopHits', flaggedTopHits.length);
    
    // Show/hide top hits list with abundance data
    const topHitsList = document.getElementById('overviewTopHitsList');
    const topHitsDiv = document.getElementById('overviewTopHitsSpecies');
    
    if (flaggedTopHits.length > 0) {
        if (topHitsList) topHitsList.style.display = 'block';
        if (topHitsDiv) {
            topHitsDiv.innerHTML = flaggedTopHits
                .map(species => {
                    const hit = data.hits ? data.hits.find(h => h.species === species) : null;
                    const abundance = hit ? hit.abundance.toFixed(2) + '%' : '';
                    return `<span class="badge bg-success me-1 mb-1" title="Abundance: ${abundance}">${species} ${abundance ? '(' + abundance + ')' : ''}</span>`;
                })
                .join('');
        }
    } else {
        if (topHitsList) topHitsList.style.display = 'none';
    }
    
    // Show/hide contaminants list with abundance data
    const contaminantsList = document.getElementById('overviewContaminantsList');
    const contaminantsDiv = document.getElementById('overviewContaminantsSpecies');
    
    if (flaggedContaminants.length > 0) {
        if (contaminantsList) contaminantsList.style.display = 'block';
        if (contaminantsDiv) {
            contaminantsDiv.innerHTML = flaggedContaminants
                .map(species => {
                    const hit = data.hits ? data.hits.find(h => h.species === species) : null;
                    const abundance = hit ? hit.abundance.toFixed(2) + '%' : '';
                    return `<span class="badge bg-warning text-dark me-1 mb-1" title="Abundance: ${abundance}">${species} ${abundance ? '(' + abundance + ')' : ''}</span>`;
                })
                .join('');
        }
    } else {
        if (contaminantsList) contaminantsList.style.display = 'none';
    }
}

/**
 * View switching functionality
 */
function showView(viewName) {
    currentView = viewName;
    
    // Hide all views
    document.querySelectorAll('.view-content').forEach(view => {
        view.style.display = 'none';
    });
    
    // Show selected view
    const targetView = document.getElementById(`${viewName}View`);
    if (targetView) {
        targetView.style.display = 'block';
    }
    
    // Update navbar active state
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const activeLink = document.getElementById(`${viewName}Link`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    // Load view-specific data
    if (viewName === 'classification') {
        loadClassificationData();
    } else if (viewName === 'nanoplot') {
        updateNanoStats();
    }
}