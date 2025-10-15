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
    loadSample(sampleId).then(sample => {
        if (sample) {
            updateSampleTitle(sample);
            loadClassificationData(sample);
        }
    });
}

/**
 * Load classification data for the sample
 */
function loadClassificationData(sample = currentSample) {
    if (!sample) return;
    
    // Load Krona plot in classification view
    if (sample.krona_file) {
        const frame = document.getElementById('classificationKronaFrame');
        if (frame) {
            frame.src = `/data/${sample.krona_file}`;
            frame.style.width = '100%';
            frame.style.height = '600px';
            frame.style.border = 'none';
        }
    } else {
        const frame = document.getElementById('classificationKronaFrame');
        if (frame) {
            frame.srcdoc = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #6c757d;"><i>No Krona plot available</i></div>';
        }
    }
    
    // Load abundance table and classification summary
    displaySampleAbundanceTable();
    updateSampleClassificationSummary();
}

/**
 * Display sample abundance table
 */
function displaySampleAbundanceTable() {
    const tbody = document.getElementById('contaminationTableBody');
    if (!tbody) return;
    
    if (!currentSample || !currentSample.taxonomic_data || !currentSample.taxonomic_data.hits) {
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

    // Load saved flags from database
    flaggedContaminants.clear();
    flaggedTopHits.clear();
    
    if (currentSample.flagged_contaminants) {
        currentSample.flagged_contaminants.forEach(species => {
            flaggedContaminants.add(species);
        });
    }
    
    if (currentSample.flagged_top_hits) {
        currentSample.flagged_top_hits.forEach(species => {
            flaggedTopHits.add(species);
        });
    }
    
    const species = currentSample.taxonomic_data.hits.sort((a, b) => b.abundance - a.abundance);
    
    tbody.innerHTML = '';
    species.forEach((organism, index) => {
        const row = document.createElement('tr');
        row.className = 'contamination-row';
        row.dataset.species = organism.species;
        
        // Check if this species is flagged
        const isTopHit = flaggedTopHits.has(organism.species);
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
                <button class="btn btn-sm ${isTopHit ? 'btn-success' : 'btn-outline-success'} top-hit-btn" 
                        data-species="${organism.species}" 
                        data-flag-type="top-hit">
                    <i class="bi ${isTopHit ? 'bi-star-fill' : 'bi-star'}"></i>
                </button>
            </td>
            <td>
                <button class="btn btn-sm ${isContaminant ? 'btn-danger' : 'btn-outline-danger'} contaminant-btn" 
                        data-species="${organism.species}" 
                        data-flag-type="contaminant">
                    <i class="bi ${isContaminant ? 'bi-flag-fill' : 'bi-flag'}"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Set up event delegation for flag buttons
    setupFlagButtonEventListeners();
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
 * Get abundance badge class for styling
 */
function getAbundanceBadgeClass(abundance) {
    if (abundance >= 10) return 'bg-success';
    if (abundance >= 5) return 'bg-warning';
    if (abundance >= 1) return 'bg-info';
    return 'bg-secondary';
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
    
    const apiBase = window.API_BASE || '/api';
    const url = `${apiBase}/samples/${currentSample.sample_id}/species-flags`;
    const payload = {
        flagged_contaminants: Array.from(flaggedContaminants),
        flagged_top_hits: Array.from(flaggedTopHits)
    };
    
    console.log('Saving species flags:', payload);
    console.log('API URL:', url);
    
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
    
    if (data.hits && data.hits.length > 0) {
        const dominant = data.hits.reduce((prev, current) => 
            (prev.abundance > current.abundance) ? prev : current
        );
        const dominantSpeciesEl = document.getElementById('dominantSpecies');
        if (dominantSpeciesEl) {
            dominantSpeciesEl.textContent = dominant.species;
        }
    } else {
        const dominantSpeciesEl = document.getElementById('dominantSpecies');
        if (dominantSpeciesEl) {
            dominantSpeciesEl.textContent = '-';
        }
    }
    
    const flaggedContaminantsEl = document.getElementById('flaggedContaminants');
    if (flaggedContaminantsEl) {
        flaggedContaminantsEl.textContent = flaggedContaminants.size;
    }
    
    const flaggedTopHitsEl = document.getElementById('flaggedTopHits');
    if (flaggedTopHitsEl) {
        flaggedTopHitsEl.textContent = flaggedTopHits.size;
    }
    
    const diversity = calculateShannonDiversity(data.hits || []);
    const diversityIndexEl = document.getElementById('diversityIndex');
    if (diversityIndexEl) {
        diversityIndexEl.textContent = diversity.toFixed(2);
    }
}

/**
 * Calculate Shannon diversity index
 */
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

/**
 * Refresh Krona plot
 */
function refreshKronaPlot() {
    if (currentSample && currentSample.krona_file) {
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
    if (currentSample && currentSample.krona_file) {
        window.open(`/data/${currentSample.krona_file}`, '_blank');
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