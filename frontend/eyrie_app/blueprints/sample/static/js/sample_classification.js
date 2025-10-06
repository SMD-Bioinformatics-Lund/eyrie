/**
 * Classification-specific functionality
 */

// Global variables for classification
let flaggedContaminants = new Set();

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

    // Load saved contamination flags from database
    flaggedContaminants.clear();
    if (currentSample.flagged_contaminants) {
        currentSample.flagged_contaminants.forEach(species => {
            flaggedContaminants.add(species);
        });
    }
    
    const species = currentSample.taxonomic_data.hits.sort((a, b) => b.abundance - a.abundance);
    
    tbody.innerHTML = '';
    species.forEach((organism, index) => {
        const row = document.createElement('tr');
        row.className = 'contamination-row';
        row.dataset.species = organism.species;
        
        // Check if this species is flagged
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
                <button class="btn btn-sm ${isContaminant ? 'btn-danger' : 'btn-outline-secondary'} flag-btn" 
                        onclick="toggleContaminantFlag('${organism.species}', this)">
                    <i class="bi ${isContaminant ? 'bi-flag-fill' : 'bi-flag'}"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
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
 * Toggle contamination flag for a species
 */
function toggleContaminantFlag(species, button) {
    if (flaggedContaminants.has(species)) {
        flaggedContaminants.delete(species);
        button.className = 'btn btn-sm btn-outline-secondary flag-btn';
        button.innerHTML = '<i class="bi bi-flag"></i>';
    } else {
        flaggedContaminants.add(species);
        button.className = 'btn btn-sm btn-danger flag-btn';
        button.innerHTML = '<i class="bi bi-flag-fill"></i>';
    }
    updateSampleClassificationSummary();
    saveContaminationFlags();
}

/**
 * Save contamination flags to the database
 */
async function saveContaminationFlags() {
    if (!currentSample) {
        return;
    }
    
    try {
        const response = await fetch(`${window.API_BASE}/samples/${currentSample.sample_id}/contamination`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                flagged_species: Array.from(flaggedContaminants)
            })
        });
        
        if (response.ok) {
            // Update the current sample data to reflect the saved flags
            currentSample.flagged_contaminants = Array.from(flaggedContaminants);
        }
    } catch (error) {
        // Silent error handling - could be enhanced with user feedback
        console.error('Error saving contamination flags:', error);
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