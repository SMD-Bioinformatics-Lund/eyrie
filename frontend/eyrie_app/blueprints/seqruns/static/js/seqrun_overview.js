/**
 * Seqrun overview page JavaScript
 * Table search functionality for samples in run
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize table search for samples in run
    new TableSearch('runSamplesSearch', 'runSamplesTableBody');
});
