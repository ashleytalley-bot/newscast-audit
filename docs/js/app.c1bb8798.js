// docs/js/modules/config.ts
var LOADING_MESSAGES = {
  readingFile: "Reading Excel file...",
  initPython: "Initializing Python environment...",
  loadingLibs: "Loading data processing libraries...",
  processing: "Processing data...",
  rendering: "Rendering charts..."
};

// docs/js/modules/theme.ts
var COLORS = {
  // Brand - TEGNA Theme
  primary: "#FF5F00",
  // TEGNA Primary Orange (Action)
  primaryHover: "#CC4C00",
  primaryLight: "#FFF0E5",
  secondary: "#010a48",
  // TEGNA Deep Navy (Extracted)
  header: "#010a48",
  // TEGNA Deep Navy (Header)
  accent: "#010a48",
  // Deep Blue as accent
  accentHover: "#000000",
  alert: "#dc2626",
  alertLight: "#fee2e2",
  // Performance scale
  performance: {
    excellent: "#059669",
    excellentBg: "#d1fae5",
    good: "#0ea5e9",
    goodBg: "#e0f2fe",
    moderate: "#f59e0b",
    moderateBg: "#fef3c7",
    poor: "#dc2626",
    poorBg: "#fee2e2"
  },
  // Chart palette - TEGNA Oriented
  chartPalette: [
    "#001489",
    // Navy (Brand)
    "#FF5F00",
    // Orange (Primary)
    "#00458c",
    // Medium Blue
    "#fb923c",
    // Light Orange
    "#334155",
    // Slate 700
    "#94a3b8",
    // Slate 400
    "#0ea5e9",
    // Sky Blue
    "#dc2626"
    // Red (Alert)
  ],
  // UI
  ui: {
    bg: "#f8fafc",
    bgSoft: "#f1f5f9",
    bgCard: "#ffffff",
    border: "#e2e8f0",
    borderStrong: "#cbd5e1",
    text: "#0f172a",
    textSecondary: "#475569",
    textMuted: "#94a3b8"
  }
};
var FONTS = {
  display: "'DM Serif Display', Georgia, serif",
  body: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace"
};
function getPerformanceColor(value) {
  if (value >= 90)
    return COLORS.performance.excellent;
  if (value >= 80)
    return COLORS.performance.good;
  if (value >= 50)
    return COLORS.performance.moderate;
  return COLORS.performance.poor;
}

