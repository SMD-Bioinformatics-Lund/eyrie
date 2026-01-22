/**
 * Sequencing runs page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize table search using shared utility
    new TableSearch('tableSearch', 'seqrunsTableBody', {
        event: 'input'
    });
});
