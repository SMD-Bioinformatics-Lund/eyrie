/**
 * Trends Analysis JavaScript
 * Real-time plotting with Plotly.js
 */

// Debug logging
function debugLog(message, data = null) {
    console.log(`[Trends Debug] ${message}`, data || '');
}

let currentTrendsData = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Auto-suggest species frequency for stacked charts
    document.getElementById('chartTypeSelect').addEventListener('change', function() {
        const chartType = this.value;
        const metricSelect = document.getElementById('metricSelect');
        const categorySelect = document.getElementById('categorySelect');

        if (chartType === 'stacked_area' || chartType === 'bar') {
            // Auto-select species frequency and dominant species for composition analysis
            if (metricSelect.value !== 'species_frequency') {
                metricSelect.value = 'species_frequency';
            }
            if (categorySelect.value !== 'dominant_species') {
                categorySelect.value = 'dominant_species';
            }
        }
    });

    // Auto-suggest chart type for species frequency
    document.getElementById('metricSelect').addEventListener('change', function() {
        const metric = this.value;
        const chartTypeSelect = document.getElementById('chartTypeSelect');
        const categorySelect = document.getElementById('categorySelect');

        if (metric === 'species_frequency') {
            if (chartTypeSelect.value === 'line') {
                chartTypeSelect.value = 'stacked_area';
            }
            if (categorySelect.value !== 'dominant_species') {
                categorySelect.value = 'dominant_species';
            }
        }
    });
}

/**
 * Update trends chart based on current selections
 */
