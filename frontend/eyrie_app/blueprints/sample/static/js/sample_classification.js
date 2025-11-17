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
}

/**
 * Load classification data for the sample
 */
function loadClassificationData(sample = currentSample) {
    if (!sample) return;

    // Initialize flags from loaded sample data
    initializeFlagsFromSample(sample);
    // Setup flag button event listeners for server-rendered table
    setupFlagButtonEventListeners();
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
 * Set up event listeners for flag buttons using event delegation
 */
function setupFlagButtonEventListeners() {
    const tbody = document.getElementById('contaminationTableBody');
    if (!tbody) return;

    // Remove existing listeners first
    tbody.removeEventListener('click', handleFlagButtonClick);

    // Add new listener
    tbody.addEventListener('click', handleFlagButtonClick);
}

/**
 * Handle flag button clicks
 */
function handleFlagButtonClick(event) {
    const button = event.target.closest('button[data-flag-type]');
    if (!button) return;

    event.preventDefault();
    event.stopPropagation();

    const species = button.dataset.species;
    const flagType = button.dataset.flagType;

    console.log('Flag button clicked:', { species, flagType });

    if (flagType === 'top-hit') {
        toggleTopHitFlag(species, button);
    } else if (flagType === 'contaminant') {
        toggleContaminantFlag(species, button);
    }
}


/**
 * Toggle top hit flag for a species
 */
function toggleTopHitFlag(species, button) {
    console.log('toggleTopHitFlag called with species:', species);
    if (flaggedTopHits.has(species)) {
        flaggedTopHits.delete(species);
        button.className = 'btn btn-sm btn-outline-success top-hit-btn';
        button.innerHTML = '<i class="bi bi-star"></i>';
        console.log('Removed from flaggedTopHits:', species);
    } else {
        flaggedTopHits.add(species);
        button.className = 'btn btn-sm btn-success top-hit-btn';
        button.innerHTML = '<i class="bi bi-star-fill"></i>';
        console.log('Added to flaggedTopHits:', species);
    }
    console.log('Current flaggedTopHits:', Array.from(flaggedTopHits));

    // Update the current sample object to reflect changes
    if (currentSample) {
        currentSample.flagged_top_hits = Array.from(flaggedTopHits);
    }

    updateSampleClassificationSummary();
    saveSpeciesFlags();

    // Update overview classification summary if function exists
    if (typeof renderOverviewClassificationSummary === 'function') {
        renderOverviewClassificationSummary();
    }
}

/**
 * Toggle contamination flag for a species
 */
function toggleContaminantFlag(species, button) {
    console.log('toggleContaminantFlag called with species:', species);
    if (flaggedContaminants.has(species)) {
        flaggedContaminants.delete(species);
        button.className = 'btn btn-sm btn-outline-danger contaminant-btn';
        button.innerHTML = '<i class="bi bi-flag"></i>';
        console.log('Removed from flaggedContaminants:', species);
    } else {
        flaggedContaminants.add(species);
        button.className = 'btn btn-sm btn-danger contaminant-btn';
        button.innerHTML = '<i class="bi bi-flag-fill"></i>';
        console.log('Added to flaggedContaminants:', species);
    }
    console.log('Current flaggedContaminants:', Array.from(flaggedContaminants));

    // Update the current sample object to reflect changes
    if (currentSample) {
        currentSample.flagged_contaminants = Array.from(flaggedContaminants);
    }

    updateSampleClassificationSummary();
    saveSpeciesFlags();

    // Update overview classification summary if function exists
    if (typeof renderOverviewClassificationSummary === 'function') {
        renderOverviewClassificationSummary();
    }
}

/**
 * Save species flags to the database
 */
async function saveSpeciesFlags() {
    if (!currentSample) {
        console.error('No current sample available for saving flags');
        return;
    }

    const url = getSampleApiUrl('speciesFlags', currentSample.sample_id);
    if (!url) {
        showError('Species flags API URL not available');
        return;
    }

    const payload = {
        flagged_contaminants: Array.from(flaggedContaminants),
        flagged_top_hits: Array.from(flaggedTopHits)
    };

    console.log('🔍 Species flags URL:', url);
    console.log('🔍 Species flags payload:', payload);

    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Flags saved successfully:', result);
            // Update the current sample data to reflect the saved flags
            currentSample.flagged_contaminants = Array.from(flaggedContaminants);
            currentSample.flagged_top_hits = Array.from(flaggedTopHits);
        } else {
            console.error('Failed to save flags. Status:', response.status);
            const errorText = await response.text();
            console.error('Error response:', errorText);
        }
    } catch (error) {
        console.error('Error saving species flags:', error);
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

    const data = currentSample.taxonomic_data.hits || [];
    const csvContent = "data:text/csv;charset=utf-8,"
        + "Species,Genus,Family,Abundance,Flagged\\n"
        + data.map(sp =>
            `"${sp.species}","${sp.genus || 'N/A'}","${sp.family || 'N/A'}",${sp.abundance},${flaggedContaminants.has(sp.species) ? 'Yes' : 'No'}`
        ).join("\\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${currentSample.sample_id}_abundance_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
