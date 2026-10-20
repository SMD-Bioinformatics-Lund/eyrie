/**
 * Samples page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('samplesTableBody').addEventListener('change', updateSelectedCount);
    document.querySelectorAll('#samplesTableBody [data-bs-toggle="tooltip"]').forEach(function(element) {
        new bootstrap.Tooltip(element, {customClass: 'list-tooltip', animation: false});
    });
});


function updateSelectedCount() {
    const checked = document.querySelectorAll('input[name="sample_ids"]:checked').length;
    document.getElementById('selectedCount').textContent = checked;
}
