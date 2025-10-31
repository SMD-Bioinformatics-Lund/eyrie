/**
 * Samples page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Setup search functionality for server-rendered table
    const searchInput = document.getElementById('tableSearch');
    searchInput.addEventListener('input', filterTable);
});


function filterTable() {
    const searchTerm = document.getElementById('tableSearch').value.toLowerCase();
    const tbody = document.getElementById('samplesTableBody');
    const rows = tbody.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let shouldShow = false;

        // Skip the loading/error rows
        if (cells.length === 1) continue;

        // Search through all text content in the row
        for (let j = 0; j < cells.length; j++) {
            const cellText = cells[j].textContent.toLowerCase();
            if (cellText.includes(searchTerm)) {
                shouldShow = true;
                break;
            }
        }

        row.style.display = shouldShow ? '' : 'none';
    }
}
