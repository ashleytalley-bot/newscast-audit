export class TableRenderer {
    /**
     * Render a data table
     */
    render(containerId: string, data: Record<string, any>[], columns: string[], config: any) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!data || data.length === 0) {
            container.innerHTML = '<p class="text-muted text-center p-3">No data available</p>';
            return;
        }

        let html = '<table class="data-table"><thead><tr>';

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
                const className = this.getCellClass(col, value);
                const displayValue = this.formatCellValue(col, value);

                html += `<td class="${className}">${displayValue}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Get CSS class for cell based on value
     * Uses the "Editorial Data Studio" performance scale
     */
    private getCellClass(columnName: string, value: any): string {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            if (typeof value !== 'number') return '';

            if (value >= 90) return 'cell-excellent';
            if (value >= 80) return 'cell-good';
            if (value >= 50) return 'cell-moderate';
            return 'cell-poor';
        }
        return '';
    }

    /**
     * Format cell value for display
     */
    private formatCellValue(columnName: string, value: any): string {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            return typeof value === 'number' ? value.toFixed(1) + '%' : value;
        }
        return String(value);
    }
}
