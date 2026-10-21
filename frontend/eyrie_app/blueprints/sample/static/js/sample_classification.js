/**
 * Classification-specific functionality
 */

// Global variables for classification
let flaggedContaminants = new Set();
let flaggedTopHits = new Set();

/**
 * Initialize classification view
 */
function initializeClassificationView(sampleId) {
    if (currentSample) {
        loadClassificationData(currentSample);
    }
    // Initialise Bootstrap tooltips for this view (e.g. Krona info button)
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function(el) {
        if (!bootstrap.Tooltip.getInstance(el)) {
            new bootstrap.Tooltip(el, { delay: 0, animation: false });
        }
    });
}

/**
 * Load classification data for the sample
 */
function loadClassificationData(sample = currentSample) {
    if (!sample) return;

    // Initialize flags from loaded sample data
    initializeFlagsFromSample(sample);
    // Update classification summary
    updateSampleClassificationSummary();
}

/**
 * Initialize flags from sample data - for server-rendered table
 */
function initializeFlagsFromSample(sample) {
    // Load saved flags from sample data
    flaggedContaminants.clear();
    flaggedTopHits.clear();

    if (sample && sample.flagged_contaminants) {
        sample.flagged_contaminants.forEach(species => {
            flaggedContaminants.add(species);
        });
    }

    if (sample && sample.flagged_top_hits) {
        sample.flagged_top_hits.forEach(species => {
            flaggedTopHits.add(species);
        });
    }
}

/**
 * Update classification summary display
 */
function updateSampleClassificationSummary() {
    if (!currentSample || !currentSample.taxonomic_data) {
        const totalSpeciesEl = document.getElementById('totalSpecies');
        const dominantSpeciesEl = document.getElementById('dominantSpecies');
        const flaggedContaminantsEl = document.getElementById('flaggedContaminants');
        const diversityIndexEl = document.getElementById('diversityIndex');

        if (totalSpeciesEl) totalSpeciesEl.textContent = '0';
        if (dominantSpeciesEl) dominantSpeciesEl.textContent = '-';
        if (flaggedContaminantsEl) flaggedContaminantsEl.textContent = '0';
        if (diversityIndexEl) diversityIndexEl.textContent = '0.0';
        return;
    }

    const data = currentSample.taxonomic_data;

    const totalSpeciesEl = document.getElementById('totalSpecies');
    if (totalSpeciesEl) {
        totalSpeciesEl.textContent = data.total_species || 0;
    }

    // Calculate dominant species from hits data
    const dominantSpeciesEl = document.getElementById('dominantSpecies');
    if (dominantSpeciesEl) {
        let dominantSpecies = '-';
        if (data.hits && data.hits.length > 0) {
            // Find species with highest abundance
            const dominant = data.hits.reduce((max, hit) => 
                hit.abundance > max.abundance ? hit : max, data.hits[0]);
            dominantSpecies = dominant.species || '-';
        }
        dominantSpeciesEl.textContent = dominantSpecies;
    }

    const flaggedContaminantsEl = document.getElementById('flaggedContaminants');
    if (flaggedContaminantsEl) {
        flaggedContaminantsEl.textContent = flaggedContaminants.size;
    }

    const flaggedTopHitsEl = document.getElementById('flaggedTopHits');
    if (flaggedTopHitsEl) {
        flaggedTopHitsEl.textContent = flaggedTopHits.size;
    }

    // Calculate Shannon diversity from hits data
    const diversityIndexEl = document.getElementById('diversityIndex');
    if (diversityIndexEl) {
        let diversity = 0.0;
        if (data.hits && data.hits.length > 0) {
            // Calculate Shannon diversity index
            const total = data.hits.reduce((sum, hit) => sum + hit.abundance, 0);
            if (total > 0) {
                diversity = data.hits.reduce((shannon, hit) => {
                    if (hit.abundance > 0) {
                        const proportion = hit.abundance / total;
                        return shannon - (proportion * Math.log(proportion));
                    }
                    return shannon;
                }, 0);
            }
        }
        diversityIndexEl.textContent = diversity.toFixed(2);
    }

    // Update spike species
    const spikeEl = document.getElementById('spike');
    if (spikeEl) {
        if (currentSample.spike) {
            spikeEl.textContent = currentSample.spike;
        } else {
            spikeEl.textContent = '-';
        }
    }
}


/**
 * Refresh Krona plot
 */
function refreshKronaPlot() {
    if (currentSample && currentSample.files?.krona) {
        const frame = document.getElementById('classificationKronaFrame');
        if (frame) {
            frame.src = frame.src; // Reload the iframe
        }
    }
}

/**
 * Download Krona plot
 */
function downloadKronaPlot() {
    if (currentSample && currentSample.files?.krona) {
        // Use Flask data file serving route
        window.open(getDataFileUrl(currentSample.files.krona), '_blank');
    } else {
        alert('No Krona plot available for download');
    }
}

/**
 * Export contamination data as CSV
 */
function exportContaminationData() {
    if (!currentSample || !currentSample.taxonomic_data) {
        alert('No data available for export');
        return;
    }

    const hits = currentSample.taxonomic_data.hits || [];
    const rows = [
        ['Species', 'Genus', 'Family', 'Abundance (%)', 'Estimated Counts',
         'Top Hit', 'Contaminant'],
        ...hits.map(sp => [
            sp.species,
            sp.genus  || 'N/A',
            sp.family || 'N/A',
            sp.abundance,
            sp.estimated_counts ?? '',
            flaggedTopHits.has(sp.species)      ? 'Yes' : 'No',
            flaggedContaminants.has(sp.species) ? 'Yes' : 'No',
        ]),
    ];

    const csv = rows.map(r => r.map(safeCSVValue).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    try {
        const a = document.createElement('a');
        a.href = url;
        a.download = sanitizeFilename(
            `${currentSample.sample_id || 'sample'}_abundance_data.csv`
        );
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } finally {
        URL.revokeObjectURL(url);
    }
}
