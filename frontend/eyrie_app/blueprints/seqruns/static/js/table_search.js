/**
 * Shared table search utility
 * Provides reusable table filtering functionality across seqruns templates
 */

class TableSearch {
    constructor(searchInputId, tableBodyId, options = {}) {
        this.searchInput = document.getElementById(searchInputId);
        this.tableBody = document.getElementById(tableBodyId);
        this.options = {
            event: options.event || 'keyup',
            skipEmptyRows: options.skipEmptyRows !== false, // default true
            ...options
        };

        if (this.searchInput && this.tableBody) {
            this.init();
        }
    }

    init() {
        this.searchInput.addEventListener(this.options.event, () => {
            this.filterTable();
        });
    }

    filterTable() {
        const searchValue = this.searchInput.value.toLowerCase();
        const rows = this.tableBody.getElementsByTagName('tr');

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];

            // Skip rows with only one cell (typically "no data" messages)
            if (this.options.skipEmptyRows && row.getElementsByTagName('td').length === 1) {
                continue;
            }

            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchValue) ? '' : 'none';
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TableSearch;
} else {
    window.TableSearch = TableSearch;
}
