export class TableRenderer {
    /**
     * Render a data table
     */
    render(containerId: string, data: Record<string, any>[], columns: string[], config: any) {
        const container = document.getElementById(containerId);
        if (!container) return;

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
     */
    private getCellClass(columnName: string, value: any, thresholds: Record<string, number>): string {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            if (value >= thresholds.good) return 'pct-good';
            if (value <= thresholds.poor) return 'pct-poor';
            return 'pct-moderate';
        }
        return '';
    }

    /**
     * Format cell value for display
     */
    private formatCellValue(columnName: string, value: any): string {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            return value + '%';
        }
        return String(value);
    }
}
