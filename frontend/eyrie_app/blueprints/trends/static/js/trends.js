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
    // Don't auto-load trends - wait for user to click Update Chart button
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // No automatic updates - user must click the Update Chart button
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
        const params = new URLSearchParams({
            category,
            metric,
            time_range: timeRange,
            group_by: groupBy,
            classification: classificationFilter
        });

        // Fetch trends data using backend API (routed through Flask frontend)
        const trendsApiUrl = `${window.API_BASE}/trends/data`;
        debugLog('Fetching trends data from:', `${trendsApiUrl}?${params}`);
        const response = await fetch(`${trendsApiUrl}?${params}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const trendsData = await response.json();
        debugLog('Received trends data:', trendsData);
        currentTrendsData = trendsData;

        // Render chart
        renderTrendsChart(trendsData, category, metric, groupBy);

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
function renderTrendsChart(data, category, metric, groupBy) {
    const chartDiv = document.getElementById('trendsChart');

    // Clear any existing content (including placeholder)
    chartDiv.innerHTML = '';

    if (!data || !data.series || data.series.length === 0) {
        showEmptyChart();
        return;
    }

    const traces = data.series.map((series, index) => {
        const colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ];

        return {
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
        };
    });

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
    document.getElementById('categorySelect').value = 'tissue_sample_type';
    document.getElementById('metricSelect').value = 'number_of_reads';
    document.getElementById('timeRangeSelect').value = '30';
    document.getElementById('groupBySelect').value = 'week';
    document.getElementById('classificationFilter').value = 'all';

    updateTrends();
}


/**
 * Helper functions for labels
 */
function getCategoryLabel(category) {
    const labels = {
        'tissue_sample_type': 'Tissue Sample Type',
        'true_hits': 'True Hits',
        'spike_species': 'Spike Species',
        'classification_type': 'Classification Type'
    };
    return labels[category] || category;
}

function getMetricLabel(metric) {
    const labels = {
        'number_of_reads': 'Number of Reads',
        'mean_read_length': 'Mean Read Length (bp)',
        'mean_read_quality': 'Mean Read Quality (Q-score)',
        'contaminants_count': 'Contaminants Count',
        'top_hits_count': 'Top Hits Count',
        'qc_pass_rate': 'QC Pass Rate (%)',
        'total_bases': 'Total Bases',
        'read_length_n50': 'Read Length N50 (bp)'
    };
    return labels[metric] || metric;
}

function getGroupByLabel(groupBy) {
    const labels = {
        'day': 'Daily',
        'week': 'Weekly',
        'month': 'Monthly'
    };
    return labels[groupBy] || groupBy;
}
