// @ts-check

/**
 * @typedef {import('../types').ConfigPassthrough} ConfigPassthrough
 */

export class TableRenderer {
    /**
     * Render a data table
     * @param {string} containerId - DOM ID of container
     * @param {Record<string, unknown>[]} data - Data rows
     * @param {string[]} columns - Column names to display
     * @param {ConfigPassthrough} config - Configuration object
     */
    render(containerId, data, columns, config) {
        const container = document.getElementById(containerId);

        if (!data || data.length === 0) {
            container.innerHTML = '<p>No data available</p>';
            return;
        }

        const thresholds = config.thresholds;
        let html = '<table><thead><tr>';

        // Table headers
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';

        // Table rows
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                const className = this.getCellClass(col, value, thresholds);
                const displayValue = this.formatCellValue(col, value);

                html += `<td class="${className}">${displayValue}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Get CSS class for cell based on value and thresholds
     * @param {string} columnName 
     * @param {any} value 
     * @param {Record<string, number>} thresholds 
     */
    getCellClass(columnName, value, thresholds) {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            if (value >= thresholds.good) return 'pct-good';
            if (value <= thresholds.poor) return 'pct-poor';
            return 'pct-moderate';
        }
        return '';
    }

    /**
     * Format cell value for display
     * @param {string} columnName 
     * @param {any} value 
     */
    formatCellValue(columnName, value) {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            return value + '%';
        }
        return value;
    }
}