// docs/js/modules/chart-config.ts
var PLOTLY_CONFIG = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: [
    "select2d",
    "lasso2d",
    "autoScale2d",
    "hoverClosestCartesian",
    "hoverCompareCartesian"
  ],
  toImageButtonOptions: {
    format: "png",
    filename: "chart",
    height: 600,
    width: 1e3,
    scale: 2
  }
};
function getBaseLayout() {
  const dark = false;
  return {
    font: {
      family: FONTS.body,
      size: 13,
      color: COLORS.ui.text
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { t: 40, r: 24, b: 60, l: 60 },
    hoverlabel: {
      bgcolor: "#ffffff",
      bordercolor: COLORS.ui.border,
      font: {
        family: FONTS.body,
        size: 12,
        color: COLORS.ui.text
      }
    },
    xaxis: {
      gridcolor: "#e5e7eb",
      gridwidth: 1,
      zerolinecolor: "#d1d5db",
      linecolor: "#d1d5db",
      tickfont: {
        size: 11,
        family: FONTS.body,
        color: COLORS.ui.textSecondary
      }
    },
    yaxis: {
      gridcolor: "#e5e7eb",
      gridwidth: 1,
      zerolinecolor: "#d1d5db",
      linecolor: "#d1d5db",
      tickfont: {
        size: 11,
        family: FONTS.body,
        color: COLORS.ui.textSecondary
      }
    }
  };
}
function getOverallBarConfig(labels, values, n) {
  const baseLayout = getBaseLayout();
  const trace = {
    type: "bar",
    x: labels,
    y: values,
    marker: {
      color: values.map((v) => getPerformanceColor(v)),
      line: { width: 0 }
    },
    text: values.map((v) => `<b>${v.toFixed(0)}%</b>`),
    textposition: "inside",
    textangle: 0,
    textfont: {
      family: FONTS.body,
      // switched to Sans-Serif
      size: 14,
      // larger for main chart
      color: "#ffffff"
      // Always White
    },
    hovertemplate: "<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    customdata: Array(labels.length).fill(n)
  };
  const layout = {
    ...baseLayout,
    bargap: 0.25,
    xaxis: {
      ...baseLayout.xaxis,
      tickangle: labels.some((l) => l.length > 15) ? -35 : 0,
      categoryorder: "total descending"
    },
    yaxis: {
      ...baseLayout.yaxis,
      range: [0, 105],
      ticksuffix: "%",
      dtick: 20
    },
    margin: { t: 20, r: 20, b: 100, l: 50 }
  };
  return { trace, layout };
}
function getWeeklyTrendConfig(dates, values, fullDates, centerLine, ucl, lcl) {
  const baseLayout = getBaseLayout();
  const traces = [];
  if (ucl && lcl) {
    const validIndices = ucl.map((u, i) => u !== null && lcl[i] !== null);
    const bandX = [...dates.filter((_, i) => validIndices[i]), ...dates.filter((_, i) => validIndices[i]).reverse()];
    const bandY = [
      ...ucl.filter((_, i) => validIndices[i]),
      ...lcl.filter((_, i) => validIndices[i]).reverse()
    ];
    traces.push({
      type: "scatter",
      mode: "none",
      fill: "toself",
      fillcolor: "rgba(156, 163, 175, 0.12)",
      x: bandX,
      y: bandY,
      hoverinfo: "skip",
      showlegend: false,
      name: "Control Band"
    });
  }
  if (centerLine !== void 0) {
    traces.push({
      type: "scatter",
      mode: "lines",
      x: dates,
      y: Array(dates.length).fill(centerLine),
      line: {
        color: "rgba(107, 114, 128, 0.5)",
        width: 1,
        dash: "dot"
      },
      hoverinfo: "skip",
      showlegend: true,
      name: `Center Line (${centerLine.toFixed(1)}%)`
    });
  }
  traces.push({
    type: "scatter",
    mode: "lines+markers",
    x: dates,
    y: values,
    text: fullDates,
    line: {
      color: COLORS.primary,
      width: 3,
      shape: "linear"
    },
    marker: {
      size: 10,
      color: COLORS.primary,
      line: { color: "#ffffff", width: 2 }
    },
    connectgaps: true,
    hovertemplate: "<b>Week of %{text}</b><br>%{y:.1f}%<extra></extra>",
    showlegend: true,
    name: "Weekly Average"
  });
  const layout = {
    ...baseLayout,
    showlegend: true,
    legend: {
      orientation: "h",
      yanchor: "bottom",
      y: 1.02,
      xanchor: "right",
      x: 1,
      font: { size: 11 }
    },
    xaxis: {
      ...baseLayout.xaxis,
      tickangle: -45
    },
    yaxis: {
      ...baseLayout.yaxis,
      range: [0, 105],
      ticksuffix: "%",
      dtick: 20
    },
    margin: { t: 50, r: 20, b: 80, l: 50 }
  };
  return { traces, layout };
}
function getHeatmapConfig(zValues, xLabels, yLabels, hoverText) {
  const baseLayout = getBaseLayout();
  const trace = {
    type: "heatmap",
    z: zValues,
    x: xLabels,
    y: yLabels,
    colorscale: [
      [0, "#fecaca"],
      // Red-200 (0%)
      [0.3, "#fed7aa"],
      // Orange-200 (30%)
      [0.5, "#fef08a"],
      // Yellow-200 (50%)
      [0.7, "#bbf7d0"],
      // Green-200 (70%)
      [1, "#86efac"]
      // Green-300 (100%)
    ],
    colorbar: {
      title: { text: "Score", side: "right", font: { size: 11 } },
      ticksuffix: "%",
      thickness: 15,
      outlinewidth: 0,
      tickfont: { size: 10 },
      len: 0.8
    },
    xgap: 2,
    ygap: 2,
    hovertemplate: "%{text}<extra></extra>",
    text: hoverText,
    texttemplate: "%{z:.0f}",
    textfont: {
      size: 12,
      family: FONTS.mono,
      color: "#000000"
      // Pure black for maximum contrast on pastel backgrounds
    },
    showscale: true
  };
  const height = Math.max(400, yLabels.length * 40 + 120);
  const layout = {
    ...baseLayout,
    height,
    xaxis: {
      ...baseLayout.xaxis,
      side: "top",
      tickangle: -45,
      automargin: true
    },
    yaxis: {
      ...baseLayout.yaxis,
      autorange: "reversed",
      tickfont: { size: 11 }
    },
    // Increase top margin for rotated labels
    margin: { t: 160, r: 80, b: 20, l: 120 }
  };
  return { trace, layout };
}
function getPerNewscastBarConfig(newscast, labels, values, n) {
  const baseLayout = getBaseLayout();
  const trace = {
    type: "bar",
    orientation: "h",
    y: labels,
    x: values,
    marker: {
      color: values.map((v) => getPerformanceColor(v)),
      line: { width: 0 }
    },
    text: values.map((v) => `<b>${v.toFixed(0)}%</b>`),
    // Smart positioning: Outside if small (<25%), Inside if large
    textposition: values.map((v) => v < 25 ? "outside" : "inside"),
    // Smart coloring: Black (ui text) if outside, White if inside
    textfont: {
      family: FONTS.body,
      size: 13,
      color: values.map((v) => v < 25 ? COLORS.ui.text : "#ffffff")
    },
    constraintext: "none",
    // Allow text to overflow bar if inside
    cliponaxis: false,
    // Allow text to go outside plot area
    hovertemplate: "<b>%{y}</b><br>%{x:.1f}%<extra></extra>"
  };
  const layout = {
    ...baseLayout,
    title: {
      text: `${newscast} (n=${n})`,
      font: { size: 14, family: FONTS.body },
      x: 0,
      xanchor: "left"
    },
    bargap: 0.2,
    xaxis: {
      ...baseLayout.xaxis,
      range: [0, 110],
      // Increased to accommodate outside labels
      ticksuffix: "%",
      dtick: 25,
      showgrid: true,
      zeroline: true,
      fixedrange: true
      // Prevent zooming
    },
    yaxis: {
      ...baseLayout.yaxis,
      automargin: true
    },
    // Large left margin for labels, standard right margin
    margin: { t: 40, r: 60, b: 40, l: 250 },
    height: Math.max(200, labels.length * 35 + 80)
  };
  return { trace, layout };
}

// docs/js/modules/ChartRenderer.ts
var ChartRenderer = class {
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
};

// docs/js/modules/TableRenderer.ts
var TableRenderer = class {
  /**
   * Render a data table
   */
  render(containerId, data, columns, config) {
    const container = document.getElementById(containerId);
    if (!container)
      return;
    if (!data || data.length === 0) {
      container.innerHTML = '<p class="text-muted text-center p-3">No data available</p>';
      return;
    }
    let html = '<table class="data-table"><thead><tr>';
    columns.forEach((col) => {
      html += `<th>${col}</th>`;
    });
    html += "</tr></thead><tbody>";
    data.forEach((row) => {
      html += "<tr>";
      columns.forEach((col) => {
        const value = row[col];
        const className = this.getCellClass(col, value);
        const displayValue = this.formatCellValue(col, value);
        html += `<td class="${className}">${displayValue}</td>`;
      });
      html += "</tr>";
    });
    html += "</tbody></table>";
    container.innerHTML = html;
  }
  /**
   * Get CSS class for cell based on value
   * Uses the "Editorial Data Studio" performance scale
   */
  getCellClass(columnName, value) {
    if (columnName === "Yes %" || columnName === "Complete %" || columnName === "Completeness") {
      if (typeof value !== "number")
        return "";
      if (value >= 90)
        return "cell-excellent";
      if (value >= 80)
        return "cell-good";
      if (value >= 50)
        return "cell-moderate";
      return "cell-poor";
    }
    return "";
  }
  /**
   * Format cell value for display
   */
  formatCellValue(columnName, value) {
    if (columnName === "Yes %" || columnName === "Complete %" || columnName === "Completeness") {
      return typeof value === "number" ? value.toFixed(1) + "%" : value;
    }
    return String(value);
  }
};

// docs/js/modules/DataExporter.ts
var DataExporter = class {
  /**
   * Export data to Excel workbook
   */
  async exportToExcel(processedData) {
    const workbook = XLSX.utils.book_new();
    this.addSheetFromData(workbook, processedData.export_data.overall, "Overall Metrics");
    this.addSheetFromData(workbook, processedData.export_data.data_quality, "Data Quality");
    if (processedData.export_data.recent && processedData.export_data.recent.length > 0) {
      this.addSheetFromData(workbook, processedData.export_data.recent, "Recent Week");
    }
    if (processedData.export_data.volume && processedData.export_data.volume.length > 0) {
      this.addSheetFromData(workbook, processedData.export_data.volume, "Volume by Newscast");
    }
    this.addSheetFromData(workbook, processedData.export_data.normalized, "All Data");
    const timestamp = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    XLSX.writeFile(workbook, `newscast-audit-${timestamp}.xlsx`);
  }
  /**
   * Add a sheet to workbook from data
   */
  addSheetFromData(workbook, data, sheetName) {
    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  }
  /**
   * Export data to PowerPoint presentation
   */
  async exportToPowerPoint(processedData, chartRenderer) {
    const pptx = new PptxGenJS();
    pptx.layout = "LAYOUT_16x9";
    pptx.author = "Newscast Audit Tool";
    pptx.company = "TEGNA";
    let slide = pptx.addSlide();
    slide.addText("Newscast Audit Report", {
      x: 0.5,
      y: 2,
      w: 9,
      h: 1,
      fontSize: 44,
      bold: true,
      color: "045ea8"
    });
    slide.addText(`Generated: ${(/* @__PURE__ */ new Date()).toLocaleDateString()}`, {
      x: 0.5,
      y: 3.5,
      w: 9,
      h: 0.5,
      fontSize: 18,
      color: "666666"
    });
    slide = pptx.addSlide();
    slide.addText("Summary", { x: 0.5, y: 0.5, w: 9, h: 0.5, fontSize: 32, bold: true });
    slide.addText([
      { text: `Total Responses: ${processedData.summary.record_count}
`, options: { breakLine: true } },
      { text: `Metrics Tracked: ${processedData.summary.metric_count}
`, options: { breakLine: true } },
      { text: `Missing Newscast: ${processedData.summary.missing_newscast}`, options: { breakLine: true } }
    ], { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 18 });
    const overallChart = await chartRenderer.captureChartAsImage("chart-overall");
    if (overallChart) {
      slide = pptx.addSlide();
      slide.addText("Overall Audit Metrics", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 28, bold: true });
      slide.addImage({ data: overallChart, x: 0.5, y: 1, w: 9, h: 4.5 });
    }
    const perNewscastCharts = processedData.charts.per_newscast;
    for (let i = 0; i < perNewscastCharts.length; i++) {
      const chartId = `chart-newscast-${i}`;
      const chartImg = await chartRenderer.captureChartAsImage(chartId);
      if (chartImg) {
        slide = pptx.addSlide();
        slide.addText(`${perNewscastCharts[i].newscast} (n=${perNewscastCharts[i].n})`, {
          x: 0.5,
          y: 0.3,
          w: 9,
          h: 0.5,
          fontSize: 28,
          bold: true
        });
        slide.addImage({ data: chartImg, x: 0.5, y: 1, w: 9, h: 4.5 });
      }
    }
    const timestamp = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    pptx.writeFile({ fileName: `newscast-audit-${timestamp}.pptx` });
  }
};

