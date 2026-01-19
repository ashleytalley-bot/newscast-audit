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
