/**
 * Nanoplot-specific functionality
 */

// Helper function to generate data URLs using Flask data file serving
function getDataUrl(filePath) {
    // Use the global function provided by sample_base.html template
    return window.getDataFileUrl ? window.getDataFileUrl(filePath) : `/analysis-files/${filePath}`;
}

// Global variables for nanoplot
let currentPlotType = null;

/**
 * Initialize nanoplot view
 */
function initializeNanoplotView(sampleId) {
    if (currentSample) {
        updateNanoStats();
    }
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

    // Switch card header buttons to info/tooltip mode
    updateHeaderButton('unprocessed', 'plot');
    updateHeaderButton('processed', 'plot');
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

    // Switch card header buttons to download mode
    updateHeaderButton('unprocessed', 'summary');
    updateHeaderButton('processed', 'summary');
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

    if (currentSample.nanoplot && currentSample.nanoplot[processingType] && currentSample.nanoplot[processingType].files) {
        const plotFiles = currentSample.nanoplot[processingType].files;

        // Map plot types to structured data fields
        switch (plotType) {
            case 'length-quality-scatter':
                filePath = plotFiles.length_quality_scatter;
                break;
            case 'non-weighted-histogram':
                filePath = plotFiles.histogram_unweighted;
                break;
            case 'weighted-histogram':
                filePath = plotFiles.histogram_weighted;
                break;
            case 'yield-by-length':
                filePath = plotFiles.yield_by_length;
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
        const response = await fetch(getDataUrl(filePath), { method: 'HEAD' });

        if (response.ok) {
            if (filePath.endsWith('.html')) {
                container.innerHTML = `
                    <iframe src="${getDataUrl(filePath)}"
                            class="w-100 h-100"
                            style="min-height: 500px; border: none;">
                    </iframe>
                `;
            } else if (filePath.endsWith('.png') || filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) {
                container.innerHTML = `
                    <div class="text-center p-3">
                        <img src="${getDataUrl(filePath)}"
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
                            <a href="${getDataUrl(filePath)}" class="btn btn-primary" target="_blank">
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
        (currentSample.nanoplot?.unprocessed?.nanostats) :
        (currentSample.nanoplot?.processed?.nanostats);

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
                    <tr${(stats.number_of_reads != null && stats.number_of_reads < 500) ? ' class="table-danger"' : ''}>
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
    const unprocessed = currentSample.nanoplot?.unprocessed?.nanostats;
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
    const processed = currentSample.nanoplot?.processed?.nanostats;
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
 * Download NanoStats as CSV.
 * When processingType is 'unprocessed' or 'processed', downloads only that panel's stats.
 * When called with no argument, downloads both columns combined.
 */
function downloadStatsCSV(processingType) {
    if (!currentSample) return;

    const unproc = currentSample.nanoplot?.unprocessed?.nanostats || {};
    const proc   = currentSample.nanoplot?.processed?.nanostats   || {};

    const metrics = [
        ['mean_read_length',   'Mean read length'],
        ['mean_read_quality',  'Mean read quality'],
        ['median_read_length', 'Median read length'],
        ['median_read_quality','Median read quality'],
        ['number_of_reads',    'Number of reads'],
        ['read_length_n50',    'Read length N50'],
        ['stdev_read_length',  'STDEV read length'],
        ['total_bases',        'Total bases'],
    ];

    let rows, filename;
    if (processingType === 'unprocessed') {
        rows = [['Metric', 'Unprocessed'], ...metrics.map(([k, l]) => [l, unproc[k] ?? ''])];
        filename = `${currentSample.sample_id || 'sample'}_nanostats_unprocessed.csv`;
    } else if (processingType === 'processed') {
        rows = [['Metric', 'Processed'], ...metrics.map(([k, l]) => [l, proc[k] ?? ''])];
        filename = `${currentSample.sample_id || 'sample'}_nanostats_processed.csv`;
    } else {
        rows = [['Metric', 'Unprocessed', 'Processed'],
                ...metrics.map(([k, l]) => [l, unproc[k] ?? '', proc[k] ?? ''])];
        filename = `${currentSample.sample_id || 'sample'}_nanostats.csv`;
    }

    const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Update a card header button based on the current display mode.
 * mode === 'summary'  → download icon, triggers CSV download for that panel
 * mode === 'plot'     → info icon, tooltip about Plotly camera
 */
function updateHeaderButton(processingType, mode) {
    const btn = document.getElementById(`${processingType}-header-btn`);
    if (!btn) return;
    const existing = bootstrap.Tooltip.getInstance(btn);
    if (existing) existing.dispose();
    if (mode === 'summary') {
        btn.removeAttribute('data-bs-toggle');
        btn.removeAttribute('title');
        btn.innerHTML = '<i class="bi bi-download"></i>';
        btn.onclick = () => downloadStatsCSV(processingType);
        btn.style.cursor = 'pointer';
    } else {
        btn.setAttribute('data-bs-toggle', 'tooltip');
        btn.setAttribute('title', 'To download, hover over the chart and click the camera icon (📷) in the Plotly toolbar');
        btn.innerHTML = '<i class="bi bi-info-circle"></i>';
        btn.onclick = null;
        btn.style.cursor = 'default';
        new bootstrap.Tooltip(btn, { delay: 0, animation: false });
    }
}