// docs/js/modules/CommentRenderer.ts
var CommentRenderer = class {
  /**
   * Render the comments feed.
   */
  renderComments(containerId, comments) {
    const container = document.getElementById(containerId);
    if (!container)
      return;
    if (!comments || comments.length === 0) {
      container.innerHTML = '<p class="text-muted">No additional comments found.</p>';
      return;
    }
    const feedHtml = `
            <div class="comments-controls">
                <input type="text" id="comment-search" placeholder="Search comments..." class="form-control mb-3">
            </div>
            <div class="comments-list" style="max-height: 400px; overflow-y: auto;">
                ${comments.map((c) => this.createCommentCard(c)).join("")}
            </div>
            <p class="text-end text-muted mt-2"><small>Total comments: ${comments.length}</small></p>
        `;
    container.innerHTML = feedHtml;
    const searchInput = document.getElementById("comment-search");
    if (searchInput) {
      searchInput.addEventListener("keyup", (e) => {
        const target = e.target;
        const term = target.value.toLowerCase();
        this.filterComments(container, term);
      });
    }
  }
  /**
   * Create HTML for a single comment card.
   */
  createCommentCard(comment) {
    return `
            <div class="card mb-2 comment-card">
                <div class="card-body py-2">
                    <h6 class="card-subtitle mb-2 text-muted d-flex justify-content-between">
                        <span>${comment.newscast}</span>
                        <small>${comment.date}</small>
                    </h6>
                    <p class="card-text mb-0">${comment.text}</p>
                </div>
            </div>
        `;
  }
  /**
   * Filter comments based on search term.
   */
  filterComments(container, term) {
    const cards = container.querySelectorAll(".comment-card");
    cards.forEach((card) => {
      const htmlCard = card;
      const text = htmlCard.textContent?.toLowerCase() || "";
      htmlCard.style.display = text.includes(term) ? "" : "none";
    });
  }
};

