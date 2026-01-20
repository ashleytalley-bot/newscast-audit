const COLORS = {
  // Brand
  primary: "#045ea8",
  primaryHover: "#034a85",
  primaryLight: "#e8f4fc",
  secondary: "#00458c",
  accent: "#f36f21",
  accentHover: "#d85d15",
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
  // Chart palette
  chartPalette: [
    "#045ea8",
    "#0891b2",
    "#0d9488",
    "#059669",
    "#65a30d",
    "#ca8a04",
    "#ea580c",
    "#dc2626"
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
const FONTS = {
  display: "'DM Serif Display', Georgia, serif",
  body: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace"
};
const FONT_SIZES = {
  xs: "0.64rem",
  // 10.24px
  sm: "0.8rem",
  // 12.8px
  base: "1rem",
  // 16px
  lg: "1.25rem",
  // 20px
  xl: "1.563rem",
  // 25px
  "2xl": "1.953rem",
  // 31.25px
  "3xl": "2.441rem",
  // 39px
  "4xl": "3.052rem"
  // 48.8px
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
function getPerformanceBgColor(value) {
  if (value >= 90)
    return COLORS.performance.excellentBg;
  if (value >= 80)
    return COLORS.performance.goodBg;
  if (value >= 50)
    return COLORS.performance.moderateBg;
  return COLORS.performance.poorBg;
}
function prefersDarkMode() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}
export {
  COLORS,
  FONTS,
  FONT_SIZES,
  getPerformanceBgColor,
  getPerformanceColor,
  prefersDarkMode
};
//# sourceMappingURL=theme.js.map
