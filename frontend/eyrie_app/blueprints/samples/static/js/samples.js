/**
 * Samples page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('#samplesTableBody [data-bs-toggle="tooltip"]').forEach(function(element) {
        new bootstrap.Tooltip(element, {customClass: 'list-tooltip', animation: false});
    });
});
