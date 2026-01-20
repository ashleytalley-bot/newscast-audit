import {
  PLOTLY_CONFIG,
  getOverallBarConfig,
  getPerNewscastBarConfig,
  getWeeklyTrendConfig,
  getHeatmapConfig
} from "./chart-config.js";
class ChartRenderer {
  /**
   * Render overall metrics chart
   */
  renderOverallChart(containerId, chartData, config) {
    const { trace, layout } = getOverallBarConfig(
      chartData.labels,
      chartData.values,
      chartData.n
    );
    Plotly.newPlot(containerId, [trace], layout, PLOTLY_CONFIG);
  }
  /**
   * Render per-newscast charts
   */
  renderPerNewscastCharts(containerId, perNewscastData, config) {
    const container = document.getElementById(containerId);
    if (!container)
      return;
    if (!perNewscastData || perNewscastData.length === 0) {
      container.innerHTML = "<p>No newscast data available</p>";
      return;
    }
    container.innerHTML = "";
    perNewscastData.forEach((data, index) => {
      const chartId = `chart-newscast-${index}`;
      const card = document.createElement("div");
      card.className = "chart-card";
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
  renderWeeklyChart(containerId, weeklyData, config) {
    const container = document.getElementById(containerId);
    if (!container || !weeklyData)
      return;
    const { traces, layout } = getWeeklyTrendConfig(
      weeklyData.dates,
      weeklyData.values,
      weeklyData.full_dates,
      weeklyData.center_line,
      weeklyData.ucl,
      weeklyData.lcl
    );
    Plotly.newPlot(containerId, traces, layout, PLOTLY_CONFIG);
  }
  /**
   * Render heatmap
   */
  renderHeatmap(containerId, perNewscastData, config) {
    const container = document.getElementById(containerId);
    if (!container || !perNewscastData || perNewscastData.length === 0)
      return;
    const allNewscasts = perNewscastData.map((d) => d.newscast).reverse();
    const allMetrics = perNewscastData[0].labels;
    const zValues = [];
    const hoverText = [];
    for (let i = perNewscastData.length - 1; i >= 0; i--) {
      const rowData = perNewscastData[i];
      zValues.push(rowData.values);
      const rowHover = rowData.values.map((v, idx) => {
        return `Newscast: ${rowData.newscast}<br>Metric: ${allMetrics[idx]}<br>Yes: ${v.toFixed(1)}%<br>n: ${rowData.n}`;
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
  async captureChartAsImage(elementId, width = 800, height = 500, forceLightMode = true) {
    const element = document.getElementById(elementId);
    if (!element || !element.layout) {
      console.warn(`Chart element ${elementId} not found or initialized`);
      return null;
    }
    try {
      let resultData;
      if (forceLightMode) {
        const originalLayout = element.layout;
        const printLayout = JSON.parse(JSON.stringify(originalLayout));
        printLayout.paper_bgcolor = "#ffffff";
        printLayout.plot_bgcolor = "#ffffff";
        if (printLayout.font)
          printLayout.font.color = "#0f172a";
        if (printLayout.xaxis) {
          printLayout.xaxis.gridcolor = "#e5e7eb";
          printLayout.xaxis.linecolor = "#d1d5db";
          if (printLayout.xaxis.tickfont)
            printLayout.xaxis.tickfont.color = "#475569";
        }
        if (printLayout.yaxis) {
          printLayout.yaxis.gridcolor = "#e5e7eb";
          printLayout.yaxis.linecolor = "#d1d5db";
          if (printLayout.yaxis.tickfont)
            printLayout.yaxis.tickfont.color = "#475569";
        }
        if (printLayout.legend && printLayout.legend.font) {
          printLayout.legend.font.color = "#475569";
        }
        if (printLayout.title && printLayout.title.font) {
          printLayout.title.font.color = "#0f172a";
        }
        await Plotly.relayout(element, printLayout);
        resultData = await Plotly.toImage(element, { format: "png", width, height });
        const restoreLayout = {};
        restoreLayout.paper_bgcolor = originalLayout.paper_bgcolor;
        restoreLayout.plot_bgcolor = originalLayout.plot_bgcolor;
        restoreLayout.font = originalLayout.font;
        if (originalLayout.xaxis)
          restoreLayout.xaxis = originalLayout.xaxis;
        if (originalLayout.yaxis)
          restoreLayout.yaxis = originalLayout.yaxis;
        await Plotly.relayout(element, restoreLayout);
      } else {
        resultData = await Plotly.toImage(element, { format: "png", width, height });
      }
      return resultData;
    } catch (error) {
      console.error(`Error capturing chart ${elementId}:`, error);
      try {
        return await Plotly.toImage(element, { format: "png", width, height });
      } catch (e) {
        return null;
      }
    }
  }
}
export {
  ChartRenderer
};
//# sourceMappingURL=ChartRenderer.js.map
