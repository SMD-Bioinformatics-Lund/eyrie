/**
 * QC Plots JavaScript
 * Handles Plotly chart initialization for QC analysis plots
 */

// Function to initialize read quality plot when visible
function initializeReadQualityPlot() {
    try {
        const plotConfigElement = document.getElementById('read-quality-plot-config');
        const plotElement = document.getElementById('read-quality-plot');

        if (plotConfigElement && plotElement && plotElement.offsetParent !== null) {
            const plotConfig = JSON.parse(plotConfigElement.textContent);

            // Get sequencing run ID from data attribute or fallback to 'unknown'
            const sequencingRunId = plotElement.dataset.sequencingRunId || 'unknown';

            // Add export configuration for read quality plot
            const exportConfig = {
                ...plotConfig.config,
                toImageButtonOptions: {
                    format: 'png',
                    filename: `eyrie_qc_read_quality_${sequencingRunId}_${new Date().toISOString().split('T')[0]}`,
                    height: 600,
                    width: 1000,
                    scale: 2
                }
            };

            Plotly.newPlot('read-quality-plot', plotConfig.data, plotConfig.layout, exportConfig);
            return true; // Successfully initialized
        }
        return false; // Not ready yet
    } catch (error) {
        console.error('Error loading read quality plot:', error);
        const plotElement = document.getElementById('read-quality-plot');
        if (plotElement) {
            plotElement.innerHTML = '<div class="alert alert-danger">Error loading read quality analysis plot</div>';
        }
        return true; // Don't retry on error
    }
}

// Store the initialization functions globally for the main QC page to call
window.initReadQualityPlot = initializeReadQualityPlot;

// Function to initialize contamination stacked bar plot when visible
function initializeContaminationPlot() {
    try {
        const configElement = document.getElementById('contamination-plot-config');
        const plotElement = document.getElementById('contamination-plot');

        if (configElement && plotElement && plotElement.offsetParent !== null) {
            const plotConfig = JSON.parse(configElement.textContent);
            const seqrunId = plotElement.dataset.sequencingRunId || 'unknown';
            const exportConfig = {
                ...plotConfig.config,
                toImageButtonOptions: {
                    format: 'png',
                    filename: `eyrie_contamination_${seqrunId}_${new Date().toISOString().split('T')[0]}`,
                    height: 600,
                    width: 1200,
                    scale: 2,
                },
            };
            Plotly.newPlot('contamination-plot', plotConfig.data, plotConfig.layout, exportConfig);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error loading contamination plot:', error);
        const el = document.getElementById('contamination-plot');
        if (el) el.innerHTML = '<div class="alert alert-danger">Error loading contamination plot</div>';
        return true;
    }
}

window.initContaminationPlot = initializeContaminationPlot;
