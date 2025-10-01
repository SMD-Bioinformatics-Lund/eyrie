// Nanoplot view JavaScript functionality

let samples = [];
let currentSample = null;
let currentPlotType = null;

// Plot type mappings for file names
const plotTypeMap = {
    'report': {
        unprocessed: 'NanoPlot-report.html',
        processed: 'NanoPlot-report.html',
        title: 'NanoPlot Report'
    },
    'length-quality-scatter': {
        unprocessed: 'LengthvsQualityScatterPlot_dot.png',
        processed: 'LengthvsQualityScatterPlot_dot.png',
        title: 'Length vs Quality Scatter Plot'
    },
    'non-weighted-histogram': {
        unprocessed: 'Non_weightedHistogramReadlength.png',
        processed: 'Non_weightedHistogramReadlength.png',
        title: 'Non-weighted Histogram Read Length'
    },
    'weighted-histogram': {
        unprocessed: 'WeightedHistogramReadlength.png',
        processed: 'WeightedHistogramReadlength.png',
        title: 'Weighted Histogram Read Length'
    },
    'yield-by-length': {
        unprocessed: 'Yield_By_Length.png',
        processed: 'Yield_By_Length.png',
        title: 'Yield by Length'
    }
};

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadSamples();
    loadCurrentUser();
    setupEventListeners();
});

function setupEventListeners() {
    // Sample selection
    document.getElementById('sampleSelect').addEventListener('change', function() {
        const sampleId = this.value;
        if (sampleId) {
            loadSampleData(sampleId);
        } else {
            clearViews();
        }
    });

    // Sample search
    document.getElementById('sampleSearch').addEventListener('input', function() {
        filterSamples(this.value);
    });
}

async function loadSamples() {
    try {
        const response = await fetch(`${window.API_BASE}/samples`);
        if (response.ok) {
            samples = await response.json();
            populateSampleSelect();
        } else {
            console.error('Failed to load samples');
        }
    } catch (error) {
        console.error('Error loading samples:', error);
    }
}

function populateSampleSelect() {
    const select = document.getElementById('sampleSelect');
    select.innerHTML = '<option value="">Select a sample...</option>';
    
    samples.forEach(sample => {
        const option = document.createElement('option');
        option.value = sample.sample_id;
        option.textContent = `${sample.sample_name} (${sample.sample_id})`;
        select.appendChild(option);
    });
}

function filterSamples(searchTerm) {
    const select = document.getElementById('sampleSelect');
    const options = select.querySelectorAll('option');
    
    options.forEach(option => {
        if (option.value === '') return; // Skip the default option
        
        const text = option.textContent.toLowerCase();
        const matches = text.includes(searchTerm.toLowerCase());
        option.style.display = matches ? '' : 'none';
    });
}

async function loadSampleData(sampleId) {
    try {
        const response = await fetch(`${window.API_BASE}/samples/${sampleId}`);
        if (response.ok) {
            currentSample = await response.json();
            updateNanoStats();
            
            // If a plot type was already selected, reload it
            if (currentPlotType) {
                loadNanoplotView(currentPlotType);
            }
        } else {
            console.error('Failed to load sample data');
        }
    } catch (error) {
        console.error('Error loading sample data:', error);
    }
}

