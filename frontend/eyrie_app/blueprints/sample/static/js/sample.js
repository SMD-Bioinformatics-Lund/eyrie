let currentSample = null;
let qcFailModal = null;
let currentView = 'overview';
let flaggedContaminants = new Set();
let currentPlotType = null;

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
        document.getElementById('kronaFrame').src = `/data/${sample.krona_file}`;
    } else {
        document.getElementById('kronaFrame').srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No Krona plot available</i></div>';
    }
    
    // Use NanoPlot LengthvsQualityScatterPlot for quality plot
    const qualityPlotPath = `test/nanoplot_unprocessed/${sample.sample_id}_nanoplot_unprocessed_LengthvsQualityScatterPlot_dot.html`;
    document.getElementById('qualityFrame').src = `/data/${qualityPlotPath}`;
    
    renderStatistics(sample.statistics || {});
}

function renderStatistics(stats) {
    // Use processed NanoStats data for Summary Statistics (prioritize processed over unprocessed)
    const nanoStats = currentSample?.nano_stats_processed || currentSample?.nano_stats_unprocessed || {};
    
    // Number of Reads
    const numberReads = nanoStats.number_of_reads;
    document.getElementById('statNumberReads').textContent = numberReads ? formatNumber(numberReads) : '--';
    
    // Mean Read Length
    const meanLength = nanoStats.mean_read_length;
    document.getElementById('statMeanLength').textContent = meanLength ? `${formatNumber(Math.round(meanLength))} bp` : '--';
    
    // Mean Read Quality
    const meanQuality = nanoStats.mean_read_quality;
    document.getElementById('statMeanQuality').textContent = meanQuality ? `Q${meanQuality.toFixed(1)}` : '--';
    
    // Median Read Length
    const medianLength = nanoStats.median_read_length;
    document.getElementById('statMedianLength').textContent = medianLength ? `${formatNumber(Math.round(medianLength))} bp` : '--';
    
    // Median Read Quality
    const medianQuality = nanoStats.median_read_quality;
    document.getElementById('statMedianQuality').textContent = medianQuality ? `Q${medianQuality.toFixed(1)}` : '--';
    
    // Read Length N50
    const readN50 = nanoStats.read_length_n50;
    document.getElementById('statReadN50').textContent = readN50 ? `${formatNumber(Math.round(readN50))} bp` : '--';
    
    // STDEV Read Length
    const stdevLength = nanoStats.stdev_read_length;
    document.getElementById('statStdevLength').textContent = stdevLength ? `${formatNumber(Math.round(stdevLength))} bp` : '--';
    
    // Total Bases
    const totalBases = nanoStats.total_bases;
    if (totalBases) {
        if (totalBases >= 1e9) {
            document.getElementById('statTotalBases').textContent = `${(totalBases / 1e9).toFixed(1)} Gb`;
        } else if (totalBases >= 1e6) {
            document.getElementById('statTotalBases').textContent = `${(totalBases / 1e6).toFixed(1)} Mb`;
        } else if (totalBases >= 1e3) {
            document.getElementById('statTotalBases').textContent = `${(totalBases / 1e3).toFixed(1)} Kb`;
        } else {
            document.getElementById('statTotalBases').textContent = `${formatNumber(totalBases)} bp`;
        }
    } else {
        document.getElementById('statTotalBases').textContent = '--';
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

// View switching functionality
function showView(viewName) {
    currentView = viewName;
    
    // Hide all views
    document.querySelectorAll('.view-content').forEach(view => {
        view.style.display = 'none';
    });
    
    // Show selected view
    document.getElementById(`${viewName}View`).style.display = 'block';
    
    // Update navbar active state
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.getElementById(`${viewName}Link`).classList.add('active');
    
    // Load view-specific data
    if (viewName === 'classification') {
        loadClassificationData();
    } else if (viewName === 'nanoplot') {
        loadNanoplotData();
    }
}

// Classification view functions
function loadClassificationData() {
    if (!currentSample) return;
    
    // Load Krona plot in classification view
    if (currentSample.krona_file) {
        const frame = document.getElementById('classificationKronaFrame');
        frame.src = `/data/${currentSample.krona_file}`;
        frame.style.width = '100%';
        frame.style.height = '600px';
        frame.style.border = 'none';
    } else {
        document.getElementById('classificationKronaFrame').srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No Krona plot available</i></div>';
    }
    
    // Load abundance table
    displayAbundanceTable();
    updateClassificationSummary();
}

function displayAbundanceTable() {
    const tbody = document.getElementById('contaminationTableBody');
    
    if (!currentSample || !currentSample.taxonomic_data || !currentSample.taxonomic_data.top_species) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center py-4">
                    <div class="text-muted">
                        <i class="bi bi-exclamation-circle text-warning" style="font-size: 2rem;"></i>
                        <p class="mt-2">No taxonomic data available</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    // Load saved contamination flags from database
    flaggedContaminants.clear();
    if (currentSample.flagged_contaminants) {
        currentSample.flagged_contaminants.forEach(species => {
            flaggedContaminants.add(species);
        });
    }
    
    const species = currentSample.taxonomic_data.top_species.sort((a, b) => b.abundance - a.abundance);
    
    tbody.innerHTML = '';
    species.forEach((organism, index) => {
        const row = document.createElement('tr');
        row.className = 'contamination-row';
        row.dataset.species = organism.species;
        
        // Check if this species is flagged (either from database or by abundance < 1.0)
        const isContaminant = flaggedContaminants.has(organism.species);
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <small class="text-muted me-2">${index + 1}.</small>
                    <div>
                        <div class="fw-semibold">${organism.species}</div>
                        <small class="text-muted">${organism.genus || 'N/A'} - ${organism.family || 'N/A'}</small>
                    </div>
                </div>
            </td>
            <td>
                <div class="d-flex align-items-center">
                    <span class="badge ${getAbundanceBadgeClass(organism.abundance)} me-2">
                        ${organism.abundance.toFixed(2)}%
                    </span>
                    <div class="progress flex-grow-1" style="height: 8px;">
                        <div class="progress-bar" style="width: ${Math.min(organism.abundance, 100)}%"></div>
                    </div>
                </div>
            </td>
            <td>
                <button class="btn btn-sm ${isContaminant ? 'btn-danger' : 'btn-outline-secondary'} flag-btn" 
                        onclick="toggleContaminantFlag('${organism.species}', this)">
                    <i class="bi ${isContaminant ? 'bi-flag-fill' : 'bi-flag'}"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function getAbundanceBadgeClass(abundance) {
    if (abundance >= 10) return 'bg-success';
    if (abundance >= 5) return 'bg-warning';
    if (abundance >= 1) return 'bg-info';
    return 'bg-secondary';
}

function toggleContaminantFlag(species, button) {
    console.log('Toggling contamination flag for:', species);
    console.log('Current flagged contaminants:', Array.from(flaggedContaminants));
    
    if (flaggedContaminants.has(species)) {
        console.log('Removing flag for:', species);
        flaggedContaminants.delete(species);
        button.className = 'btn btn-sm btn-outline-secondary flag-btn';
        button.innerHTML = '<i class="bi bi-flag"></i>';
    } else {
        console.log('Adding flag for:', species);
        flaggedContaminants.add(species);
        button.className = 'btn btn-sm btn-danger flag-btn';
        button.innerHTML = '<i class="bi bi-flag-fill"></i>';
    }
    updateClassificationSummary();
    saveContaminationFlags();
}

async function saveContaminationFlags() {
    if (!currentSample) {
        console.log('No current sample, skipping save');
        return;
    }
    
    console.log('Saving contamination flags:', Array.from(flaggedContaminants));
    console.log('API URL will be:', `${window.API_BASE}/samples/${currentSample.sample_id}/contamination`);
    
    try {
        const response = await fetch(`${window.API_BASE}/samples/${currentSample.sample_id}/contamination`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                flagged_species: Array.from(flaggedContaminants)
            })
        });
        
        console.log('Response status:', response.status);
        const responseText = await response.text();
        console.log('Response body:', responseText);
        
        if (response.ok) {
            console.log('Contamination flags saved successfully');
            // Update the current sample data to reflect the saved flags
            currentSample.flagged_contaminants = Array.from(flaggedContaminants);
        } else {
            console.error('Failed to save contamination flags:', response.status, response.statusText);
            console.error('Response body:', responseText);
        }
    } catch (error) {
        console.error('Error saving contamination flags:', error);
    }
}

function updateClassificationSummary() {
    if (!currentSample || !currentSample.taxonomic_data) {
        document.getElementById('totalSpecies').textContent = '0';
        document.getElementById('dominantSpecies').textContent = '-';
        document.getElementById('flaggedContaminants').textContent = '0';
        document.getElementById('diversityIndex').textContent = '0.0';
        return;
    }

    const data = currentSample.taxonomic_data;
    
    document.getElementById('totalSpecies').textContent = data.total_species || 0;
    
    if (data.top_species && data.top_species.length > 0) {
        const dominant = data.top_species.reduce((prev, current) => 
            (prev.abundance > current.abundance) ? prev : current
        );
        document.getElementById('dominantSpecies').textContent = dominant.species;
    } else {
        document.getElementById('dominantSpecies').textContent = '-';
    }
    
    document.getElementById('flaggedContaminants').textContent = flaggedContaminants.size;
    
    const diversity = calculateShannonDiversity(data.top_species || []);
    document.getElementById('diversityIndex').textContent = diversity.toFixed(2);
}

function calculateShannonDiversity(species) {
    if (!species || species.length === 0) return 0;
    
    const total = species.reduce((sum, sp) => sum + sp.abundance, 0);
    if (total === 0) return 0;
    
    let diversity = 0;
    species.forEach(sp => {
        if (sp.abundance > 0) {
            const proportion = sp.abundance / total;
            diversity -= proportion * Math.log(proportion);
        }
    });
    
    return diversity;
}

function refreshKronaPlot() {
    if (currentSample && currentSample.krona_file) {
        const frame = document.getElementById('classificationKronaFrame');
        frame.src = frame.src; // Reload the iframe
    }
}

function downloadKronaPlot() {
    if (currentSample && currentSample.krona_file) {
        window.open(`/data/${currentSample.krona_file}`, '_blank');
    } else {
        alert('No Krona plot available for download');
    }
}

function exportContaminationData() {
    if (!currentSample || !currentSample.taxonomic_data) {
        alert('No data available for export');
        return;
    }

    const data = currentSample.taxonomic_data.top_species || [];
    const csvContent = "data:text/csv;charset=utf-8," 
        + "Species,Genus,Family,Abundance,Flagged\n"
        + data.map(sp => 
            `"${sp.species}","${sp.genus || 'N/A'}","${sp.family || 'N/A'}",${sp.abundance},${flaggedContaminants.has(sp.species) ? 'Yes' : 'No'}`
        ).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${currentSample.sample_id}_abundance_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Nanoplot view functions
function loadNanoplotData() {
    if (!currentSample) return;
    updateNanoStats();
}

const plotTypeMap = {
    'report': {
        unprocessed: 'NanoPlot-report.html',
        processed: 'NanoPlot-report.html',
        title: 'NanoPlot Report'
    },
    'length-quality-scatter': {
        unprocessed: 'LengthvsQualityScatterPlot_dot.html',
        processed: 'LengthvsQualityScatterPlot_dot.html',
        title: 'Length vs Quality Scatter Plot'
    },
    'non-weighted-histogram': {
        unprocessed: 'Non_weightedHistogramReadlength.html',
        processed: 'Non_weightedHistogramReadlength.html',
        title: 'Non-weighted Histogram Read Length'
    },
    'weighted-histogram': {
        unprocessed: 'WeightedHistogramReadlength.html',
        processed: 'WeightedHistogramReadlength.html',
        title: 'Weighted Histogram Read Length'
    },
    'yield-by-length': {
        unprocessed: 'Yield_By_Length.html',
        processed: 'Yield_By_Length.html',
        title: 'Yield by Length'
    }
};

function loadNanoplotView(plotType) {
    currentPlotType = plotType;
    
    if (!currentSample) {
        alert('No sample loaded');
        return;
    }

    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-${plotType}`).classList.add('active');

    loadPlot('unprocessed', plotType);
    loadPlot('processed', plotType);
}

function loadPlot(processingType, plotType) {
    const container = document.getElementById(`${processingType}PlotContainer`);
    const plotInfo = plotTypeMap[plotType];
    
    if (!plotInfo) {
        displayPlotError(container, 'Unknown plot type');
        return;
    }

    let filePath = null;
    
    if (processingType === 'unprocessed') {
        filePath = `test/nanoplot_unprocessed/${currentSample.sample_id}_nanoplot_unprocessed_${plotInfo.unprocessed}`;
    } else {
        filePath = `test/nanoplot_processed/${currentSample.sample_id}_nanoplot_processed_${plotInfo.processed}`;
    }

    checkAndDisplayFile(container, filePath, plotInfo.title, processingType);
}

async function checkAndDisplayFile(container, filePath, title, processingType) {
    try {
        const response = await fetch(`/data/${filePath}`, { method: 'HEAD' });
        
        if (response.ok) {
            if (filePath.endsWith('.html')) {
                container.innerHTML = `
                    <iframe src="/data/${filePath}" 
                            class="w-100 h-100" 
                            style="min-height: 500px; border: none;">
                    </iframe>
                `;
            } else if (filePath.endsWith('.png') || filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) {
                container.innerHTML = `
                    <div class="text-center p-3">
                        <img src="/data/${filePath}" 
                             class="img-fluid" 
                             alt="${title}"
                             style="max-height: 500px; max-width: 100%;">
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="d-flex justify-content-center align-items-center h-100">
                        <div class="text-center">
                            <i class="bi bi-file-earmark text-info" style="font-size: 4rem;"></i>
                            <p class="text-muted mt-3">${title}</p>
                            <a href="/data/${filePath}" class="btn btn-primary" target="_blank">
                                <i class="bi bi-download me-2"></i>Download File
                            </a>
                        </div>
                    </div>
                `;
            }
        } else {
            displayPlotError(container, `No ${processingType} ${currentPlotType} data available`);
        }
    } catch (error) {
        console.error('Error checking file:', error);
        displayPlotError(container, `Error loading ${processingType} ${currentPlotType} data`);
    }
}

function displayPlotError(container, message) {
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center">
                <i class="bi bi-exclamation-circle text-warning" style="font-size: 4rem;"></i>
                <p class="text-muted mt-3">${message}</p>
            </div>
        </div>
    `;
}

function updateNanoStats() {
    if (!currentSample) {
        clearNanoStats();
        return;
    }

    const unprocessed = currentSample.nano_stats_unprocessed;
    if (unprocessed) {
        document.getElementById('unproc-reads').textContent = formatNumber(unprocessed.number_of_reads) || '-';
        document.getElementById('unproc-length').textContent = formatLength(unprocessed.mean_read_length) || '-';
        document.getElementById('unproc-quality').textContent = formatQuality(unprocessed.mean_read_quality) || '-';
        document.getElementById('unproc-bases').textContent = formatBases(unprocessed.total_bases) || '-';
    } else {
        ['unproc-reads', 'unproc-length', 'unproc-quality', 'unproc-bases'].forEach(id => {
            document.getElementById(id).textContent = '-';
        });
    }

    const processed = currentSample.nano_stats_processed;
    if (processed) {
        document.getElementById('proc-reads').textContent = formatNumber(processed.number_of_reads) || '-';
        document.getElementById('proc-length').textContent = formatLength(processed.mean_read_length) || '-';
        document.getElementById('proc-quality').textContent = formatQuality(processed.mean_read_quality) || '-';
        document.getElementById('proc-bases').textContent = formatBases(processed.total_bases) || '-';
    } else {
        ['proc-reads', 'proc-length', 'proc-quality', 'proc-bases'].forEach(id => {
            document.getElementById(id).textContent = '-';
        });
    }
}

function clearNanoStats() {
    ['unproc-reads', 'unproc-length', 'unproc-quality', 'unproc-bases',
     'proc-reads', 'proc-length', 'proc-quality', 'proc-bases'].forEach(id => {
        document.getElementById(id).textContent = '-';
    });
}

function formatNumber(num) {
    if (!num) return null;
    return new Intl.NumberFormat().format(num);
}

function formatLength(length) {
    if (!length) return null;
    return `${Math.round(length)} bp`;
}

function formatQuality(quality) {
    if (!quality) return null;
    return `${quality.toFixed(1)}`;
}

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

function downloadPlot(processingType) {
    if (!currentSample || !currentPlotType) {
        alert('Please select a plot type first');
        return;
    }

    const plotInfo = plotTypeMap[currentPlotType];
    const fileName = processingType === 'unprocessed' ? plotInfo.unprocessed : plotInfo.processed;
    const filePath = `${processingType === 'unprocessed' ? 'nanoplot_unprocessed' : 'nanoplot_processed'}/${currentSample.sample_id}_nanoplot_${processingType}_${fileName}`;
    
    window.open(`/data/${filePath}`, '_blank');
}