// docs/js/modules/DateUtils.ts
function parseDateUTC(dateStr) {
  if (!dateStr)
    return null;
  try {
    let date;
    if (dateStr instanceof Date) {
      date = dateStr;
    } else {
      date = new Date(dateStr);
    }
    if (isNaN(date.getTime())) {
      return null;
    }
    const utcDate = new Date(Date.UTC(
      date.getUTCFullYear(),
      date.getUTCMonth(),
      date.getUTCDate()
    ));
    return utcDate;
  } catch (e) {
    console.error("Date parsing error:", e);
    return null;
  }
}
function toDateString(date) {
  if (!date || isNaN(date.getTime())) {
    return null;
  }
  try {
    return date.toISOString().split("T")[0];
  } catch (e) {
    console.error("Date formatting error:", e);
    return null;
  }
}
function toDayIndex(targetDate, referenceDate) {
  const targetUTC = Date.UTC(
    targetDate.getUTCFullYear(),
    targetDate.getUTCMonth(),
    targetDate.getUTCDate()
  );
  const referenceUTC = Date.UTC(
    referenceDate.getUTCFullYear(),
    referenceDate.getUTCMonth(),
    referenceDate.getUTCDate()
  );
  const DAY_MS = 864e5;
  const dayOffset = Math.round((targetUTC - referenceUTC) / DAY_MS);
  return dayOffset;
}
function fromDayIndex(dayIndex, referenceDate) {
  const referenceUTC = Date.UTC(
    referenceDate.getUTCFullYear(),
    referenceDate.getUTCMonth(),
    referenceDate.getUTCDate()
  );
  const DAY_MS = 864e5;
  const targetUTC = referenceUTC + dayIndex * DAY_MS;
  return new Date(targetUTC);
}
function getDateRange(dates) {
  if (!dates || dates.length === 0) {
    return null;
  }
  const parsedDates = dates.map((d) => parseDateUTC(d)).filter((d) => d !== null);
  if (parsedDates.length === 0) {
    return null;
  }
  const min = new Date(Math.min(...parsedDates.map((d) => d.getTime())));
  const max = new Date(Math.max(...parsedDates.map((d) => d.getTime())));
  const totalDays = toDayIndex(max, min);
  return { min, max, totalDays };
}

// docs/js/modules/DateSlider.ts
var DateSlider = class {
  constructor(sliderElementId, startInputId, endInputId, displayElementId = null, options = {}) {
    this.dateRange = null;
    this.isInitializing = false;
    const slider = document.getElementById(sliderElementId);
    if (!slider) {
      throw new Error(`Slider element with id '${sliderElementId}' not found`);
    }
    this.sliderElement = slider;
    this.startInput = document.getElementById(startInputId);
    this.endInput = document.getElementById(endInputId);
    this.displayElement = displayElementId ? document.getElementById(displayElementId) : null;
    this.options = options;
  }
  /**
   * Initialize the slider with a date range from processing results.
   *
   * @param result - Processing result containing date range or weekly dates
   */
  initialize(result) {
    let minDate = null;
    let maxDate = null;
    if (result.charts?.date_range?.min && result.charts?.date_range?.max) {
      minDate = parseDateUTC(result.charts.date_range.min);
      maxDate = parseDateUTC(result.charts.date_range.max);
      console.log("Using raw daily date range:", result.charts.date_range);
    } else if (result.charts?.weekly?.full_dates && result.charts.weekly.full_dates.length > 0) {
      const dateRange = getDateRange(result.charts.weekly.full_dates);
      if (dateRange) {
        minDate = dateRange.min;
        maxDate = dateRange.max;
      }
    }
    if (!minDate || !maxDate) {
      console.warn("No valid date range found in result. Slider not initialized.");
      return;
    }
    this.dateRange = {
      min: minDate,
      max: maxDate,
      totalDays: toDayIndex(maxDate, minDate)
    };
    console.log("Slider Setup (UTC):", {
      minDateStr: toDateString(this.dateRange.min),
      maxDateStr: toDateString(this.dateRange.max),
      totalDays: this.dateRange.totalDays
    });
    this.createSlider();
  }
  /**
   * Create or recreate the noUiSlider instance.
   */
  createSlider() {
    if (!this.dateRange) {
      throw new Error("Cannot create slider without date range. Call initialize() first.");
    }
    if (this.sliderElement.noUiSlider) {
      this.sliderElement.noUiSlider.destroy();
    }
    let dayStart = 0;
    let dayEnd = this.dateRange.totalDays;
    if (this.options.initialStartDate && this.options.initialEndDate) {
      const startDate = parseDateUTC(this.options.initialStartDate);
      const endDate = parseDateUTC(this.options.initialEndDate);
      if (startDate && endDate) {
        dayStart = Math.max(0, toDayIndex(startDate, this.dateRange.min));
        dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(endDate, this.dateRange.min));
      }
    } else if (this.startInput?.value && this.endInput?.value) {
      const startDate = parseDateUTC(this.startInput.value);
      const endDate = parseDateUTC(this.endInput.value);
      if (startDate && endDate) {
        dayStart = Math.max(0, toDayIndex(startDate, this.dateRange.min));
        dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(endDate, this.dateRange.min));
      }
    }
    this.isInitializing = true;
    try {
      noUiSlider.create(this.sliderElement, {
        start: [dayStart, dayEnd],
        connect: true,
        behaviour: "drag-tap",
        range: {
          "min": 0,
          "max": this.dateRange.totalDays
        },
        step: 1
      });
      this.sliderElement.noUiSlider.on("update", (values, handle) => {
        const startDay = Math.round(Number(values[0]));
        const endDay = Math.round(Number(values[1]));
        const startDate = fromDayIndex(startDay, this.dateRange.min);
        const endDate = fromDayIndex(endDay, this.dateRange.min);
        const startDateStr = toDateString(startDate);
        const endDateStr = toDateString(endDate);
        if (this.displayElement) {
          this.displayElement.innerHTML = `${startDateStr}  \u2014  ${endDateStr}`;
        }
        if (handle === 0 && this.startInput) {
          this.startInput.value = startDateStr;
        } else if (this.endInput) {
          this.endInput.value = endDateStr;
        }
        if (this.options.onUpdate && !this.isInitializing) {
          this.options.onUpdate(startDateStr, endDateStr);
        }
      });
      this.sliderElement.noUiSlider.on("change", (values) => {
        if (this.isInitializing) {
          console.log("Slider changed during initialization. Skipping auto-action.");
          return;
        }
        const startDay = Math.round(Number(values[0]));
        const endDay = Math.round(Number(values[1]));
        const startDate = fromDayIndex(startDay, this.dateRange.min);
        const endDate = fromDayIndex(endDay, this.dateRange.min);
        const startDateStr = toDateString(startDate);
        const endDateStr = toDateString(endDate);
        console.log("Slider released. Triggering onChange callback...");
        if (this.options.onChange) {
          this.options.onChange(startDateStr, endDateStr);
        }
      });
      setTimeout(() => {
        this.isInitializing = false;
        console.log("Slider initialization complete.");
      }, 100);
    } catch (err) {
      console.error("Slider creation failed:", err);
      this.isInitializing = false;
      throw err;
    }
  }
  /**
   * Get the current date range from the slider.
   */
  getCurrentRange() {
    if (!this.startInput || !this.endInput) {
      return null;
    }
    return {
      startDate: this.startInput.value,
      endDate: this.endInput.value
    };
  }
  /**
   * Programmatically set the slider range.
   */
  setRange(startDate, endDate) {
    if (!this.dateRange) {
      throw new Error("Slider not initialized");
    }
    const start = parseDateUTC(startDate);
    const end = parseDateUTC(endDate);
    if (!start || !end) {
      throw new Error("Invalid date strings provided");
    }
    const dayStart = Math.max(0, toDayIndex(start, this.dateRange.min));
    const dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(end, this.dateRange.min));
    this.sliderElement.noUiSlider.set([dayStart, dayEnd]);
  }
  /**
   * Destroy the slider instance.
   */
  destroy() {
    if (this.sliderElement.noUiSlider) {
      this.sliderElement.noUiSlider.destroy();
    }
    this.dateRange = null;
  }
};