function loadNanoplotView(plotType) {
    currentPlotType = plotType;
    
    if (!currentSample) {
        alert('Please select a sample first');
        return;
    }

    // Update active button
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-${plotType}`).classList.add('active');

    // Load plots for both unprocessed and processed
    loadPlot('unprocessed', plotType);
    loadPlot('processed', plotType);
}

function loadPlot(processingType, plotType) {
    const container = document.getElementById(`${processingType}PlotContainer`);
    const plotInfo = plotTypeMap[plotType];
    
    if (!plotInfo) {
        displayError(container, 'Unknown plot type');
        return;
    }

    // Construct the expected file path based on sample structure
    let filePath = null;
    
    if (processingType === 'unprocessed') {
        // Look for unprocessed nanoplot files
        filePath = `nanoplot_unprocessed/${currentSample.sample_id}_nanoplot_unprocessed_${plotInfo.unprocessed}`;
    } else {
        // Look for processed nanoplot files
        filePath = `nanoplot_processed/${currentSample.sample_id}_nanoplot_processed_${plotInfo.processed}`;
    }

    // Check if the file exists and display it
    checkAndDisplayFile(container, filePath, plotInfo.title, processingType);
}

async function checkAndDisplayFile(container, filePath, title, processingType) {
    try {
        const response = await fetch(`/data/${filePath}`, { method: 'HEAD' });
        
        if (response.ok) {
            // File exists, display it
            if (filePath.endsWith('.html')) {
                // Display HTML files in iframe
                container.innerHTML = `
                    <iframe src="/data/${filePath}" 
                            class="w-100 h-100" 
                            style="min-height: 500px; border: none;">
                    </iframe>
                `;
            } else if (filePath.endsWith('.png') || filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) {
                // Display image files
                container.innerHTML = `
                    <div class="text-center p-3">
                        <img src="/data/${filePath}" 
                             class="img-fluid" 
                             alt="${title}"
                             style="max-height: 500px; max-width: 100%;">
                    </div>
                `;
            } else {
                // Other file types - provide download link
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
            // File doesn't exist
            displayError(container, `No ${processingType} ${currentPlotType} data available`);
        }
    } catch (error) {
        console.error('Error checking file:', error);
        displayError(container, `Error loading ${processingType} ${currentPlotType} data`);
    }
}

function displayError(container, message) {
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
        clearStats();
        return;
    }

    // Update unprocessed stats
    const unprocessed = currentSample.nano_stats_unprocessed;
    if (unprocessed) {
        document.getElementById('unproc-reads').textContent = formatNumber(unprocessed.number_of_reads) || '-';
        document.getElementById('unproc-length').textContent = formatLength(unprocessed.mean_read_length) || '-';
        document.getElementById('unproc-quality').textContent = formatQuality(unprocessed.mean_read_quality) || '-';
        document.getElementById('unproc-bases').textContent = formatBases(unprocessed.total_bases) || '-';
    } else {
        document.getElementById('unproc-reads').textContent = '-';
        document.getElementById('unproc-length').textContent = '-';
        document.getElementById('unproc-quality').textContent = '-';
        document.getElementById('unproc-bases').textContent = '-';
    }

    // Update processed stats
    const processed = currentSample.nano_stats_processed;
    if (processed) {
        document.getElementById('proc-reads').textContent = formatNumber(processed.number_of_reads) || '-';
        document.getElementById('proc-length').textContent = formatLength(processed.mean_read_length) || '-';
        document.getElementById('proc-quality').textContent = formatQuality(processed.mean_read_quality) || '-';
        document.getElementById('proc-bases').textContent = formatBases(processed.total_bases) || '-';
    } else {
        document.getElementById('proc-reads').textContent = '-';
        document.getElementById('proc-length').textContent = '-';
        document.getElementById('proc-quality').textContent = '-';
        document.getElementById('proc-bases').textContent = '-';
    }
}

function clearStats() {
    ['unproc-reads', 'unproc-length', 'unproc-quality', 'unproc-bases',
     'proc-reads', 'proc-length', 'proc-quality', 'proc-bases'].forEach(id => {
        document.getElementById(id).textContent = '-';
    });
}

function clearViews() {
    currentSample = null;
    currentPlotType = null;
    
    // Clear plot containers
    ['unprocessedPlotContainer', 'processedPlotContainer'].forEach(id => {
        document.getElementById(id).innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="text-center">
                    <i class="bi bi-graph-up text-muted" style="font-size: 4rem;"></i>
                    <p class="text-muted mt-3">Select a sample and plot type</p>
                </div>
            </div>
        `;
    });
    
    // Clear active button
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Clear stats
    clearStats();
}

// Utility functions
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

// Action functions
function downloadPlot(processingType) {
    if (!currentSample || !currentPlotType) {
        alert('Please select a sample and plot type first');
        return;
    }

    const plotInfo = plotTypeMap[currentPlotType];
    const fileName = processingType === 'unprocessed' ? plotInfo.unprocessed : plotInfo.processed;
    const filePath = `${processingType === 'unprocessed' ? 'nanoplot_unprocessed' : 'nanoplot_processed'}/${currentSample.sample_id}_nanoplot_${processingType}_${fileName}`;
    
    window.open(`/data/${filePath}`, '_blank');
}

// User management functions (shared across views)
async function loadCurrentUser() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/current-user`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('currentUsername').textContent = user.username;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading current user:', error);
        window.location.href = '/login';
    }
}

async function logout() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error during logout:', error);
        window.location.href = '/login';
    }
}
