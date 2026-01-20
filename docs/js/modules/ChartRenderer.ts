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
    public async captureChartAsImage(elementId: string, width: number = 800, height: number = 500): Promise<string | null> {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Chart element ${elementId} not found`);
            return null;
        }

        try {
            return await Plotly.toImage(element, {
                format: 'png',
                width,
                height
            });
        } catch (error) {
            console.error(`Error capturing chart ${elementId}:`, error);
            return null;
        }
    }
}
