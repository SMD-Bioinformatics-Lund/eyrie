// Classification view JavaScript functionality

let samples = [];
let currentSample = null;
let flaggedContaminants = new Set();

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadSamples();
    loadCurrentUser();
    setupEventListeners();
});

function setupEventListeners() {
    // Sample selection
    document.getElementById('sampleSelect').addEventListener('change', function() {
        const sampleId = this.value;
        if (sampleId) {
            loadSampleData(sampleId);
        } else {
            clearViews();
        }
    });

    // Sample search
    document.getElementById('sampleSearch').addEventListener('input', function() {
        filterSamples(this.value);
    });
}

async function loadSamples() {
    try {
        const response = await fetch(`${window.API_BASE}/samples`);
        if (response.ok) {
            samples = await response.json();
            populateSampleSelect();
        } else {
            console.error('Failed to load samples');
        }
    } catch (error) {
        console.error('Error loading samples:', error);
    }
}

function populateSampleSelect() {
    const select = document.getElementById('sampleSelect');
    select.innerHTML = '<option value="">Select a sample...</option>';
    
    samples.forEach(sample => {
        const option = document.createElement('option');
        option.value = sample.sample_id;
        option.textContent = `${sample.sample_name} (${sample.sample_id})`;
        select.appendChild(option);
    });
}

function filterSamples(searchTerm) {
    const select = document.getElementById('sampleSelect');
    const options = select.querySelectorAll('option');
    
    options.forEach(option => {
        if (option.value === '') return; // Skip the default option
        
        const text = option.textContent.toLowerCase();
        const matches = text.includes(searchTerm.toLowerCase());
        option.style.display = matches ? '' : 'none';
    });
}

async function loadSampleData(sampleId) {
    try {
        const response = await fetch(`${window.API_BASE}/samples/${sampleId}`);
        if (response.ok) {
            currentSample = await response.json();
            displayKronaPlot();
            displayAbundanceTable();
            updateSummaryStats();
        } else {
            console.error('Failed to load sample data');
        }
    } catch (error) {
        console.error('Error loading sample data:', error);
    }
}

function displayKronaPlot() {
    const container = document.getElementById('kronaPlotContainer');
    
    if (currentSample && currentSample.krona_file) {
        // Display Krona plot in iframe
        container.innerHTML = `
            <iframe src="/data/${currentSample.krona_file}" 
                    class="w-100 h-100" 
                    style="min-height: 600px; border: none;">
            </iframe>
        `;
    } else {
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="text-center">
                    <i class="bi bi-exclamation-circle text-warning" style="font-size: 4rem;"></i>
                    <p class="text-muted mt-3">No Krona plot available for this sample</p>
                </div>
            </div>
        `;
    }
}

function displayAbundanceTable() {
    const tbody = document.getElementById('contaminationTableBody');
    
    if (!currentSample || !currentSample.taxonomic_data || !currentSample.taxonomic_data.top_species) {
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

    // Clear existing flagged contaminants for new sample
    flaggedContaminants.clear();

    // Sort species by abundance (descending)
    const species = currentSample.taxonomic_data.top_species.sort((a, b) => b.abundance - a.abundance);
    
    tbody.innerHTML = '';
    species.forEach((organism, index) => {
        const row = document.createElement('tr');
        row.className = 'contamination-row';
        row.dataset.species = organism.species;
        
        // Determine if this should be pre-flagged based on sample data
        const isContaminant = currentSample.taxonomic_data.contaminants_detected > 0 && 
                             organism.abundance < 1.0; // Example logic
        
        if (isContaminant) {
            flaggedContaminants.add(organism.species);
        }
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <small class="text-muted me-2">${index + 1}.</small>
                    <div>
                        <div class="fw-semibold">${organism.species}</div>
                        <small class="text-muted">${organism.genus} - ${organism.family}</small>
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

function getAbundanceBadgeClass(abundance) {
    if (abundance >= 10) return 'bg-success';
    if (abundance >= 5) return 'bg-warning';
    if (abundance >= 1) return 'bg-info';
    return 'bg-secondary';
}

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
    
    updateSummaryStats();
}

function updateSummaryStats() {
    if (!currentSample || !currentSample.taxonomic_data) {
        document.getElementById('totalSpecies').textContent = '0';
        document.getElementById('dominantSpecies').textContent = '-';
        document.getElementById('flaggedContaminants').textContent = '0';
        document.getElementById('diversityIndex').textContent = '0.0';
        return;
    }

    const data = currentSample.taxonomic_data;
    
    // Total species
    document.getElementById('totalSpecies').textContent = data.total_species || 0;
    
    // Dominant species
    if (data.top_species && data.top_species.length > 0) {
        const dominant = data.top_species.reduce((prev, current) => 
            (prev.abundance > current.abundance) ? prev : current
        );
        document.getElementById('dominantSpecies').textContent = dominant.species;
    } else {
        document.getElementById('dominantSpecies').textContent = '-';
    }
    
    // Flagged contaminants
    document.getElementById('flaggedContaminants').textContent = flaggedContaminants.size;
    
    // Calculate Shannon diversity index
    const diversity = calculateShannonDiversity(data.top_species || []);
    document.getElementById('diversityIndex').textContent = diversity.toFixed(2);
}

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

function clearViews() {
    currentSample = null;
    flaggedContaminants.clear();
    
    document.getElementById('kronaPlotContainer').innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center">
                <i class="bi bi-pie-chart text-muted" style="font-size: 4rem;"></i>
                <p class="text-muted mt-3">Select a sample to view taxonomic classification</p>
            </div>
        </div>
    `;
    
    document.getElementById('contaminationTableBody').innerHTML = `
        <tr>
            <td colspan="3" class="text-center py-4">
                <div class="text-muted">
                    <i class="bi bi-table text-muted" style="font-size: 2rem;"></i>
                    <p class="mt-2">Select a sample to view abundance data</p>
                </div>
            </td>
        </tr>
    `;
    
    updateSummaryStats();
}

// Action functions
function refreshKronaPlot() {
    if (currentSample) {
        displayKronaPlot();
    }
}

function downloadKronaPlot() {
    if (currentSample && currentSample.krona_file) {
        window.open(`/data/${currentSample.krona_file}`, '_blank');
    } else {
        alert('No Krona plot available for download');
    }
}

function exportContaminationData() {
    if (!currentSample || !currentSample.taxonomic_data) {
        alert('No data available for export');
        return;
    }

    const data = currentSample.taxonomic_data.top_species || [];
    const csvContent = "data:text/csv;charset=utf-8," 
        + "Species,Genus,Family,Abundance,Flagged\n"
        + data.map(sp => 
            `"${sp.species}","${sp.genus}","${sp.family}",${sp.abundance},${flaggedContaminants.has(sp.species) ? 'Yes' : 'No'}`
        ).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${currentSample.sample_id}_abundance_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// User management functions (shared across views)
async function loadCurrentUser() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/current-user`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('currentUsername').textContent = user.username;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading current user:', error);
        window.location.href = '/login';
    }
}

async function logout() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error during logout:', error);
        window.location.href = '/login';
    }
}
