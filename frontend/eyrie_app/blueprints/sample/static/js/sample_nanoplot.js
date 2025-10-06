/**
 * Nanoplot-specific functionality
 */

// Global variables for nanoplot
let currentPlotType = null;

/**
 * Initialize nanoplot view
 */
function initializeNanoplotView(sampleId) {
    loadSample(sampleId).then(sample => {
        if (sample) {
            updateSampleTitle(sample);
            updateNanoStats();
        }
    });
}

/**
 * Load nanoplot view with specific plot type
 */
function loadNanoplotView(plotType) {
    currentPlotType = plotType;
    
    if (!currentSample) {
        alert('No sample loaded');
        return;
    }

    // Update button states
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`btn-${plotType}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Load both plots
    loadPlot('unprocessed', plotType);
    loadPlot('processed', plotType);
}

/**
 * Show summary statistics instead of plots
 */
function showSummaryStats() {
    if (!currentSample) {
        alert('No sample loaded');
        return;
    }

    // Update button states
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById('btn-summary');
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Display detailed statistics in both containers
    displayDetailedStats('unprocessed');
    displayDetailedStats('processed');
}

/**
 * Load individual plot
 */
function loadPlot(processingType, plotType) {
    const container = document.getElementById(`${processingType}PlotContainer`);
    if (!container) return;
    
    const plotTypeMap = {
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

    const plotInfo = plotTypeMap[plotType];
    if (!plotInfo) {
        displayPlotError(container, 'Unknown plot type');
        return;
    }

    // Use structured nanoplot data
    let filePath = null;
    
    if (currentSample.nanoplot && currentSample.nanoplot[processingType]) {
        const plotData = currentSample.nanoplot[processingType];
        
        // Map plot types to structured data fields
        switch (plotType) {
            case 'length-quality-scatter':
                filePath = plotData.length_quality_scatter;
                break;
            case 'non-weighted-histogram':
                filePath = plotData.histogram_unweighted;
                break;
            case 'weighted-histogram':
                filePath = plotData.histogram_weighted;
                break;
            case 'yield-by-length':
                filePath = plotData.yield_by_length;
                break;
        }
    }
    
    if (filePath) {
        checkAndDisplayFile(container, filePath, plotInfo.title, processingType);
    } else {
        displayPlotError(container, `No ${processingType} ${plotType} data available`);
    }
}

/**
 * Check and display file
 */
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
        displayPlotError(container, `Error loading ${processingType} ${currentPlotType} data`);
    }
}

/**
 * Display plot error
 */
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

/**
 * Display detailed statistics in a container
 */
function displayDetailedStats(processingType) {
    const container = document.getElementById(`${processingType}PlotContainer`);
    if (!container) return;

    const stats = processingType === 'unprocessed' ? 
        currentSample.nano_stats_unprocessed : 
        currentSample.nano_stats_processed;

    if (!stats) {
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="text-center">
                    <i class="bi bi-exclamation-circle text-warning" style="font-size: 4rem;"></i>
                    <p class="text-muted mt-3">No ${processingType} statistics available</p>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="p-3">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Mean read length</td>
                        <td>${formatLength(stats.mean_read_length) || '-'}</td>
                    </tr>
                    <tr>
                        <td>Mean read quality</td>
                        <td>${formatQuality(stats.mean_read_quality) || '-'}</td>
                    </tr>
                    <tr>
                        <td>Median read length</td>
                        <td>${formatLength(stats.median_read_length) || '-'}</td>
                    </tr>
                    <tr>
                        <td>Median read quality</td>
                        <td>${formatQuality(stats.median_read_quality) || '-'}</td>
                    </tr>
                    <tr>
                        <td>Number of reads</td>
                        <td>${formatNumber(stats.number_of_reads) || '-'}</td>
                    </tr>
                    <tr>
                        <td>Read length N50</td>
                        <td>${formatLength(stats.read_length_n50) || '-'}</td>
                    </tr>
                    <tr>
                        <td>STDEV read length</td>
                        <td>${formatLength(stats.stdev_read_length) || '-'}</td>
                    </tr>
                    <tr>
                        <td>Total bases</td>
                        <td>${formatBases(stats.total_bases) || '-'}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Update nano stats display
 */
function updateNanoStats() {
    if (!currentSample) {
        clearNanoStats();
        return;
    }

    // Update unprocessed stats
    const unprocessed = currentSample.nano_stats_unprocessed;
    if (unprocessed) {
        updateStatsElement('unproc-reads', formatNumber(unprocessed.number_of_reads));
        updateStatsElement('unproc-length', formatLength(unprocessed.mean_read_length));
        updateStatsElement('unproc-quality', formatQuality(unprocessed.mean_read_quality));
        updateStatsElement('unproc-bases', formatBases(unprocessed.total_bases));
    } else {
        ['unproc-reads', 'unproc-length', 'unproc-quality', 'unproc-bases'].forEach(id => {
            updateStatsElement(id, '-');
        });
    }

    // Update processed stats
    const processed = currentSample.nano_stats_processed;
    if (processed) {
        updateStatsElement('proc-reads', formatNumber(processed.number_of_reads));
        updateStatsElement('proc-length', formatLength(processed.mean_read_length));
        updateStatsElement('proc-quality', formatQuality(processed.mean_read_quality));
        updateStatsElement('proc-bases', formatBases(processed.total_bases));
    } else {
        ['proc-reads', 'proc-length', 'proc-quality', 'proc-bases'].forEach(id => {
            updateStatsElement(id, '-');
        });
    }
}

/**
 * Update individual stats element
 */
function updateStatsElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value || '-';
    }
}

/**
 * Clear nano stats
 */
function clearNanoStats() {
    ['unproc-reads', 'unproc-length', 'unproc-quality', 'unproc-bases',
     'proc-reads', 'proc-length', 'proc-quality', 'proc-bases'].forEach(id => {
        updateStatsElement(id, '-');
    });
}

/**
 * Download plot
 */
function downloadPlot(processingType) {
    if (!currentSample || !currentPlotType) {
        alert('Please select a plot type first');
        return;
    }

    // Use structured nanoplot data to get the file path
    let filePath = null;
    
    if (currentSample.nanoplot && currentSample.nanoplot[processingType]) {
        const plotData = currentSample.nanoplot[processingType];
        
        // Map plot types to structured data fields
        switch (currentPlotType) {
            case 'length-quality-scatter':
                filePath = plotData.length_quality_scatter;
                break;
            case 'non-weighted-histogram':
                filePath = plotData.histogram_unweighted;
                break;
            case 'weighted-histogram':
                filePath = plotData.histogram_weighted;
                break;
            case 'yield-by-length':
                filePath = plotData.yield_by_length;
                break;
        }
    }
    
    if (filePath) {
        window.open(`/data/${filePath}`, '_blank');
    } else {
        alert(`No ${processingType} ${currentPlotType} data available for download`);
    }
}