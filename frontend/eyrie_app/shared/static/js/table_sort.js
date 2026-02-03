/**
 * Shared table sorting utility
 * Provides multi-column sorting functionality for sample tables
 */

class TableSort {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        if (!this.table) {
            console.error('TableSort: Table not found:', tableId);
            return;
        }

        this.tbody = this.table.querySelector('tbody');
        this.headers = this.table.querySelectorAll('thead th');
        this.sortState = []; // Array of {column, direction} for multi-sort
        this.options = {
            defaultSort: options.defaultSort || [], // e.g., [{column: 2, direction: 'desc'}, {column: 1, direction: 'asc'}]
            nonSortableColumns: options.nonSortableColumns || [0], // Column indices that shouldn't be sortable
            ...options
        };

        this.init();
    }

    init() {
        this.headers.forEach((header, index) => {
            if (this.isColumnSortable(index)) {
                header.style.cursor = 'pointer';
                header.setAttribute('data-sortable', 'true');
                header.addEventListener('click', (e) => this.handleHeaderClick(index, e.shiftKey));
                this.addSortIndicator(header);
            }
        });

        // Apply default sort if specified
        if (this.options.defaultSort.length > 0) {
            this.sortState = [...this.options.defaultSort];
            this.applySort();
            this.updateIndicators();
        }
    }

    isColumnSortable(index) {
        return !this.options.nonSortableColumns.includes(index);
    }

    handleHeaderClick(columnIndex, isShiftKey) {
        if (isShiftKey) {
            // Multi-sort: add to existing sort or toggle direction
            const existingIndex = this.sortState.findIndex(s => s.column === columnIndex);
            if (existingIndex >= 0) {
                this.toggleDirection(existingIndex);
            } else {
                this.sortState.push({column: columnIndex, direction: 'asc'});
            }
        } else {
            // Single column sort
            const existing = this.sortState.find(s => s.column === columnIndex);
            if (existing && this.sortState.length === 1) {
                // Toggle direction if already sorting by this column alone
                existing.direction = existing.direction === 'asc' ? 'desc' : 'asc';
            } else {
                // Start fresh sort by this column
                this.sortState = [{column: columnIndex, direction: 'asc'}];
            }
        }

        this.applySort();
        this.updateIndicators();
    }

    toggleDirection(stateIndex) {
        const state = this.sortState[stateIndex];
        if (state.direction === 'asc') {
            state.direction = 'desc';
        } else if (state.direction === 'desc') {
            // Remove from sort state on third click
            this.sortState.splice(stateIndex, 1);
        }
    }

    applySort() {
        const rows = Array.from(this.tbody.querySelectorAll('tr'));

        // Skip if no sort criteria or only empty/error rows
        if (this.sortState.length === 0) return;

        rows.sort((a, b) => {
            // Skip rows with only one cell (typically "no data" messages)
            if (a.cells.length === 1 || b.cells.length === 1) return 0;

            for (const {column, direction} of this.sortState) {
                const aVal = this.getCellValue(a, column);
                const bVal = this.getCellValue(b, column);
                const cmp = this.compare(aVal, bVal);
                if (cmp !== 0) {
                    return direction === 'asc' ? cmp : -cmp;
                }
            }
            return 0;
        });

        // Reorder rows in the DOM
        rows.forEach(row => this.tbody.appendChild(row));
    }

    getCellValue(row, column) {
        const cell = row.cells[column];
        if (!cell) return '';

        // Check for data-sort-value attribute first (for custom sort values)
        if (cell.hasAttribute('data-sort-value')) {
            return cell.getAttribute('data-sort-value').toLowerCase();
        }

        return cell.textContent.trim().toLowerCase();
    }

    compare(a, b) {
        // Handle empty values - push them to the end
        if (a === '' && b === '') return 0;
        if (a === '') return 1;
        if (b === '') return -1;

        // Try numeric comparison first
        const numA = parseFloat(a);
        const numB = parseFloat(b);
        if (!isNaN(numA) && !isNaN(numB)) {
            return numA - numB;
        }

        // Date comparison (ISO format or common date formats)
        const dateA = Date.parse(a);
        const dateB = Date.parse(b);
        if (!isNaN(dateA) && !isNaN(dateB)) {
            return dateA - dateB;
        }

        // String comparison
        return a.localeCompare(b);
    }

    addSortIndicator(header) {
        const indicator = document.createElement('span');
        indicator.className = 'sort-indicator';
        indicator.innerHTML = '';
        header.appendChild(indicator);
    }

    updateIndicators() {
        // Clear all indicators
        this.headers.forEach(header => {
            const indicator = header.querySelector('.sort-indicator');
            if (indicator) {
                indicator.innerHTML = '';
                indicator.classList.remove('active');
            }
        });

        // Update active indicators
        this.sortState.forEach((state, priority) => {
            const header = this.headers[state.column];
            if (!header) return;

            const indicator = header.querySelector('.sort-indicator');
            if (indicator) {
                const arrow = state.direction === 'asc' ? '↑' : '↓';
                // Show priority number if multi-sorting
                const priorityBadge = this.sortState.length > 1 ? `<sub>${priority + 1}</sub>` : '';
                indicator.innerHTML = arrow + priorityBadge;
                indicator.classList.add('active');
            }
        });
    }

    // Public method to re-sort after filtering or data changes
    refresh() {
        this.applySort();
    }

    // Public method to clear all sorting
    clearSort() {
        this.sortState = [];
        this.updateIndicators();
    }

    // Public method to set sort programmatically
    setSort(sortState) {
        this.sortState = sortState;
        this.applySort();
        this.updateIndicators();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TableSort;
} else {
    window.TableSort = TableSort;
}
