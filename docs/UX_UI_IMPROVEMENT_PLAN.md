# Newscast Audit — UX/UI Improvement Master Plan

> **Document Version**: 1.0
> **Created**: January 2025
> **Purpose**: Comprehensive guide for improving the user experience and interface of the Newscast Audit application

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Design Direction](#design-direction)
4. [Phase 1: Foundation Fixes](#phase-1-foundation-fixes)
5. [Phase 2: Typography System](#phase-2-typography-system)
6. [Phase 3: Plotly Chart Improvements](#phase-3-plotly-chart-improvements)
7. [Phase 4: Data Representation](#phase-4-data-representation)
8. [Phase 5: Interactions & Motion](#phase-5-interactions--motion)
9. [Phase 6: Layout Improvements](#phase-6-layout-improvements)
10. [Phase 7: Dark Mode](#phase-7-dark-mode)
11. [Implementation Checklist](#implementation-checklist)
12. [File Reference](#file-reference)

---

## Executive Summary

### What This App Does

The Newscast Audit application is a browser-based survey analysis tool for analyzing newscast quality audit data exported from Microsoft Forms. It runs entirely in the browser using Pyodide (Python via WebAssembly) and generates interactive reports with Plotly charts.

### Key Problems Identified

1. **Bootstrap Class Conflicts**: HTML uses Bootstrap utility classes (`d-flex`, `card`, `btn-outline-primary`) but Bootstrap CSS is never loaded
2. **Inconsistent Color System**: Hardcoded colors throughout charts bypass CSS variables
3. **Typography Chaos**: Mixed font sizes without clear hierarchy
4. **Chart Design Issues**: Default Plotly styling lacks polish and brand consistency
5. **Missing Dark Mode**: Partial implementation causes readability issues
6. **Spacing Inconsistencies**: Mix of CSS variables and hardcoded values

### Chosen Design Direction

**"Editorial Data Studio"** — A refined, professional aesthetic inspired by high-end newsroom dashboards and financial data terminals. Clean typography hierarchy, purposeful negative space, and data visualizations that feel authoritative yet accessible.

---

## Current State Analysis

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | TypeScript | 5.0 (strict) |
| Build Tool | esbuild | 0.19.0 |
| Charts | Plotly.js | 2.27.0 (CDN) |
| Excel I/O | SheetJS | 0.20.1 |
| PowerPoint | PptxGenJS | 3.12.0 |
| Python Runtime | Pyodide | 0.26.1 |
| Date Slider | noUiSlider | 14.6.3 |
| Testing | Playwright | 1.57.0 |

### Current Brand Colors

```css
--color-primary: #045ea8   /* TEGNA Blue */
--color-secondary: #00458c /* Darker blue */
--color-accent: #f36f21    /* Orange */
--color-alert: #d64541     /* Red */
```

### Current Chart Types

| Chart | File Location | Purpose |
|-------|---------------|---------|
| Overall Bar | `src/chart-renderer.ts` | Overall performance across all newscasts |
| Per-Newscast Bars | `src/chart-renderer.ts` | Individual newscast performance (horizontal) |
| Weekly Trend | `src/chart-renderer.ts` | Time-series with control limits |
| Heatmap | `src/chart-renderer.ts` | Newscast × Metric matrix |

### Key Files to Modify

```
docs/
├── index.html          # Main HTML, add fonts here
├── style.css           # Primary stylesheet
├── error-ui.css        # Error component styles
src/
├── chart-renderer.ts   # All Plotly chart logic
├── table-renderer.ts   # Table rendering
├── comment-renderer.ts # Comments section
├── chart-config.ts     # Chart configuration (create new)
├── theme.ts            # Theme configuration (create new)
```

---

## Design Direction

### Aesthetic: Editorial Data Studio

**Characteristics:**
- Sharp contrast between bold display headings and refined body text
- Restrained palette with strategic accent moments
- Generous whitespace with clear visual hierarchy
- Aligned grids with purposeful asymmetry
- Charts that feel crafted, not auto-generated

### Design Principles

1. **Data First**: Every visual decision should enhance data comprehension
2. **Consistent**: Use CSS variables everywhere, no hardcoded values
3. **Purposeful Motion**: Animations guide attention, never distract
4. **Accessible**: WCAG 2.1 AA compliance minimum
5. **Responsive**: Mobile-first, desktop-enhanced

---

## Phase 1: Foundation Fixes

### 1.1 Add Missing Utility Classes

**Problem**: HTML references Bootstrap classes that don't exist.

**File**: `docs/style.css`

**Add these utility classes:**

```css
/* ==========================================================================
   UTILITY CLASSES (Bootstrap-compatible)
   ========================================================================== */

/* Display */
.d-flex { display: flex; }
.d-none { display: none; }
.d-block { display: block; }
.d-inline-block { display: inline-block; }

/* Flexbox */
.flex-column { flex-direction: column; }
.flex-wrap { flex-wrap: wrap; }
.align-items-center { align-items: center; }
.align-items-start { align-items: start; }
.align-items-end { align-items: end; }
.justify-content-center { justify-content: center; }
.justify-content-between { justify-content: space-between; }
.justify-content-end { justify-content: flex-end; }

/* Gap */
.gap-1 { gap: 0.25rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 1rem; }
.gap-4 { gap: 1.5rem; }

/* Margin */
.m-0 { margin: 0; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 1rem; }
.mb-4 { margin-bottom: 1.5rem; }
.me-1 { margin-right: 0.25rem; }
.me-2 { margin-right: 0.5rem; }
.me-3 { margin-right: 1rem; }
.ms-1 { margin-left: 0.25rem; }
.ms-2 { margin-left: 0.5rem; }
.ms-auto { margin-left: auto; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; }

/* Padding */
.p-0 { padding: 0; }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 1rem; }
.px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
.px-3 { padding-left: 1rem; padding-right: 1rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }

/* Width */
.w-100 { width: 100%; }
.w-auto { width: auto; }

/* Text */
.text-center { text-align: center; }
.text-end { text-align: right; }
.text-muted { color: var(--color-text-secondary); }
.fw-bold { font-weight: 700; }
.fw-semibold { font-weight: 600; }
.small { font-size: 0.875rem; }
```

### 1.2 Centralize Color System

**File**: `docs/style.css`

**Replace existing `:root` with expanded version:**

```css
:root {
  /* ==========================================================================
     BRAND COLORS
     ========================================================================== */
  --color-primary: #045ea8;
  --color-primary-hover: #034a85;
  --color-primary-light: #e8f4fc;
  --color-secondary: #00458c;
  --color-accent: #f36f21;
  --color-accent-hover: #d85d15;
  --color-alert: #dc2626;
  --color-alert-light: #fee2e2;

  /* ==========================================================================
     PERFORMANCE SCALE (for data visualization)
     ========================================================================== */
  --color-perf-excellent: #059669;      /* >= 90% */
  --color-perf-excellent-bg: #d1fae5;
  --color-perf-good: #0ea5e9;           /* >= 80% */
  --color-perf-good-bg: #e0f2fe;
  --color-perf-moderate: #f59e0b;       /* >= 50% */
  --color-perf-moderate-bg: #fef3c7;
  --color-perf-poor: #dc2626;           /* < 50% */
  --color-perf-poor-bg: #fee2e2;

  /* ==========================================================================
     CHART COLOR PALETTE (sequential for multi-series)
     ========================================================================== */
  --chart-color-1: #045ea8;
  --chart-color-2: #0891b2;
  --chart-color-3: #0d9488;
  --chart-color-4: #059669;
  --chart-color-5: #65a30d;
  --chart-color-6: #ca8a04;
  --chart-color-7: #ea580c;
  --chart-color-8: #dc2626;

  /* ==========================================================================
     UI COLORS
     ========================================================================== */
  --color-bg: #f8fafc;
  --color-bg-soft: #f1f5f9;
  --color-bg-card: #ffffff;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #94a3b8;

  /* ==========================================================================
     SPACING SCALE (8px base)
     ========================================================================== */
  --spacing-xs: 0.25rem;   /* 4px */
  --spacing-sm: 0.5rem;    /* 8px */
  --spacing-md: 1rem;      /* 16px */
  --spacing-lg: 1.5rem;    /* 24px */
  --spacing-xl: 2rem;      /* 32px */
  --spacing-2xl: 3rem;     /* 48px */
  --spacing-3xl: 4rem;     /* 64px */

  /* ==========================================================================
     BORDER RADIUS
     ========================================================================== */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* ==========================================================================
     SHADOWS
     ========================================================================== */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);

  /* ==========================================================================
     TRANSITIONS
     ========================================================================== */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 350ms ease;

  /* ==========================================================================
     Z-INDEX SCALE
     ========================================================================== */
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal: 300;
  --z-tooltip: 400;
}
```

### 1.3 Create Theme Configuration Module

**File**: `src/theme.ts` (CREATE NEW)

```typescript
/**
 * Theme configuration module
 * Centralizes all design tokens for use in TypeScript/JavaScript
 */

export const COLORS = {
  // Brand
  primary: '#045ea8',
  primaryHover: '#034a85',
  primaryLight: '#e8f4fc',
  secondary: '#00458c',
  accent: '#f36f21',
  accentHover: '#d85d15',
  alert: '#dc2626',
  alertLight: '#fee2e2',

  // Performance scale
  performance: {
    excellent: '#059669',
    excellentBg: '#d1fae5',
    good: '#0ea5e9',
    goodBg: '#e0f2fe',
    moderate: '#f59e0b',
    moderateBg: '#fef3c7',
    poor: '#dc2626',
    poorBg: '#fee2e2',
  },

  // Chart palette
  chartPalette: [
    '#045ea8', '#0891b2', '#0d9488', '#059669',
    '#65a30d', '#ca8a04', '#ea580c', '#dc2626'
  ],

  // UI
  ui: {
    bg: '#f8fafc',
    bgSoft: '#f1f5f9',
    bgCard: '#ffffff',
    border: '#e2e8f0',
    borderStrong: '#cbd5e1',
    text: '#0f172a',
    textSecondary: '#475569',
    textMuted: '#94a3b8',
  }
} as const;

export const FONTS = {
  display: "'DM Serif Display', Georgia, serif",
  body: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const FONT_SIZES = {
  xs: '0.64rem',    // 10.24px
  sm: '0.8rem',     // 12.8px
  base: '1rem',     // 16px
  lg: '1.25rem',    // 20px
  xl: '1.563rem',   // 25px
  '2xl': '1.953rem', // 31.25px
  '3xl': '2.441rem', // 39px
  '4xl': '3.052rem', // 48.8px
} as const;

/**
 * Get performance color based on percentage value
 */
export function getPerformanceColor(value: number): string {
  if (value >= 90) return COLORS.performance.excellent;
  if (value >= 80) return COLORS.performance.good;
  if (value >= 50) return COLORS.performance.moderate;
  return COLORS.performance.poor;
}

/**
 * Get performance background color based on percentage value
 */
export function getPerformanceBgColor(value: number): string {
  if (value >= 90) return COLORS.performance.excellentBg;
  if (value >= 80) return COLORS.performance.goodBg;
  if (value >= 50) return COLORS.performance.moderateBg;
  return COLORS.performance.poorBg;
}

/**
 * Check if user prefers dark mode
 */
export function prefersDarkMode(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}
```

---

## Phase 2: Typography System

### 2.1 Add Google Fonts

**File**: `docs/index.html`

**Add to `<head>` section (before other stylesheets):**

```html
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### 2.2 Typography CSS

**File**: `docs/style.css`

**Add typography section:**

```css
/* ==========================================================================
   TYPOGRAPHY
   ========================================================================== */

:root {
  /* Font Families */
  --font-display: 'DM Serif Display', Georgia, serif;
  --font-body: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Type Scale (1.25 ratio) */
  --text-xs: 0.64rem;
  --text-sm: 0.8rem;
  --text-base: 1rem;
  --text-lg: 1.25rem;
  --text-xl: 1.563rem;
  --text-2xl: 1.953rem;
  --text-3xl: 2.441rem;
  --text-4xl: 3.052rem;

  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Headings */
h1, .h1 {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 400;
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin: 0 0 var(--spacing-md);
}

h2, .h2 {
  font-family: var(--font-body);
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin: 0 0 var(--spacing-md);
}

h3, .h3 {
  font-family: var(--font-body);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin: 0 0 var(--spacing-sm);
}

h4, .h4 {
  font-family: var(--font-body);
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin: 0 0 var(--spacing-sm);
}

/* Body text variants */
.text-lg { font-size: var(--text-lg); }
.text-sm { font-size: var(--text-sm); }
.text-xs { font-size: var(--text-xs); }

/* Monospace for data */
.font-mono {
  font-family: var(--font-mono);
}

/* Data values (large numbers) */
.data-value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1;
}

.data-value--lg {
  font-size: var(--text-3xl);
}

/* Labels */
.label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}
```

---

## Phase 3: Plotly Chart Improvements

### 3.1 Create Chart Configuration Module

**File**: `src/chart-config.ts` (CREATE NEW)

```typescript
/**
 * Unified Plotly chart configuration
 * All chart styling should reference this module
 */

import { COLORS, FONTS, getPerformanceColor } from './theme';

// Detect dark mode for dynamic theming
const isDarkMode = () => window.matchMedia('(prefers-color-scheme: dark)').matches;

/**
 * Base layout configuration shared by all charts
 */
export function getBaseLayout() {
  const dark = isDarkMode();

  return {
    font: {
      family: FONTS.body,
      size: 13,
      color: dark ? '#f1f5f9' : COLORS.ui.text,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 40, r: 24, b: 60, l: 60 },
    hoverlabel: {
      bgcolor: dark ? '#1e293b' : '#ffffff',
      bordercolor: dark ? '#334155' : COLORS.ui.border,
      font: {
        family: FONTS.body,
        size: 12,
        color: dark ? '#f1f5f9' : COLORS.ui.text,
      },
    },
    xaxis: {
      gridcolor: dark ? '#334155' : '#e5e7eb',
      gridwidth: 1,
      zerolinecolor: dark ? '#475569' : '#d1d5db',
      linecolor: dark ? '#475569' : '#d1d5db',
      tickfont: {
        size: 11,
        family: FONTS.body,
        color: dark ? '#94a3b8' : COLORS.ui.textSecondary,
      },
    },
    yaxis: {
      gridcolor: dark ? '#334155' : '#e5e7eb',
      gridwidth: 1,
      zerolinecolor: dark ? '#475569' : '#d1d5db',
      linecolor: dark ? '#475569' : '#d1d5db',
      tickfont: {
        size: 11,
        family: FONTS.body,
        color: dark ? '#94a3b8' : COLORS.ui.textSecondary,
      },
    },
  };
}

/**
 * Standard Plotly config (toolbar, interaction settings)
 */
export const PLOTLY_CONFIG = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: [
    'select2d',
    'lasso2d',
    'autoScale2d',
    'hoverClosestCartesian',
    'hoverCompareCartesian',
  ],
  toImageButtonOptions: {
    format: 'png',
    filename: 'chart',
    height: 600,
    width: 1000,
    scale: 2,
  },
};

/**
 * Overall bar chart configuration
 */
export function getOverallBarConfig(labels: string[], values: number[], n: number) {
  const baseLayout = getBaseLayout();

  const trace = {
    type: 'bar' as const,
    x: labels,
    y: values,
    marker: {
      color: values.map(v => getPerformanceColor(v)),
      line: { width: 0 },
    },
    text: values.map(v => `${v.toFixed(0)}%`),
    textposition: 'inside' as const,
    textangle: 0,
    textfont: {
      family: FONTS.mono,
      size: 13,
      color: '#ffffff',
    },
    hovertemplate: '<b>%{x}</b><br>%{y:.1f}%<extra></extra>',
    customdata: Array(labels.length).fill(n),
  };

  const layout = {
    ...baseLayout,
    bargap: 0.25,
    xaxis: {
      ...baseLayout.xaxis,
      tickangle: labels.some(l => l.length > 15) ? -35 : 0,
      categoryorder: 'total descending' as const,
    },
    yaxis: {
      ...baseLayout.yaxis,
      range: [0, 105],
      ticksuffix: '%',
      dtick: 20,
    },
    margin: { t: 20, r: 20, b: 100, l: 50 },
  };

  return { trace, layout };
}

/**
 * Weekly trend chart configuration with control limits
 */
export function getWeeklyTrendConfig(
  dates: string[],
  values: (number | null)[],
  fullDates: string[],
  centerLine?: number,
  ucl?: (number | null)[],
  lcl?: (number | null)[]
) {
  const baseLayout = getBaseLayout();
  const traces = [];

  // Control band (filled area between UCL and LCL)
  if (ucl && lcl) {
    const validIndices = ucl.map((u, i) => u !== null && lcl[i] !== null);
    const bandX = [...dates.filter((_, i) => validIndices[i]), ...dates.filter((_, i) => validIndices[i]).reverse()];
    const bandY = [
      ...ucl.filter((_, i) => validIndices[i]),
      ...(lcl.filter((_, i) => validIndices[i]) as number[]).reverse()
    ];

    traces.push({
      type: 'scatter' as const,
      mode: 'none' as const,
      fill: 'toself' as const,
      fillcolor: 'rgba(156, 163, 175, 0.12)',
      x: bandX,
      y: bandY,
      hoverinfo: 'skip' as const,
      showlegend: false,
      name: 'Control Band',
    });
  }

  // Center line
  if (centerLine !== undefined) {
    traces.push({
      type: 'scatter' as const,
      mode: 'lines' as const,
      x: dates,
      y: Array(dates.length).fill(centerLine),
      line: {
        color: 'rgba(107, 114, 128, 0.5)',
        width: 1,
        dash: 'dot' as const,
      },
      hoverinfo: 'skip' as const,
      showlegend: true,
      name: `Center Line (${centerLine.toFixed(1)}%)`,
    });
  }

  // Main data line
  traces.push({
    type: 'scatter' as const,
    mode: 'lines+markers' as const,
    x: dates,
    y: values,
    text: fullDates,
    line: {
      color: COLORS.primary,
      width: 3,
      shape: 'spline' as const,
    },
    marker: {
      size: 10,
      color: COLORS.primary,
      line: { color: '#ffffff', width: 2 },
    },
    connectgaps: true,
    hovertemplate: '<b>Week of %{text}</b><br>%{y:.1f}%<extra></extra>',
    showlegend: true,
    name: 'Weekly Average',
  });

  const layout = {
    ...baseLayout,
    showlegend: true,
    legend: {
      orientation: 'h' as const,
      yanchor: 'bottom' as const,
      y: 1.02,
      xanchor: 'right' as const,
      x: 1,
      font: { size: 11 },
    },
    xaxis: {
      ...baseLayout.xaxis,
      tickangle: -45,
    },
    yaxis: {
      ...baseLayout.yaxis,
      range: [0, 105],
      ticksuffix: '%',
      dtick: 20,
    },
    margin: { t: 50, r: 20, b: 80, l: 50 },
  };

  return { traces, layout };
}

/**
 * Heatmap configuration
 */
export function getHeatmapConfig(
  zValues: number[][],
  xLabels: string[],
  yLabels: string[],
  hoverText: string[][]
) {
  const baseLayout = getBaseLayout();

  const trace = {
    type: 'heatmap' as const,
    z: zValues,
    x: xLabels,
    y: yLabels,
    colorscale: [
      [0, '#fecaca'],      // Red-200 (0%)
      [0.3, '#fed7aa'],    // Orange-200 (30%)
      [0.5, '#fef08a'],    // Yellow-200 (50%)
      [0.7, '#bbf7d0'],    // Green-200 (70%)
      [1, '#86efac'],      // Green-300 (100%)
    ],
    colorbar: {
      title: { text: 'Score', side: 'right' as const, font: { size: 11 } },
      ticksuffix: '%',
      thickness: 15,
      outlinewidth: 0,
      tickfont: { size: 10 },
      len: 0.8,
    },
    xgap: 2,
    ygap: 2,
    hovertemplate: '%{text}<extra></extra>',
    text: hoverText,
    texttemplate: '%{z:.0f}',
    textfont: {
      size: 11,
      family: FONTS.mono,
      color: '#374151',
    },
    showscale: true,
  };

  // Dynamic height based on number of rows
  const height = Math.max(400, yLabels.length * 40 + 120);

  const layout = {
    ...baseLayout,
    height,
    xaxis: {
      ...baseLayout.xaxis,
      side: 'top' as const,
      tickangle: -45,
    },
    yaxis: {
      ...baseLayout.yaxis,
      autorange: 'reversed' as const,
      tickfont: { size: 11 },
    },
    margin: { t: 100, r: 80, b: 20, l: 120 },
  };

  return { trace, layout };
}

/**
 * Per-newscast horizontal bar chart configuration
 */
export function getPerNewscastBarConfig(
  newscast: string,
  labels: string[],
  values: number[],
  n: number
) {
  const baseLayout = getBaseLayout();

  const trace = {
    type: 'bar' as const,
    orientation: 'h' as const,
    y: labels,
    x: values,
    marker: {
      color: values.map(v => getPerformanceColor(v)),
      line: { width: 0 },
    },
    text: values.map(v => `${v.toFixed(0)}%`),
    textposition: 'inside' as const,
    textfont: {
      family: FONTS.mono,
      size: 11,
      color: '#ffffff',
    },
    hovertemplate: '<b>%{y}</b><br>%{x:.1f}%<extra></extra>',
  };

  const layout = {
    ...baseLayout,
    title: {
      text: `${newscast} (n=${n})`,
      font: { size: 14, family: FONTS.body },
      x: 0,
      xanchor: 'left' as const,
    },
    bargap: 0.2,
    xaxis: {
      ...baseLayout.xaxis,
      range: [0, 105],
      ticksuffix: '%',
      dtick: 25,
    },
    yaxis: {
      ...baseLayout.yaxis,
      automargin: true,
    },
    margin: { t: 40, r: 20, b: 40, l: 150 },
    height: Math.max(200, labels.length * 35 + 80),
  };

  return { trace, layout };
}

/**
 * Animation configuration for chart updates
 */
export const ANIMATION_CONFIG = {
  transition: {
    duration: 500,
    easing: 'cubic-in-out' as const,
  },
  frame: {
    duration: 500,
    redraw: false,
  },
};
```

### 3.2 Update ChartRenderer Class

**File**: `src/chart-renderer.ts`

**Key changes to make:**

1. Import the new chart config module
2. Replace hardcoded colors with theme colors
3. Use the config functions for each chart type
4. Add animation support for chart updates

```typescript
// Add to imports at top of file
import {
  getBaseLayout,
  getOverallBarConfig,
  getWeeklyTrendConfig,
  getHeatmapConfig,
  getPerNewscastBarConfig,
  PLOTLY_CONFIG,
  ANIMATION_CONFIG,
} from './chart-config';
import { COLORS, FONTS } from './theme';

// Example: Update renderOverallChart method
renderOverallChart(data: ChartData): void {
  const container = document.getElementById('chart-overall');
  if (!container) return;

  const { trace, layout } = getOverallBarConfig(data.labels, data.values, data.n);

  Plotly.react(container, [trace], layout, PLOTLY_CONFIG);
}

// Example: Update renderWeeklyChart method
renderWeeklyChart(data: WeeklyChart): void {
  const container = document.getElementById('chart-weekly');
  if (!container) return;

  const { traces, layout } = getWeeklyTrendConfig(
    data.dates,
    data.values,
    data.full_dates,
    data.center_line,
    data.ucl,
    data.lcl
  );

  Plotly.react(container, traces, layout, PLOTLY_CONFIG);
}
```

### 3.3 Chart Design Best Practices Reference

| Practice | Implementation |
|----------|----------------|
| **Consistent fonts** | Use `FONTS.body` for labels, `FONTS.mono` for values |
| **Performance colors** | Use `getPerformanceColor()` function |
| **Transparent backgrounds** | Set `paper_bgcolor` and `plot_bgcolor` to `'rgba(0,0,0,0)'` |
| **Responsive sizing** | Set `responsive: true` in config |
| **Clear hover info** | Use `hovertemplate` with `<extra></extra>` to hide trace name |
| **Grid styling** | Light gray grids, no heavy borders |
| **Value labels** | Inside bars for bars >20%, outside for smaller |
| **Animation** | Use `Plotly.react()` with animation config for updates |

---

## Phase 4: Data Representation

### 4.1 Table Styling Improvements

**File**: `docs/style.css`

**Add/update table styles:**

```css
/* ==========================================================================
   DATA TABLES
   ========================================================================== */

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.data-table thead {
  background: var(--color-bg-soft);
  border-bottom: 2px solid var(--color-border-strong);
}

.data-table th {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-weight: 600;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.data-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

/* Right-align numeric columns */
.data-table td:nth-child(n+2),
.data-table th:nth-child(n+2) {
  text-align: right;
  font-family: var(--font-mono);
}

/* First column (labels) stays left */
.data-table td:first-child,
.data-table th:first-child {
  text-align: left;
  font-family: var(--font-body);
}

/* Subtle row striping */
.data-table tbody tr:nth-child(even) {
  background: var(--color-bg);
}

/* Hover state */
.data-table tbody tr {
  transition: background-color var(--transition-fast);
}

.data-table tbody tr:hover {
  background: var(--color-primary-light);
}

/* Performance indicator cells */
.cell-excellent {
  background: var(--color-perf-excellent-bg) !important;
  color: #065f46;
}

.cell-good {
  background: var(--color-perf-good-bg) !important;
  color: #0c4a6e;
}

.cell-moderate {
  background: var(--color-perf-moderate-bg) !important;
  color: #78350f;
}

.cell-poor {
  background: var(--color-perf-poor-bg) !important;
  color: #7f1d1d;
}
```

### 4.2 Metric Cards Component

**File**: `docs/style.css`

**Add metric cards styles:**

```css
/* ==========================================================================
   METRIC CARDS
   ========================================================================== */

.metric-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.metric-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
  transition: transform var(--transition-normal), box-shadow var(--transition-normal);
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* Top accent bar */
.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--color-primary);
}

.metric-card--accent::before {
  background: var(--color-accent);
}

.metric-card--success::before {
  background: var(--color-perf-excellent);
}

.metric-card--warning::before {
  background: var(--color-perf-moderate);
}

.metric-value {
  font-family: var(--font-mono);
  font-size: var(--text-3xl);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1;
  margin-bottom: var(--spacing-xs);
}

.metric-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.metric-trend {
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.metric-trend--up {
  color: var(--color-perf-excellent);
}

.metric-trend--down {
  color: var(--color-perf-poor);
}

.metric-trend--neutral {
  color: var(--color-text-muted);
}

/* Trend arrow icons (using CSS) */
.metric-trend--up::before {
  content: '↑';
  font-weight: bold;
}

.metric-trend--down::before {
  content: '↓';
  font-weight: bold;
}

.metric-trend--neutral::before {
  content: '→';
}
```

### 4.3 Update HTML for Metric Cards

**File**: `docs/index.html`

**Replace summary bar with metric cards:**

```html
<!-- Replace existing summary-bar div with: -->
<div class="metric-cards" id="metric-cards">
  <div class="metric-card">
    <div class="metric-label">Total Audits</div>
    <div class="metric-value" id="metric-total">--</div>
    <div class="metric-trend metric-trend--neutral" id="metric-total-trend"></div>
  </div>
  <div class="metric-card metric-card--success">
    <div class="metric-label">Overall Score</div>
    <div class="metric-value" id="metric-score">--%</div>
    <div class="metric-trend" id="metric-score-trend"></div>
  </div>
  <div class="metric-card metric-card--accent">
    <div class="metric-label">Date Range</div>
    <div class="metric-value" id="metric-range" style="font-size: var(--text-lg);">--</div>
    <div class="metric-trend metric-trend--neutral" id="metric-range-weeks"></div>
  </div>
</div>
```

---

## Phase 5: Interactions & Motion

### 5.1 Page Load Animations

**File**: `docs/style.css`

```css
/* ==========================================================================
   ANIMATIONS
   ========================================================================== */

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Staggered animation for results sections */
.results-section.animate > * {
  animation: fadeInUp 0.5s ease-out backwards;
}

.results-section.animate > *:nth-child(1) { animation-delay: 0ms; }
.results-section.animate > *:nth-child(2) { animation-delay: 60ms; }
.results-section.animate > *:nth-child(3) { animation-delay: 120ms; }
.results-section.animate > *:nth-child(4) { animation-delay: 180ms; }
.results-section.animate > *:nth-child(5) { animation-delay: 240ms; }
.results-section.animate > *:nth-child(6) { animation-delay: 300ms; }
.results-section.animate > *:nth-child(7) { animation-delay: 360ms; }
.results-section.animate > *:nth-child(8) { animation-delay: 420ms; }

/* Card animations */
.card {
  animation: scaleIn 0.3s ease-out;
}

/* Chart container fade in */
.chart-container {
  animation: fadeIn 0.4s ease-out;
}
```

### 5.2 Add Animation Trigger in JavaScript

**File**: `src/app.ts`

**Add to the `showResults()` or similar method:**

```typescript
// When showing results, add animate class
private showResults(): void {
  const resultsSection = document.getElementById('results-section');
  if (resultsSection) {
    resultsSection.classList.remove('d-none');
    // Trigger animation
    resultsSection.classList.add('animate');
  }
}
```

### 5.3 Interactive States

**File**: `docs/style.css`

```css
/* ==========================================================================
   INTERACTIVE STATES
   ========================================================================== */

/* Buttons */
.btn {
  transition:
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    transform var(--transition-fast),
    box-shadow var(--transition-fast);
}

.btn:hover {
  transform: translateY(-1px);
}

.btn:active {
  transform: translateY(0);
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

/* Cards */
.card {
  transition:
    transform var(--transition-normal),
    box-shadow var(--transition-normal);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}

.card--interactive:hover {
  transform: translateY(-2px);
}

/* Links */
a {
  transition: color var(--transition-fast);
}

/* Form elements */
input, select, textarea {
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

input:focus, select:focus, textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  outline: none;
}

/* Upload dropzone */
.upload-box {
  transition:
    border-color var(--transition-fast),
    background-color var(--transition-fast),
    transform var(--transition-fast);
}

.upload-box:hover,
.upload-box.dragover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
  transform: scale(1.01);
}
```

---

## Phase 6: Layout Improvements

### 6.1 Section Headers

**File**: `docs/style.css`

```css
/* ==========================================================================
   SECTION HEADERS
   ========================================================================== */

.section-header {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.section-title {
  font-family: var(--font-body);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.section-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin: var(--spacing-xs) 0 0;
}

/* Section with icon */
.section-header--with-icon {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-md);
  font-size: var(--text-lg);
}
```

### 6.2 Results Grid Layout

**File**: `docs/style.css`

```css
/* ==========================================================================
   RESULTS GRID
   ========================================================================== */

.results-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--spacing-lg);
}

/* Full width */
.col-12 { grid-column: span 12; }

/* Two-thirds / one-third */
.col-8 { grid-column: span 8; }
.col-4 { grid-column: span 4; }

/* Half */
.col-6 { grid-column: span 6; }

/* One-third */
.col-3 { grid-column: span 3; }

/* Responsive */
@media (max-width: 1024px) {
  .col-8, .col-4, .col-6, .col-3 {
    grid-column: span 12;
  }
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
}
```

### 6.3 Card Component

**File**: `docs/style.css`

```css
/* ==========================================================================
   CARDS
   ========================================================================== */

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.card-header-title {
  font-size: var(--text-base);
  font-weight: 600;
  margin: 0;
}

.card-body {
  padding: var(--spacing-lg);
}

.card-footer {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg);
}

/* Compact card variant */
.card--compact .card-body {
  padding: var(--spacing-md);
}

/* Borderless card */
.card--flat {
  box-shadow: none;
  border: 1px solid var(--color-border);
}
```

---

## Phase 7: Dark Mode

### 7.1 Dark Mode CSS Variables

**File**: `docs/style.css`

**Add at end of file:**

```css
/* ==========================================================================
   DARK MODE
   ========================================================================== */

@media (prefers-color-scheme: dark) {
  :root {
    /* Background colors */
    --color-bg: #0f172a;
    --color-bg-soft: #1e293b;
    --color-bg-card: #1e293b;

    /* Border colors */
    --color-border: #334155;
    --color-border-strong: #475569;

    /* Text colors */
    --color-text: #f1f5f9;
    --color-text-secondary: #94a3b8;
    --color-text-muted: #64748b;

    /* Brand colors (slightly adjusted for dark) */
    --color-primary: #3b82f6;
    --color-primary-hover: #2563eb;
    --color-primary-light: rgba(59, 130, 246, 0.15);

    /* Shadows (darker, more subtle) */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5), 0 4px 6px -4px rgb(0 0 0 / 0.4);

    /* Performance colors (keep similar but slightly muted) */
    --color-perf-excellent: #10b981;
    --color-perf-excellent-bg: rgba(16, 185, 129, 0.15);
    --color-perf-good: #0ea5e9;
    --color-perf-good-bg: rgba(14, 165, 233, 0.15);
    --color-perf-moderate: #f59e0b;
    --color-perf-moderate-bg: rgba(245, 158, 11, 0.15);
    --color-perf-poor: #ef4444;
    --color-perf-poor-bg: rgba(239, 68, 68, 0.15);
  }

  /* Body background */
  body {
    background-color: var(--color-bg);
  }

  /* Header adjustments */
  .header {
    background: #0a0a0a;
    border-bottom: 1px solid var(--color-border);
  }

  /* Card borders for better definition */
  .card {
    border: 1px solid var(--color-border);
  }

  /* Table adjustments */
  .data-table thead {
    background: var(--color-bg);
  }

  .data-table tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }

  .data-table tbody tr:hover {
    background: rgba(59, 130, 246, 0.1);
  }

  /* Form elements */
  input, select, textarea {
    background: var(--color-bg);
    border-color: var(--color-border);
    color: var(--color-text);
  }

  /* Upload box */
  .upload-box {
    background: var(--color-bg-soft);
    border-color: var(--color-border);
  }

  .upload-box:hover,
  .upload-box.dragover {
    background: var(--color-primary-light);
  }

  /* Performance cells in dark mode */
  .cell-excellent {
    background: var(--color-perf-excellent-bg) !important;
    color: #34d399;
  }

  .cell-good {
    background: var(--color-perf-good-bg) !important;
    color: #38bdf8;
  }

  .cell-moderate {
    background: var(--color-perf-moderate-bg) !important;
    color: #fbbf24;
  }

  .cell-poor {
    background: var(--color-perf-poor-bg) !important;
    color: #f87171;
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: var(--color-bg);
  }

  ::-webkit-scrollbar-thumb {
    background: var(--color-border);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-strong);
  }
}
```

### 7.2 Dynamic Chart Theme Support

**File**: `src/theme.ts`

**Add dark mode listener:**

```typescript
/**
 * Listen for dark mode changes and trigger callback
 */
export function onThemeChange(callback: (isDark: boolean) => void): void {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  // Initial call
  callback(mediaQuery.matches);

  // Listen for changes
  mediaQuery.addEventListener('change', (e) => {
    callback(e.matches);
  });
}
```

**File**: `src/app.ts`

**Add theme change handler:**

```typescript
import { onThemeChange } from './theme';

// In initialization
onThemeChange((isDark) => {
  // Re-render charts with new theme
  if (this.currentData) {
    this.chartRenderer.renderAllCharts(this.currentData);
  }
});
```

---

## Implementation Checklist

### Phase 1: Foundation (Priority: Critical)
- [ ] Add utility CSS classes to `docs/style.css`
- [ ] Update CSS variables in `:root` selector
- [ ] Create `src/theme.ts` module
- [ ] Test that all Bootstrap class references now work

### Phase 2: Typography (Priority: High)
- [ ] Add Google Fonts link to `docs/index.html`
- [ ] Add typography CSS rules
- [ ] Update existing elements to use new typography classes
- [ ] Verify font loading and fallbacks

### Phase 3: Charts (Priority: High)
- [ ] Create `src/chart-config.ts` module
- [ ] Update `src/chart-renderer.ts` to use new config
- [ ] Test all four chart types with new styling
- [ ] Verify responsive behavior
- [ ] Test chart animations on data update

### Phase 4: Data Representation (Priority: Medium)
- [ ] Update table styling in CSS
- [ ] Update `src/table-renderer.ts` for new classes
- [ ] Create metric cards HTML structure
- [ ] Wire up metric cards to data
- [ ] Test performance color coding

### Phase 5: Interactions (Priority: Medium)
- [ ] Add animation keyframes to CSS
- [ ] Add animation classes to HTML/JS
- [ ] Update interactive states (hover, focus)
- [ ] Test page load animations
- [ ] Verify no animation jank

### Phase 6: Layout (Priority: Medium)
- [ ] Add section header component
- [ ] Implement results grid system
- [ ] Update card component styling
- [ ] Test responsive breakpoints
- [ ] Verify print styles still work

### Phase 7: Dark Mode (Priority: Low)
- [ ] Add dark mode CSS variables
- [ ] Test all components in dark mode
- [ ] Add theme change listener for charts
- [ ] Verify color contrast (WCAG AA)
- [ ] Test dark mode transitions

---

## File Reference

### Files to Create

| File | Purpose |
|------|---------|
| `src/theme.ts` | Centralized theme configuration and utilities |
| `src/chart-config.ts` | Plotly chart configuration module |

### Files to Modify

| File | Changes |
|------|---------|
| `docs/index.html` | Add Google Fonts, update metric cards HTML |
| `docs/style.css` | Add utility classes, typography, animations, dark mode |
| `src/chart-renderer.ts` | Use new chart config module |
| `src/table-renderer.ts` | Use new performance color classes |
| `src/app.ts` | Add animation triggers, theme change handler |

### Files to Review (No Changes Required)

| File | Notes |
|------|-------|
| `docs/error-ui.css` | Already has dark mode support |
| `src/data-exporter.ts` | May need chart theme for export |
| `src/pyodide-service.ts` | No UI changes needed |

---

## Testing Checklist

### Visual Testing
- [ ] All charts render correctly
- [ ] Tables display with proper alignment
- [ ] Metric cards show correct values
- [ ] Animations play smoothly
- [ ] Dark mode looks correct
- [ ] Print preview shows clean output

### Functional Testing
- [ ] File upload still works
- [ ] Date slider filters correctly
- [ ] Export to Excel works
- [ ] Export to PowerPoint works
- [ ] Comments search works
- [ ] All interactive elements respond

### Responsive Testing
- [ ] Desktop (1920px+)
- [ ] Laptop (1024-1919px)
- [ ] Tablet (768-1023px)
- [ ] Mobile (320-767px)

### Accessibility Testing
- [ ] Color contrast ratios pass WCAG AA
- [ ] Focus states are visible
- [ ] Screen reader announces content
- [ ] Keyboard navigation works

---

## Notes for Implementer

1. **Start with Phase 1** - The Bootstrap class conflicts are breaking existing UI
2. **Test incrementally** - After each phase, verify nothing is broken
3. **Use browser DevTools** - Dark mode can be forced in DevTools for testing
4. **Check Plotly docs** - https://plotly.com/javascript/ for any chart config questions
5. **Preserve functionality** - Don't break existing features while improving UI
6. **Commit after each phase** - Makes it easier to revert if issues arise

---

*Document created by Claude Code - January 2025*