// docs/js/services/PyodideService.ts
var PyodideService = class {
  constructor() {
    this.worker = null;
    this.initPromise = null;
    this.messageIdCounter = 0;
    this.pendingMessages = /* @__PURE__ */ new Map();
    this.onProgressCallback = null;
  }
  /**
   * Register a callback for progress updates.
   */
  setOnProgress(callback) {
    this.onProgressCallback = callback;
  }
  /**
   * Initialize Pyodide Web Worker.
   */
  async initialize() {
    if (this.initPromise) {
      return this.initPromise;
    }
    this.initPromise = this._doInitialize();
    return this.initPromise;
  }
  _doInitialize() {
    return new Promise((resolve, reject) => {
      if (this.worker) {
        resolve();
        return;
      }
      console.log("[PyodideService] Initializing Worker...");
      this.worker = new Worker("js/workers/PyodideWorker.js");
      this.worker.onmessage = (e) => {
        const { type, id: id2, payload, error, message } = e.data;
        const pending = this.pendingMessages.get(id2);
        if (type === "progress") {
          if (this.onProgressCallback) {
            this.onProgressCallback(message);
          }
          return;
        }
        if (pending) {
          if (type === "error") {
            pending.reject(new Error(error));
          } else if (type === "init_complete") {
            pending.resolve(null);
          } else if (type === "process_complete") {
            pending.resolve(payload);
          }
          this.pendingMessages.delete(id2);
        } else if (type === "error") {
          console.error("[PyodideService] Unhandled Worker Error:", error);
        }
      };
      this.worker.onerror = (err) => {
        console.error("Worker Script Error:", err);
        const initPending = this.pendingMessages.get(0) || this.pendingMessages.get(1);
        if (initPending && this.pendingMessages.size === 1) {
          initPending.reject(err);
        }
      };
      const id = this.nextId();
      this.pendingMessages.set(id, { resolve: () => resolve(), reject });
      const baseUrl = window.location.href.substring(0, window.location.href.lastIndexOf("/") + 1);
      this.worker.postMessage({
        type: "init",
        id,
        payload: { baseUrl }
      });
    });
  }
  /**
   * Process survey data using the Python pipeline in the worker.
   */
  async processData(inputData, options = null) {
    if (!this.worker) {
      throw new Error("Pyodide not initialized. Call initialize() first.");
    }
    return new Promise((resolve, reject) => {
      const id = this.nextId();
      this.pendingMessages.set(id, { resolve, reject });
      this.worker.postMessage({
        type: "process",
        id,
        payload: { data: inputData, options }
      });
    });
  }
  /**
   * Check if Pyodide is initialized.
   */
  isInitialized() {
    return this.worker !== null;
  }
  nextId() {
    return ++this.messageIdCounter;
  }
};