async function updateTrends() {
    const chartStatus = document.getElementById('chartStatus');
    chartStatus.textContent = 'Loading...';
    chartStatus.className = 'badge bg-warning text-dark';

    try {
        const category = document.getElementById('categorySelect').value;
        const metric = document.getElementById('metricSelect').value;
        const timeRange = document.getElementById('timeRangeSelect').value;
        const groupBy = document.getElementById('groupBySelect').value;
        const classificationFilter = document.getElementById('classificationFilter').value;

        // Build query parameters
        const sampleTypeFilter = document.getElementById('sampleTypeFilter').value;
        const tissueFilter = document.getElementById('tissueFilter').value;
        const extractionKitFilter = document.getElementById('extractionKitFilter').value;
        const libraryKitFilter = document.getElementById('libraryKitFilter').value;
        const dilutionFilter = document.getElementById('dilutionFilter').value;
        const spikeConcentrationFilter = document.getElementById('spikeConcentrationFilter').value;
        const qcFilter = document.getElementById('qcFilter').value;
        const readQualityFilteringFilter = document.getElementById('readQualityFilteringFilter').value;
        const genusFilter = document.getElementById('genusFilter').value;
        const chartType = document.getElementById('chartTypeSelect').value;

        const params = new URLSearchParams({
            category,
            metric,
            time_range: timeRange,
            group_by: groupBy,
            classification: classificationFilter,
            sample_type: sampleTypeFilter,
            tissue: tissueFilter,
            extraction_kit: extractionKitFilter,
            library_prep_kit: libraryKitFilter,
            dilution: dilutionFilter,
            spike_concentration: spikeConcentrationFilter,
            qc: qcFilter,
            read_quality_filtering: readQualityFilteringFilter,
            genus: genusFilter
        });

        // Fetch trends data using Flask route
        const trendsApiUrl = window.TRENDS_API_URL || '/api/trends/data';
        debugLog('Fetching trends data from:', `${trendsApiUrl}?${params}`);
        const response = await fetch(`${trendsApiUrl}?${params}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const trendsData = await response.json();
        debugLog('Received trends data:', trendsData);
        currentTrendsData = trendsData;

        // Auto-adjust chart type for insufficient data points
        let adjustedChartType = chartType;
        debugLog(`Chart type check: chartType=${chartType}, period_count=${trendsData.metadata?.period_count}, group_by=${groupBy}`);

        if (chartType === 'stacked_area' && trendsData.metadata && trendsData.metadata.period_count === 1) {
            adjustedChartType = 'bar';
            const chartTypeSelect = document.getElementById('chartTypeSelect');
            chartTypeSelect.value = 'bar';
            debugLog('Auto-switched from stacked area to bar chart due to single data point');
        } else if (chartType === 'stacked_area') {
            debugLog(`No auto-switch needed: period_count=${trendsData.metadata?.period_count}`);
        }

        // Render chart
        renderTrendsChart(trendsData, category, metric, groupBy, adjustedChartType);

        chartStatus.textContent = 'Updated';
        chartStatus.className = 'badge bg-success text-white';

        // Reset status after 3 seconds
        setTimeout(() => {
            chartStatus.textContent = 'Ready';
            chartStatus.className = 'badge bg-light text-dark';
        }, 3000);

    } catch (error) {
        console.error('Error updating trends:', error);
        showErrorChart(error.message);
        chartStatus.textContent = 'Error';
        chartStatus.className = 'badge bg-danger text-white';
    }
}

/**
 * Render trends chart using Plotly
 */
function renderTrendsChart(data, category, metric, groupBy, chartType = 'line') {
    const chartDiv = document.getElementById('trendsChart');

    // Clear any existing content (including placeholder)
    chartDiv.innerHTML = '';

    if (!data || !data.series || data.series.length === 0) {
        showEmptyChart();
        return;
    }

    const colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ];

    let traces;

    if (chartType === 'bar') {
        traces = data.series.map((series, index) => ({
            x: series.dates,
            y: series.values,
            type: 'bar',
            name: series.name,
            marker: {
                color: colors[index % colors.length]
            },
            hovertemplate: `<b>${series.name}</b><br>` +
                          `Date: %{x}<br>` +
                          `${getMetricLabel(metric)}: %{y}<br>` +
                          `<extra></extra>`
        }));
    } else if (chartType === 'stacked_area') {
        traces = data.series.map((series, index) => ({
            x: series.dates,
            y: series.values,
            type: 'scatter',
            mode: 'lines',
            name: series.name,
            fill: 'tonexty',
            fillcolor: colors[index % colors.length] + '40',
            line: {
                color: colors[index % colors.length],
                width: 1
            },
            hovertemplate: `<b>${series.name}</b><br>` +
                          `Date: %{x}<br>` +
                          `${getMetricLabel(metric)}: %{y}<br>` +
                          `<extra></extra>`
        }));

        // Set first trace to fill to zero
        if (traces.length > 0) {
            traces[0].fill = 'tozeroy';
        }
    } else {
        // Default line chart
        traces = data.series.map((series, index) => ({
            x: series.dates,
            y: series.values,
            type: 'scatter',
            mode: 'lines+markers',
            name: series.name,
            line: {
                color: colors[index % colors.length],
                width: 2
            },
            marker: {
                size: 6,
                color: colors[index % colors.length]
            },
            hovertemplate: `<b>${series.name}</b><br>` +
                          `Date: %{x}<br>` +
                          `${getMetricLabel(metric)}: %{y}<br>` +
                          `<extra></extra>`
        }));
    }

    const layout = {
        title: {
            text: `${getCategoryLabel(category)} vs ${getMetricLabel(metric)} (${getGroupByLabel(groupBy)})`,
            font: { size: 16 }
        },
        xaxis: {
            title: 'Date',
            type: 'date',
            showgrid: true
        },
        yaxis: {
            title: getMetricLabel(metric),
            showgrid: true
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: {
            l: 60,
            r: 40,
            t: 60,
            b: 80
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)'
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: `eyrie_trends_${category}_${metric}_${new Date().toISOString().split('T')[0]}`,
            height: 600,
            width: 1200,
            scale: 1
        }
    };

    Plotly.newPlot(chartDiv, traces, layout, config);
}

/**
 * Show empty chart message
 */
function showEmptyChart() {
    const chartDiv = document.getElementById('trendsChart');
    chartDiv.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center">
                <i class="bi bi-graph-down text-muted" style="font-size: 4rem;"></i>
                <p class="text-muted mt-3">No data available for the selected parameters</p>
                <small class="text-muted">Try adjusting the time range or filters</small>
            </div>
        </div>
    `;
}

/**
 * Show error message in chart area
 */
function showErrorChart(errorMessage) {
    const chartDiv = document.getElementById('trendsChart');
    chartDiv.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center">
                <i class="bi bi-exclamation-circle text-danger" style="font-size: 4rem;"></i>
                <p class="text-danger mt-3">Error loading trends data</p>
                <small class="text-muted">${errorMessage}</small>
            </div>
        </div>
    `;
}

/**
 * Export current chart
 */
function exportChart() {
    if (!currentTrendsData) {
        alert('No chart data to export. Please load a chart first.');
        return;
    }

    const chartDiv = document.getElementById('trendsChart');
    Plotly.downloadImage(chartDiv, {
        format: 'png',
        width: 1200,
        height: 600,
        filename: `eyrie_trends_${new Date().toISOString().split('T')[0]}`
    });
}

/**
 * Reset all filters to default values
 */
function resetFilters() {
    document.getElementById('categorySelect').value = 'sample_id';
    document.getElementById('metricSelect').value = 'number_of_reads';
    document.getElementById('timeRangeSelect').value = '30';
    document.getElementById('groupBySelect').value = 'week';
    document.getElementById('classificationFilter').value = 'all';
    document.getElementById('sampleTypeFilter').value = 'all';
    document.getElementById('tissueFilter').value = 'all';
    document.getElementById('extractionKitFilter').value = 'all';
    document.getElementById('libraryKitFilter').value = 'all';
    document.getElementById('dilutionFilter').value = 'all';
    document.getElementById('spikeConcentrationFilter').value = 'all';
    document.getElementById('qcFilter').value = 'all';
    document.getElementById('readQualityFilteringFilter').value = 'processed';
    document.getElementById('genusFilter').value = 'all';
    document.getElementById('chartTypeSelect').value = 'line';

    updateTrends();
}

/**
 * Helper functions for labels - simplified, now just extracting from DOM elements
 */
function getCategoryLabel(category) {
    const select = document.getElementById('categorySelect');
    const option = select.querySelector(`option[value="${category}"]`);
    return option ? option.textContent : category;
}

function getMetricLabel(metric) {
    const select = document.getElementById('metricSelect');
    const option = select.querySelector(`option[value="${metric}"]`);
    return option ? option.textContent : metric;
}

function getGroupByLabel(groupBy) {
    const select = document.getElementById('groupBySelect');
    const option = select.querySelector(`option[value="${groupBy}"]`);
    return option ? option.textContent : groupBy;
}
