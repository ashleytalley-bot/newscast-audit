import {
    PLOTLY_CONFIG,
    getOverallBarConfig,
    getPerNewscastBarConfig,
    getWeeklyTrendConfig,
    getHeatmapConfig
} from './chart-config.js';

// Global declaration for Plotly
declare const Plotly: any;

export class ChartRenderer {
    /**
     * Render overall metrics chart
     */
    public renderOverallChart(containerId: string, chartData: any, config: any) {
        // Use new unified config generator
        // We ignore the passed 'config' palette in favor of the theme.ts system
        const { trace, layout } = getOverallBarConfig(
            chartData.labels,
            chartData.values,
            chartData.n
        );

        // Title removed to avoid duplication with card header

        Plotly.newPlot(containerId, [trace], layout, PLOTLY_CONFIG);
    }

    /**
     * Render per-newscast charts
     */
    public renderPerNewscastCharts(containerId: string, perNewscastData: any[], config: any) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!perNewscastData || perNewscastData.length === 0) {
            container.innerHTML = '<p>No newscast data available</p>';
            return;
        }

        container.innerHTML = '';

        perNewscastData.forEach((data, index) => {
            const chartId = `chart-newscast-${index}`;
            const card = document.createElement('div');
            card.className = 'chart-card';
            // We remove the explicit H3 header here if the chart title covers it, 
            // but for per-newscast, the chart title in layout is cleaner.
            // Let's keep the card container simple.
            card.innerHTML = `<div id="${chartId}" class="chart-container"></div>`;
            container.appendChild(card);

            const { trace, layout } = getPerNewscastBarConfig(
                data.newscast,
                data.labels,
                data.values,
                data.n
            );

            Plotly.newPlot(chartId, [trace], layout, PLOTLY_CONFIG);
        });
    }

    /**
     * Render weekly trend chart
     */
    public renderWeeklyChart(containerId: string, weeklyData: any, config: any) {
        const container = document.getElementById(containerId);
        if (!container || !weeklyData) return;

        const { traces, layout } = getWeeklyTrendConfig(
            weeklyData.dates,
            weeklyData.values,
            weeklyData.full_dates,
            weeklyData.center_line,
            weeklyData.ucl,
            weeklyData.lcl
        );

        // Title removed to avoid duplication with card header

        Plotly.newPlot(containerId, traces, layout, PLOTLY_CONFIG);
    }

    /**
     * Render heatmap
     */
    public renderHeatmap(containerId: string, perNewscastData: any[], config: any) {
        const container = document.getElementById(containerId);
        if (!container || !perNewscastData || perNewscastData.length === 0) return;

        // Prepare data for the helper
        // Extract all newscast names for Y-axis ordering (Reverse for top-down)
        const allNewscasts = perNewscastData.map(d => d.newscast).reverse();
        // Extract all metric labels
        const allMetrics = perNewscastData[0].labels;

        // Construct Z values
        const zValues: number[][] = [];
        const hoverText: string[][] = [];

        for (let i = perNewscastData.length - 1; i >= 0; i--) {
            const rowData = perNewscastData[i];
            zValues.push(rowData.values);

            // Build hover text matrix
            const rowHover = rowData.values.map((v: number, idx: number) => {
                return `Newscast: ${rowData.newscast}<br>` +
                    `Metric: ${allMetrics[idx]}<br>` +
                    `Yes: ${v.toFixed(1)}%<br>` +
                    `n: ${rowData.n}`;
            });
            hoverText.push(rowHover);
        }

        const { trace, layout } = getHeatmapConfig(
            zValues,
            allMetrics,
            allNewscasts,
            hoverText
        );

        Plotly.newPlot(containerId, [trace], layout, PLOTLY_CONFIG);
    }

    /**
     * Capture chart as image (for PowerPoint export)
     */
    /**
     * Capture chart as image (for PowerPoint export)
     * Forces Light Mode if forceLightMode is true
     */
    public async captureChartAsImage(elementId: string, width: number = 800, height: number = 500, forceLightMode: boolean = true): Promise<string | null> {
        const element = document.getElementById(elementId) as any;
        if (!element || !element.layout) {
            console.warn(`Chart element ${elementId} not found or initialized`);
            return null;
        }

        try {
            // If forcing light mode, we must make sure colors are optimized for white background
            let resultData: string;

            if (forceLightMode) {
                // deep clone layout to avoid mutating screen
                const originalLayout = element.layout;
                // Create a temporary layout override for printing
                const printLayout = JSON.parse(JSON.stringify(originalLayout));

                // Override for Light Mode (White Background)
                printLayout.paper_bgcolor = '#ffffff';
                printLayout.plot_bgcolor = '#ffffff';
                if (printLayout.font) printLayout.font.color = '#0f172a'; // Slate-900
                if (printLayout.xaxis) {
                    printLayout.xaxis.gridcolor = '#e5e7eb';
                    printLayout.xaxis.linecolor = '#d1d5db';
                    if (printLayout.xaxis.tickfont) printLayout.xaxis.tickfont.color = '#475569';
                }
                if (printLayout.yaxis) {
                    printLayout.yaxis.gridcolor = '#e5e7eb';
                    printLayout.yaxis.linecolor = '#d1d5db';
                    if (printLayout.yaxis.tickfont) printLayout.yaxis.tickfont.color = '#475569';
                }
                // Fix legends
                if (printLayout.legend && printLayout.legend.font) {
                    printLayout.legend.font.color = '#475569';
                }
                // Fix titles
                if (printLayout.title && printLayout.title.font) {
                    printLayout.title.font.color = '#0f172a';
                }

                // Apply temporary layout
                await Plotly.relayout(element, printLayout);

                // Capture
                resultData = await Plotly.toImage(element, { format: 'png', width, height });

                // Restore original (re-apply original settings)
                // Note: relayout merges, so we need to be careful. 
                // Creating a hidden clone is safer but slower. 
                // Let's try restoring the specific properties we changed.
                // Or simply: re-apply the original layout properties.
                const restoreLayout: any = {};
                restoreLayout.paper_bgcolor = originalLayout.paper_bgcolor;
                restoreLayout.plot_bgcolor = originalLayout.plot_bgcolor;
                restoreLayout.font = originalLayout.font;
                if (originalLayout.xaxis) restoreLayout.xaxis = originalLayout.xaxis;
                if (originalLayout.yaxis) restoreLayout.yaxis = originalLayout.yaxis;

                await Plotly.relayout(element, restoreLayout);

            } else {
                resultData = await Plotly.toImage(element, { format: 'png', width, height });
            }

            return resultData;
        } catch (error) {
            console.error(`Error capturing chart ${elementId}:`, error);
            // Attempt restore if failed during process
            try { return await Plotly.toImage(element, { format: 'png', width, height }); } catch (e) { return null; }
        }
    }
}