// docs/js/modules/ErrorUI.ts
var ErrorUI = class {
  constructor() {
    this.errorContainer = document.getElementById("error-message");
    this.warningsContainer = this.createWarningsContainer();
  }
  /**
   * Create warnings container if it doesn't exist
   */
  createWarningsContainer() {
    let container = document.getElementById("warnings-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "warnings-container";
      container.className = "warnings-container hidden";
      const resultsSection = document.getElementById("results-section");
      if (resultsSection) {
        resultsSection.appendChild(container);
      }
    }
    return container;
  }
  /**
   * Show structured error with detailed information
   */
  showError(error) {
    if (typeof error === "string") {
      this.showSimpleError(error);
      return;
    }
    if (error && error.error) {
      this.showStructuredError(error.error);
    } else if (error instanceof Error) {
      this.showSimpleError(error.message);
    } else {
      this.showSimpleError(String(error));
    }
  }
  /**
   * Show simple error message
   */
  showSimpleError(message) {
    this.errorContainer.innerHTML = this.createErrorHTML({
      error_type: "Error",
      message,
      user_action: "Please try again or contact support if the issue persists."
    });
    this.errorContainer.classList.remove("hidden");
    this.scrollToError();
  }
  /**
   * Show structured error with full details
   */
  showStructuredError(errorData) {
    this.errorContainer.innerHTML = this.createStructuredErrorHTML(errorData);
    this.errorContainer.classList.remove("hidden");
    this.scrollToError();
  }
  /**
   * Create HTML for basic error
   */
  createErrorHTML(errorData) {
    return `
            <div class="error-card">
                <div class="error-header">
                    <svg class="error-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <h3 class="error-title">${this.escapeHtml(errorData.error_type || "Error")}</h3>
                </div>
                <p class="error-message">${this.escapeHtml(errorData.message)}</p>
                ${errorData.user_action ? `
                    <div class="error-action">
                        <strong>What to do:</strong> ${this.escapeHtml(errorData.user_action)}
                    </div>
                ` : ""}
            </div>
        `;
  }
  /**
   * Create HTML for structured error with details
   */
  createStructuredErrorHTML(errorData) {
    let html = `
            <div class="error-card">
                <div class="error-header">
                    <svg class="error-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <h3 class="error-title">${this.escapeHtml(errorData.error_type || "Error")}</h3>
                </div>
                <p class="error-message">${this.escapeHtml(errorData.message)}</p>
        `;
    if (errorData.user_action) {
      html += `
                <div class="error-action">
                    <strong>What to do:</strong> ${this.escapeHtml(errorData.user_action)}
                </div>
            `;
    }
    if (errorData.details && Object.keys(errorData.details).length > 0) {
      html += `<div class="error-details">`;
      html += `<button class="error-details-toggle" onclick="this.nextElementSibling.classList.toggle('hidden')">
                Show technical details \u25BC
            </button>`;
      html += `<div class="error-details-content hidden">`;
      if (errorData.details.missing_columns) {
        html += `
                    <div class="error-detail-item">
                        <strong>Missing columns:</strong>
                        <ul>
                            ${errorData.details.missing_columns.map((col) => `<li>${this.escapeHtml(col)}</li>`).join("")}
                        </ul>
                    </div>
                `;
      }
      if (errorData.details.found_columns && errorData.details.found_columns.length > 0) {
        html += `
                    <div class="error-detail-item">
                        <strong>Columns found in file:</strong>
                        <ul>
                            ${errorData.details.found_columns.slice(0, 10).map((col) => `<li>${this.escapeHtml(col)}</li>`).join("")}
                            ${errorData.details.found_columns.length > 10 ? "<li>... and more</li>" : ""}
                        </ul>
                    </div>
                `;
      }
      if (errorData.details.issue_count !== void 0) {
        html += `
                    <div class="error-detail-item">
                        <strong>Issues found:</strong> ${errorData.details.issue_count}
                    </div>
                `;
      }
      if (errorData.details.examples && errorData.details.examples.length > 0) {
        html += `
                    <div class="error-detail-item">
                        <strong>Examples:</strong>
                        <ul>
                            ${errorData.details.examples.map((ex) => `<li>${this.escapeHtml(String(ex))}</li>`).join("")}
                        </ul>
                    </div>
                `;
      }
      if (errorData.details.initial_count) {
        html += `
                    <div class="error-detail-item">
                        <strong>Data summary:</strong>
                        <ul>
                            <li>Initial rows: ${errorData.details.initial_count}</li>
                            <li>Valid rows: ${errorData.details.final_count || 0}</li>
                            <li>Dropped rows: ${errorData.details.dropped_count || 0}</li>
                        </ul>
                    </div>
                `;
      }
      html += `</div></div>`;
    }
    html += `</div>`;
    return html;
  }
  /**
   * Show data quality messages (warnings and info)
   */
  showWarnings(qualityData) {
    if (!qualityData || (!qualityData.warnings || qualityData.warnings.length === 0) && (!qualityData.info || qualityData.info.length === 0)) {
      this.hideWarnings();
      return;
    }
    let html = '<div class="warnings-card">';
    if (qualityData.warnings && qualityData.warnings.length > 0) {
      html += `
                <div class="warnings-header">
                    <svg class="warning-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    <h4>Data Quality Warnings</h4>
                </div>
                <p class="warnings-intro">The data was processed successfully, but some quality issues were detected:</p>
            `;
      qualityData.warnings.forEach((warning) => {
        html += this.createQualityMessageHTML(warning, "warning");
      });
    }
    if (qualityData.info && qualityData.info.length > 0) {
      html += `
                <div class="info-header ${qualityData.warnings && qualityData.warnings.length > 0 ? "mt-4" : ""}">
                    <svg class="info-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <h4>Information</h4>
                </div>
            `;
      qualityData.info.forEach((info) => {
        html += this.createQualityMessageHTML(info, "info");
      });
    }
    html += "</div>";
    this.warningsContainer.innerHTML = html;
    this.warningsContainer.classList.remove("hidden");
  }
  createQualityMessageHTML(data, type) {
    return `
            <div class="quality-item ${type}-item">
                <p class="quality-message">${this.escapeHtml(data.message)}</p>
                ${data.examples && data.examples.length > 0 ? `
                    <details class="quality-examples">
                        <summary>Show examples (${data.examples.length})</summary>
                        <ul>
                            ${data.examples.map((ex) => `<li>${this.escapeHtml(String(ex))}</li>`).join("")}
                        </ul>
                    </details>
                ` : ""}
            </div>
        `;
  }
  hideError() {
    this.errorContainer.classList.add("hidden");
    this.errorContainer.innerHTML = "";
  }
  hideWarnings() {
    this.warningsContainer.classList.add("hidden");
    this.warningsContainer.innerHTML = "";
  }
  scrollToError() {
    setTimeout(() => {
      this.errorContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 100);
  }
  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
  clearAll() {
    this.hideError();
    this.hideWarnings();
  }
};
var errorUI = new ErrorUI();

// docs/js/app.ts
var NewscastAuditApp = class {
  constructor() {
    this.processedData = null;
    this.jsonData = null;
    // Raw Excel data
    this.dateSlider = null;
    console.log("NewscastAuditApp constructor called");
    this.pyodideService = new PyodideService();
    this.dom = {
      uploadSection: document.getElementById("upload-section"),
      resultsSection: document.getElementById("results-section"),
      dropZone: document.getElementById("drop-zone"),
      fileInput: document.getElementById("file-input"),
      loadingIndicator: document.getElementById("loading-indicator"),
      loadingText: document.getElementById("loading-text"),
      errorMessage: document.getElementById("error-message")
    };
    this.validateDom();
    this.chartRenderer = new ChartRenderer();
    this.tableRenderer = new TableRenderer();
    this.commentRenderer = new CommentRenderer();
    this.exporter = new DataExporter();
  }
  validateDom() {
    for (const [key, element] of Object.entries(this.dom)) {
      if (!element) {
        console.error(`CRITICAL: DOM element '${key}' not found!`);
        const errDiv = document.getElementById("error-message");
        if (errDiv) {
          errDiv.classList.remove("hidden");
          errDiv.textContent = `Error: DOM element '${key}' missing. Page structure incorrect.`;
        }
      }
    }
  }
  /**
   * Initialize the application
   */
  init() {
    console.log("Newscast Audit App v2.2.3 - Deployed: 2026-01-18");
    this.setupEventListeners();
    this.pyodideService.setOnProgress((msg) => {
      this.updateLoadingText(msg);
    });
  }
  /**
   * Set up all event listeners
   */
  setupEventListeners() {
    this.dom.dropZone.addEventListener("click", () => this.dom.fileInput.click());
    this.dom.fileInput.addEventListener("change", (e) => this.handleFileSelect(e));
    this.dom.dropZone.addEventListener("dragover", (e) => this.handleDragOver(e));
    this.dom.dropZone.addEventListener("dragleave", (e) => this.handleDragLeave(e));
    this.dom.dropZone.addEventListener("drop", (e) => this.handleDrop(e));
    document.getElementById("btn-export-excel")?.addEventListener("click", () => this.exportExcel());
    document.getElementById("btn-export-pptx")?.addEventListener("click", () => this.exportPowerPoint());
    document.getElementById("btn-new-file")?.addEventListener("click", () => this.resetToUpload());
    document.getElementById("btn-copy-comments")?.addEventListener("click", () => this.copyCommentsToClipboard());
  }
  async applyDateFilter() {
    const startInput = document.getElementById("filter-start-date");
    const endInput = document.getElementById("filter-end-date");
    const start = startInput?.value;
    const end = endInput?.value;
    console.log(`Apply Filter Triggered: [${start}] to [${end}]`);
    if (!this.jsonData)
      return;
    this.showLoading("Applying filters...");
    try {
      const options = {
        filter_start_date: start || null,
        filter_end_date: end || null
      };
      const result = await this.pyodideService.processData(this.jsonData, options);
      if (result.success) {
        this.processedData = result;
        this.renderResults();
      } else {
        errorUI.showError(result);
      }
    } catch (e) {
      console.error(e);
      errorUI.showError("Failed to apply filter");
    } finally {
      this.hideLoading();
    }
  }
  async copyCommentsToClipboard() {
    if (!this.processedData || !this.processedData.comments)
      return;
    const comments = this.processedData.comments;
    if (comments.length === 0) {
      alert("No comments to copy.");
      return;
    }
    const text = comments.map((c) => `[${c.date}] ${c.newscast}: ${c.text}`).join("\n");
    try {
      await navigator.clipboard.writeText(text);
      const btn = document.getElementById("btn-copy-comments");
      if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = "Copied!";
        setTimeout(() => {
          btn.innerHTML = originalText;
        }, 2e3);
      }
    } catch (err) {
      console.error("Failed to copy comments: ", err);
      alert("Failed to copy to clipboard.");
    }
  }
  /**
   * Initialize date range slider using the DateSlider module.
   *
   * This replaces the previous 114-line inline implementation with a clean,
   * testable class that uses centralized DateUtils for all date math.
   */
  initializeDateFilters(result) {
    try {
      this.dateSlider = new DateSlider(
        "date-slider",
        "filter-start-date",
        "filter-end-date",
        "slider-values",
        {
          onChange: (start, end) => {
            console.log(`Date filter changed: ${start} to ${end}`);
            this.applyDateFilter();
          }
        }
      );
      this.dateSlider.initialize(result);
    } catch (err) {
      console.error("Failed to initialize date slider:", err);
    }
  }
  // ═══════════════════════════════════════════════════════════════════════
  // FILE HANDLING
  // ═══════════════════════════════════════════════════════════════════════
  handleDragOver(e) {
    e.preventDefault();
    this.dom.dropZone.classList.add("drag-over");
  }
  handleDragLeave(e) {
    e.preventDefault();
    this.dom.dropZone.classList.remove("drag-over");
  }
  handleDrop(e) {
    e.preventDefault();
    this.dom.dropZone.classList.remove("drag-over");
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      this.processFile(files[0]);
    }
  }
  handleFileSelect(e) {
    const target = e.target;
    const files = target.files;
    if (files && files.length > 0) {
      this.processFile(files[0]);
    }
  }
  /**
   * Process uploaded Excel file
   */
  async processFile(file) {
    try {
      this.prepareUIForProcessing();
      if (!this.isValidExcelFile(file)) {
        errorUI.showError("Please upload an Excel file (.xlsx or .xls)");
        this.hideLoading();
        return;
      }
      this.showLoading(LOADING_MESSAGES.readingFile);
      const jsonData = await this.parseExcelFile(file);
      if (!this.isValidData(jsonData)) {
        errorUI.showError("Excel file appears to be empty");
        this.hideLoading();
        return;
      }
      this.jsonData = jsonData;
      this.showLoading(LOADING_MESSAGES.initPython);
      await this.pyodideService.initialize();
      this.showLoading(LOADING_MESSAGES.processing);
      const result = await this.pyodideService.processData(jsonData);
      await this.handleProcessingResult(result);
    } catch (error) {
      this.handleProcessingError(error);
    }
  }
  prepareUIForProcessing() {
    this.hideError();
    const startInput = document.getElementById("filter-start-date");
    const endInput = document.getElementById("filter-end-date");
    if (startInput)
      startInput.value = "";
    if (endInput)
      endInput.value = "";
  }
  isValidExcelFile(file) {
    return !!file.name.match(/\.xlsx?$/i);
  }
  isValidData(data) {
    return data && data.length > 0;
  }
  async handleProcessingResult(result) {
    if (!result.success) {
      errorUI.showError(result);
      this.hideLoading();
      return;
    }
    const successResult = result;
    if (successResult.quality && (successResult.quality.warnings && successResult.quality.warnings.length > 0 || successResult.quality.info && successResult.quality.info.length > 0)) {
      errorUI.showWarnings(successResult.quality);
    }
    this.showLoading(LOADING_MESSAGES.rendering);
    this.processedData = successResult;
    this.showResults();
    this.renderResults();
    this.hideLoading();
    this.initializeDateFilters(successResult);
  }
  handleProcessingError(error) {
    this.hideLoading();
    console.error("Processing error:", error);
    let msg = "Unknown error occurred";
    if (typeof error === "string") {
      msg = error;
    } else if (error instanceof Error) {
      msg = error.message;
    } else if (typeof error === "object" && error !== null) {
      const errObj = error;
      if (errObj.message)
        msg = errObj.message;
      else if (errObj.error)
        msg = errObj.error;
      else {
        try {
          msg = JSON.stringify(error);
        } catch (e) {
          msg = "Error object could not be stringified";
        }
      }
    }
    errorUI.showError(`Error processing file: ${msg}`);
  }
  /**
   * Parse Excel file to JSON using SheetJS
   */
  async parseExcelFile(file) {
    const arrayBuffer = await file.arrayBuffer();
    const workbook = XLSX.read(arrayBuffer, { type: "array", cellDates: true });
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
    return XLSX.utils.sheet_to_json(firstSheet);
  }
  // ═══════════════════════════════════════════════════════════════════════════
  // UI STATE MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════════════
  updateLoadingText(message) {
    if (this.dom.loadingText) {
      this.dom.loadingText.textContent = message;
    }
  }
  showLoading(message) {
    this.updateLoadingText(message);
    this.dom.loadingIndicator.classList.remove("hidden");
  }
  hideLoading() {
    this.dom.loadingIndicator.classList.add("hidden");
  }
  hideError() {
    this.dom.errorMessage.classList.add("hidden");
    errorUI.clearAll();
  }
  showResults() {
    this.dom.uploadSection.classList.add("hidden");
    this.dom.resultsSection.classList.remove("hidden");
    requestAnimationFrame(() => {
      this.dom.resultsSection.classList.add("is-visible");
    });
  }
  resetToUpload() {
    this.dom.resultsSection.classList.add("hidden");
    this.dom.resultsSection.classList.remove("is-visible");
    this.dom.uploadSection.classList.remove("hidden");
    this.dom.fileInput.value = "";
    this.hideError();
    errorUI.clearAll();
  }
  // ═══════════════════════════════════════════════════════════════════════
  // RESULT RENDERING
  // ═══════════════════════════════════════════════════════════════════════
  renderResults() {
    if (!this.processedData)
      return;
    try {
      this.renderSummary();
    } catch (e) {
      console.error("Error rendering summary:", e);
    }
    try {
      this.renderTables();
    } catch (e) {
      console.error("Error rendering tables:", e);
    }
    try {
      this.renderCharts();
    } catch (e) {
      console.error("Error rendering charts:", e);
    }
  }
  renderSummary() {
    if (!this.processedData)
      return;
    const summary = this.processedData.summary;
    document.getElementById("summary-rows").textContent = summary.record_count.toString();
    document.getElementById("summary-metrics").textContent = summary.metric_count.toString();
    document.getElementById("summary-missing").textContent = summary.missing_newscast.toString();
  }
  renderTables() {
    if (!this.processedData)
      return;
    const tables = this.processedData.tables;
    this.tableRenderer.render("table-overall", tables.overall, ["Question", "Yes %"], this.processedData.config);
    this.tableRenderer.render("table-quality", tables.data_quality, ["Question", "Complete %", "Missing"], this.processedData.config);
    const recentCard = document.getElementById("recent-week-card");
    if (tables.recent && recentCard) {
      recentCard.classList.remove("hidden");
      document.getElementById("recent-week-title").textContent = `Week of ${tables.recent_week_start}`;
      this.tableRenderer.render("table-recent", tables.recent, ["Question", "Yes %"], this.processedData.config);
    } else if (recentCard) {
      recentCard.classList.add("hidden");
    }
    if (tables.volume) {
      this.tableRenderer.render("table-volume", tables.volume, ["Newscast", "Responses"], this.processedData.config);
    }
    if (tables.users) {
      this.tableRenderer.render("table-users", tables.users, ["User", "Audits", "Completeness", "Most Missed Metric"], this.processedData.config);
    }
  }
  renderCharts() {
    if (!this.processedData)
      return;
    const charts = this.processedData.charts;
    const config = this.processedData.config;
    this.chartRenderer.renderOverallChart("chart-overall", charts.overall, config);
    this.chartRenderer.renderPerNewscastCharts("charts-per-newscast", charts.per_newscast, config);
    if (charts.weekly) {
      this.chartRenderer.renderWeeklyChart("chart-weekly", charts.weekly, config);
    }
    if (charts.filter_options && charts.filter_options.length > 0) {
      const select = document.getElementById("weekly-chart-filter");
      if (select) {
        select.innerHTML = "";
        charts.filter_options.forEach((opt, index) => {
          const option = document.createElement("option");
          option.value = index.toString();
          option.textContent = opt.label;
          select.appendChild(option);
        });
        select.onchange = () => {
          const selectedIndex = parseInt(select.value);
          const selectedData = charts.filter_options[selectedIndex];
          if (selectedData) {
            try {
              const weeklyData = {
                dates: selectedData.dates,
                values: selectedData.values,
                full_dates: selectedData.dates,
                center_line: selectedData.center_line,
                ucl: selectedData.ucl,
                lcl: selectedData.lcl
              };
              this.chartRenderer.renderWeeklyChart("chart-weekly", weeklyData, config);
            } catch (e) {
              console.error("Error updating chart:", e);
            }
          }
        };
      }
    }
    if (charts.per_newscast && charts.per_newscast.length > 0) {
      this.chartRenderer.renderHeatmap("chart-heatmap", charts.per_newscast, config);
    }
    if (this.processedData.comments) {
      this.commentRenderer.renderComments("comments-feed", this.processedData.comments);
    }
  }
  // ═══════════════════════════════════════════════════════════════════════
  // EXPORT FUNCTIONALITY
  // ═══════════════════════════════════════════════════════════════════════
  async exportExcel() {
    if (!this.processedData)
      return;
    await this.exporter.exportToExcel(this.processedData);
  }
  async exportPowerPoint() {
    if (!this.processedData)
      return;
    await this.exporter.exportToPowerPoint(this.processedData, this.chartRenderer);
  }
};
export {
  NewscastAuditApp
};
//# sourceMappingURL=app.js.map
