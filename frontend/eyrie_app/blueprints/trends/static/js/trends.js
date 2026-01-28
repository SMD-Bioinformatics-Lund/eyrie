/**
 * Trends Analysis JavaScript
 */

let currentTrendsData = null;

/**
 * Fetch and update trends chart asynchronously
 */
async function updateTrends() {
    const chartStatus = document.getElementById('chartStatus');
    chartStatus.textContent = 'Loading...';
    chartStatus.className = 'badge bg-warning text-dark';

    try {
        // Build query params from form elements
        const params = new URLSearchParams({
            category: document.getElementById('groupBySelect').value,
            metric: document.getElementById('metricSelect').value,
            time_range: 'all',
            group_by: 'exp_start_time',
            classification: document.getElementById('classificationFilter').value,
            sample_type: document.getElementById('sampleTypeFilter').value,
            qc: document.getElementById('qcFilter').value,
            read_quality_filtering: document.getElementById('readQualityFilteringSelect').value
        });

        const response = await fetch(`${window.TRENDS_API_URL}?${params}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        currentTrendsData = data;
        renderTrendsChart(data);

        chartStatus.textContent = 'Updated';
        chartStatus.className = 'badge bg-success text-white';
        setTimeout(() => {
            chartStatus.textContent = 'Ready';
            chartStatus.className = 'badge bg-light text-dark';
        }, 3000);

    } catch (error) {
        console.error('Error:', error);
        showErrorChart(error.message);
        chartStatus.textContent = 'Error';
        chartStatus.className = 'badge bg-danger text-white';
    }
}

/**
 * Render trends chart using Plotly (line charts only)
 */
function renderTrendsChart(data) {
    const chartDiv = document.getElementById('trendsChart');
    chartDiv.innerHTML = '';

    if (!data?.series?.length) {
        showEmptyChart();
        return;
    }

    const colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ];

    // Line chart only
    const traces = data.series.map((s, i) => ({
        x: s.dates,
        y: s.values,
        type: 'scatter',
        mode: 'lines+markers',
        name: s.name,
        line: { color: colors[i % colors.length], width: 2 },
        marker: { size: 6, color: colors[i % colors.length] },
        hovertemplate: `<b>${s.name}</b><br>` +
                      `Date: %{x}<br>` +
                      `${getMetricLabel()}: %{y}<br>` +
                      `<extra></extra>`
    }));

    const layout = {
        title: { text: `${getMetricLabel()} by ${getGroupByLabel()} over Time`, font: { size: 16 } },
        xaxis: { title: 'Experiment Start Time', type: 'date', showgrid: true },
        yaxis: { title: getMetricLabel(), showgrid: true },
        hovermode: 'x unified',
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 },
        margin: { l: 60, r: 40, t: 60, b: 80 },
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
            filename: `eyrie_trends_${new Date().toISOString().split('T')[0]}`,
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
                <small class="text-muted">Try adjusting the filters</small>
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
    window.location.href = window.location.pathname;
}

/**
 * Helper functions for labels
 */
function getGroupByLabel() {
    const select = document.getElementById('groupBySelect');
    return select?.options[select.selectedIndex]?.text || 'Category';
}

function getMetricLabel() {
    const select = document.getElementById('metricSelect');
    return select?.options[select.selectedIndex]?.text || 'Metric';
}
