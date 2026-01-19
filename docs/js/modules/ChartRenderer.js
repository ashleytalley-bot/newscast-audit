// @ts-check
import { CHART_DEFAULTS } from './config.js';

/**
 * @typedef {import('../types').ChartData} ChartData
 * @typedef {import('../types').PerNewscastChart} PerNewscastChart
 * @typedef {import('../types').ConfigPassthrough} ConfigPassthrough
 */

export class ChartRenderer {
    /**
     * Create a Plotly bar trace
     * @param {string[]} labels 
     * @param {number[]} values 
     * @param {string[]} colors 
     * @param {boolean} [isHorizontal=false] 
     */
    createBarTrace(labels, values, colors, isHorizontal = false) {
        const baseTrace = {
            type: 'bar',
            marker: { color: colors },
            text: values.map(v => v + '%'),
            textposition: 'outside'
        };

        if (isHorizontal) {
            return { ...baseTrace, y: labels, x: values, orientation: 'h' };
        } else {
            return { ...baseTrace, x: labels, y: values };
        }
    }

    /**
     * Create Plotly layout configuration
     * @param {string|null} title 
     * @param {ConfigPassthrough} config 
     * @param {boolean} [isHorizontal=false] 
     */
    createLayout(title, config, isHorizontal = false) {
        const margins = isHorizontal ? CHART_DEFAULTS.margins.perNewscast
            : CHART_DEFAULTS.margins.overall;
        const axis = isHorizontal ? 'xaxis' : 'yaxis';

        const layout = {
            title,
            [axis]: {
                title: 'Percent Yes',
                range: CHART_DEFAULTS.axisRange,
                ticksuffix: '%'
            },
            margin: margins,
            font: {
                family: CHART_DEFAULTS.fonts.family,
                color: config.palette.primary
            }
        };

        if (!isHorizontal) {
            layout.xaxis = { tickangle: -35 };
        }

        return layout;
    }

    /**
     * Render overall metrics chart
     * @param {string} containerId 
     * @param {ChartData} chartData 
     * @param {ConfigPassthrough} config 
     */
    renderOverallChart(containerId, chartData, config) {
        const trace = this.createBarTrace(chartData.labels, chartData.values, chartData.colors);
        const layout = this.createLayout(`Overall Audit Metrics (n=${chartData.n})`, config);

        // @ts-ignore Plotly is loaded via CDN
        Plotly.newPlot(containerId, [trace], layout, { responsive: CHART_DEFAULTS.responsive });
    }

    /**
     * Render per-newscast charts
     * @param {string} containerId 
     * @param {PerNewscastChart[]} perNewscastData 
     * @param {ConfigPassthrough} config 
     */
    renderPerNewscastCharts(containerId, perNewscastData, config) {
        const container = document.getElementById(containerId);

        if (!perNewscastData || perNewscastData.length === 0) {
            container.innerHTML = '<p>No newscast data available</p>';
            return;
        }

        container.innerHTML = '';

        perNewscastData.forEach((data, index) => {
            const chartId = `chart-newscast-${index}`;
            const card = document.createElement('div');
            card.className = 'chart-card';
            card.innerHTML = `<h3>${data.newscast} (n=${data.n})</h3><div id="${chartId}" class="chart-container"></div>`;
            container.appendChild(card);

            const trace = this.createBarTrace(data.labels, data.values, data.colors, true);
            const layout = this.createLayout(null, config, true);

            // @ts-ignore
            Plotly.newPlot(chartId, [trace], layout, { responsive: CHART_DEFAULTS.responsive });
        });
    }

    /**
     * Render weekly trend chart
     * @param {string} containerId 
     * @param {import('../types').WeeklyChart} weeklyData 
     * @param {ConfigPassthrough} config 
     */
    renderWeeklyChart(containerId, weeklyData, config) {
        const container = document.getElementById(containerId);
        if (!container || !weeklyData) return;

        const trace = {
            x: weeklyData.dates,
            y: weeklyData.values,
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: config.palette.primary,
                width: 3,
                shape: 'spline'
            },
            marker: { size: 8 },
            text: weeklyData.full_dates,
            hovertemplate: 'Week of %{text}: %{y}%<extra></extra>'
        };

        const layout = {
            title: 'Weekly Performance Trend',
            yaxis: {
                title: 'Percent Yes',
                range: CHART_DEFAULTS.axisRange,
                ticksuffix: '%'
            },
            margin: CHART_DEFAULTS.margins.overall,
            font: {
                family: CHART_DEFAULTS.fonts.family,
                color: config.palette.primary
            }
        };

        // @ts-ignore
        Plotly.newPlot(containerId, [trace], layout, { responsive: CHART_DEFAULTS.responsive });
    }

    /**
     * Render heatmap of metrics vs newscasts
     * @param {string} containerId
     * @param {PerNewscastChart[]} perNewscastData
     * @param {ConfigPassthrough} config
     */
    renderHeatmap(containerId, perNewscastData, config) {
        const container = document.getElementById(containerId);
        if (!container || !perNewscastData || perNewscastData.length === 0) return;

        // Find max N for opacity scaling
        const maxN = Math.max(...perNewscastData.map(d => d.n));

        // Extract all newscast names for Y-axis ordering
        // (Reverse them so the first item in array appears at top of chart)
        const allNewscasts = perNewscastData.map(d => d.newscast).reverse();

        // Create one trace per newscast to allow individual opacity control
        const traces = perNewscastData.map((data, i) => {
            // Normalize N (min 0.3 opacity to ensure visibility)
            const normalizedN = maxN > 0 ? (data.n / maxN) : 1;
            const opacity = 0.3 + (0.7 * normalizedN);

            return {
                z: [data.values],
                x: data.labels,
                y: [data.newscast],
                type: 'heatmap',
                colorscale: [
                    [0, '#d32f2f'],   // Red for low
                    [0.5, '#fbc02d'], // Yellow for mid
                    [1, '#388e3c']    // Green for high
                ],
                zmin: 0,
                zmax: 100,
                opacity: opacity,
                showscale: i === 0, // Only show colorbar for the first trace
                hoverongaps: false,
                hovertemplate:
                    `Newscast: %{y}<br>` +
                    `Metric: %{x}<br>` +
                    `Yes: %{z}%<br>` +
                    `n: ${data.n}<extra></extra>`
            };
        });

        const layout = {
            title: 'Performance Heatmap (Opacity based on Sample Size)',
            xaxis: {
                tickangle: -45,
                automargin: true,
                side: 'top' // Move labels to top for better readability
            },
            yaxis: {
                automargin: true,
                categoryarray: allNewscasts,
                categoryorder: 'array'
            },
            margin: {
                l: 120, r: 20, b: 50, t: 150 // Increased top margin for labels
            },
            // Ensure traces share the same comparison scale
            coloraxis: {
                cmin: 0,
                cmax: 100
            }
        };

        // @ts-ignore
        Plotly.newPlot(containerId, traces, layout, { responsive: CHART_DEFAULTS.responsive });
    }

    /**
     * Capture chart as image (for PowerPoint export)
     * @param {string} elementId 
     * @param {number} [width=800] 
     * @param {number} [height=500] 
     */
    async captureChartAsImage(elementId, width = 800, height = 500) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Chart element ${elementId} not found`);
            return null;
        }

        try {
            // @ts-ignore
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
