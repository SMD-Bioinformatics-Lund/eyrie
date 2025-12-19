// Sequencing runs table search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('tableSearch');
    const tableBody = document.getElementById('seqrunsTableBody');

    if (searchInput && tableBody) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const rows = tableBody.getElementsByTagName('tr');
            
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchValue) ? '' : 'none';
            }
        });
    }

    // Refresh table data periodically (every 30 seconds)
    setInterval(function() {
        if (window.location.pathname.includes('/seqruns') && !window.location.pathname.includes('/seqrun/')) {
            refreshSeqRunsTable();
        }
    }, 30000);
});

// Function to refresh sequencing runs table
function refreshSeqRunsTable() {
    fetch('/seqruns')
        .then(response => response.text())
        .then(html => {
            // Extract the table body content from the response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTableBody = doc.getElementById('seqrunsTableBody');
            
            if (newTableBody) {
                const currentTableBody = document.getElementById('seqrunsTableBody');
                if (currentTableBody) {
                    currentTableBody.innerHTML = newTableBody.innerHTML;
                }
            }
        })
        .catch(error => {
            console.error('Error refreshing sequencing runs table:', error);
        });
}