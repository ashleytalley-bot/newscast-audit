import { COLORS, FONTS, getPerformanceColor } from "./theme.js";
const isDarkMode = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
const PLOTLY_CONFIG = {
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
  const dark = isDarkMode();
  return {
    font: {
      family: FONTS.body,
      size: 13,
      color: dark ? "#f1f5f9" : COLORS.ui.text
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { t: 40, r: 24, b: 60, l: 60 },
    hoverlabel: {
      bgcolor: dark ? "#1e293b" : "#ffffff",
      bordercolor: dark ? "#334155" : COLORS.ui.border,
      font: {
        family: FONTS.body,
        size: 12,
        color: dark ? "#f1f5f9" : COLORS.ui.text
      }
    },
    xaxis: {
      gridcolor: dark ? "#334155" : "#e5e7eb",
      gridwidth: 1,
      zerolinecolor: dark ? "#475569" : "#d1d5db",
      linecolor: dark ? "#475569" : "#d1d5db",
      tickfont: {
        size: 11,
        family: FONTS.body,
        color: dark ? "#94a3b8" : COLORS.ui.textSecondary
      }
    },
    yaxis: {
      gridcolor: dark ? "#334155" : "#e5e7eb",
      gridwidth: 1,
      zerolinecolor: dark ? "#475569" : "#d1d5db",
      linecolor: dark ? "#475569" : "#d1d5db",
      tickfont: {
        size: 11,
        family: FONTS.body,
        color: dark ? "#94a3b8" : COLORS.ui.textSecondary
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
    text: values.map((v) => `${v.toFixed(0)}%`),
    textposition: "inside",
    textangle: 0,
    textfont: {
      family: FONTS.mono,
      size: 13,
      color: values.map((v) => {
        if (v >= 90)
          return "#ffffff";
        if (v >= 50)
          return "#000000";
        return "#ffffff";
      })
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
    text: values.map((v) => `${v.toFixed(0)}%`),
    textposition: "inside",
    textfont: {
      family: FONTS.mono,
      size: 11,
      color: values.map((v) => {
        if (v >= 90)
          return "#ffffff";
        if (v >= 50)
          return "#000000";
        return "#ffffff";
      })
    },
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
      range: [0, 105],
      ticksuffix: "%",
      dtick: 25
    },
    yaxis: {
      ...baseLayout.yaxis,
      automargin: true
    },
    margin: { t: 40, r: 20, b: 40, l: 150 },
    height: Math.max(200, labels.length * 35 + 80)
  };
  return { trace, layout };
}
const ANIMATION_CONFIG = {
  transition: {
    duration: 500,
    easing: "cubic-in-out"
  },
  frame: {
    duration: 500,
    redraw: false
  }
};
export {
  ANIMATION_CONFIG,
  PLOTLY_CONFIG,
  getBaseLayout,
  getHeatmapConfig,
  getOverallBarConfig,
  getPerNewscastBarConfig,
  getWeeklyTrendConfig
};
//# sourceMappingURL=chart-config.js.map
