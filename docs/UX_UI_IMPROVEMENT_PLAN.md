# Newscast Audit — UX/UI Improvement Plan v2.0

> **Document Version**: 2.0
> **Updated**: January 2025
> **Status**: Completed (All Phases 1-5 & Fixes Implemented)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Implementation Status](#implementation-status)
3. [TEGNA Brand Guidelines](#tegna-brand-guidelines)
4. [Known Issues & Fixes](#known-issues--fixes)
5. [Remaining Work: Phase 5](#remaining-work-phase-5)
6. [File Reference](#file-reference)
7. [Implementation Checklist](#implementation-checklist)

---

## Executive Summary

### What This App Does

The Newscast Audit application is a browser-based survey analysis tool for analyzing newscast quality audit data exported from Microsoft Forms. It runs entirely in the browser using Pyodide (Python via WebAssembly) and generates interactive reports with Plotly charts.

### Current State

**Substantially Complete.** The major UX/UI improvements have been implemented:
- ✅ Centralized design system (CSS variables, theme.ts)
- ✅ Typography system with Google Fonts
- ✅ Unified Plotly chart configuration
- ✅ Performance-based color coding
- ✅ Responsive layouts
- ✅ Bootstrap-compatible utility classes

### What Remains

3. **Cleanup**: Unused dark mode CSS removed

---

## Implementation Status

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| **1** | CSS Variables | ✅ Done | All design tokens defined |
| **1** | Utility Classes | ✅ Done | Bootstrap-compatible classes |
| **1** | theme.ts Module | ✅ Done | TEGNA branding applied |
| **2** | Google Fonts | ✅ Done | DM Serif, Plus Jakarta Sans, JetBrains Mono |
| **2** | Typography CSS | ✅ Done | Type scale, headings, data values |
| **3** | chart-config.ts | ✅ Done | All 4 chart types unified |
| **3** | ChartRenderer.ts | ✅ Done | Uses new config system |
| **4** | Table Styling | ✅ Done | Performance cells, alignment |
| **4** | Metric Cards | ✅ Done | Summary metrics display |
| **5** | Animations | ✅ Done | Staggered entry animations applied |
| **5** | Interactions | ✅ Done | Enhanced hover states & micro-interactions |
| **6** | Layout/Grid | ✅ Done | Responsive grid system |
| **7** | Dark Mode | ❌ Removed | Code cleanup complete |

---

## TEGNA Brand Guidelines

### Official Colors

Based on TEGNA's visual identity:

| Color | Hex | Usage |
|-------|-----|-------|
| **TEGNA Orange** | `#FF5F00` | Primary actions, CTAs, highlights |
| **TEGNA Navy** | `#010a48` | Headers, text, secondary elements |
| **Medium Blue** | `#00458c` | Accents, links |
| **Light Orange** | `#fb923c` | Secondary highlights |

### Current Implementation (theme.ts)

```typescript
export const COLORS = {
    primary: '#FF5F00',     // TEGNA Orange
    primaryHover: '#CC4C00',
    primaryLight: '#FFF0E5',
    secondary: '#010a48',   // TEGNA Navy
    header: '#010a48',
    // ... rest of theme
}
```

### Typography

| Role | Font | Weight |
|------|------|--------|
| Display/Headings | DM Serif Display | 400 |
| Body/UI | Plus Jakarta Sans | 400, 500, 600, 700 |
| Data/Monospace | JetBrains Mono | 400, 500 |

### Performance Color Scale

| Range | Color | Hex |
|-------|-------|-----|
| ≥90% Excellent | Green | `#059669` |
| ≥80% Good | Blue | `#0ea5e9` |
| ≥50% Moderate | Amber | `#f59e0b` |
| <50% Poor | Red | `#dc2626` |

---

## Known Issues & Fixes

### Issue 1: 5-7am Chart Scaling Problem

**Symptoms**: The "5 - 7 am" per-newscast chart may display incorrectly - either clipped, scaled wrong, or with layout issues.

**Root Cause Analysis**:

The per-newscast horizontal bar charts have a large left margin (250px) for Y-axis labels. Combined with CSS `overflow: hidden` on containers, this can cause:
1. Chart content being clipped
2. Plotly auto-scaling incorrectly
3. Labels being cut off

**Current Configuration** (chart-config.ts line 363):
```typescript
margin: { t: 40, r: 60, b: 40, l: 250 },
```

**Current CSS** (style.css lines 888-894):
```css
.chart-container {
    min-height: 400px;
    width: 100%;
    position: relative;
    overflow: hidden;  /* ← This clips chart overflow */
}
```

**Fix Options**:

#### Option A: Remove overflow hidden (Recommended)
```css
/* File: docs/css/style.css */
.chart-container {
    min-height: 400px;
    width: 100%;
    position: relative;
    /* Remove overflow: hidden to allow chart labels */
}

/* Add overflow control at parent level if needed */
.chart-card {
    overflow-x: auto;  /* Allow horizontal scroll if needed */
}
```

#### Option B: Use Plotly automargin
```typescript
/* File: docs/js/modules/chart-config.ts */
// In getPerNewscastBarConfig function, update yaxis:
yaxis: {
    ...baseLayout.yaxis,
    automargin: true,  // Already set, but ensure it's working
    tickfont: { size: 11 },
},
// And reduce fixed left margin:
margin: { t: 40, r: 60, b: 40, l: 120 },  // Reduced from 250
```

#### Option C: Dynamic margin based on label length
```typescript
/* File: docs/js/modules/chart-config.ts */
export function getPerNewscastBarConfig(
    newscast: string,
    labels: string[],
    values: number[],
    n: number
) {
    // Calculate margin based on longest label
    const maxLabelLength = Math.max(...labels.map(l => l.length));
    const leftMargin = Math.min(300, Math.max(150, maxLabelLength * 8));

    // ... rest of config
    margin: { t: 40, r: 60, b: 40, l: leftMargin },
}
```

**Recommended Fix**: Combine Option A + B

1. Remove `overflow: hidden` from `.chart-container`
2. Ensure `automargin: true` is set on yaxis
3. Add `overflow-x: auto` to `.chart-card` as safety net

---

### Issue 2: CSS Variable Mismatch

**Problem**: `style.css` defines `--chart-color-*` variables but `theme.ts` uses different values.

**CSS Variables** (style.css):
```css
--chart-color-1: #045ea8;  /* Different from theme.ts */
```

**theme.ts**:
```typescript
chartPalette: [
    '#001489', // Navy (Brand)
    '#FF5F00', // Orange (Primary)
    // ...
]
```

**Fix**: Sync CSS variables with theme.ts or remove unused CSS variables.

```css
/* Update in docs/css/style.css */
:root {
    --chart-color-1: #001489;
    --chart-color-2: #FF5F00;
    --chart-color-3: #00458c;
    --chart-color-4: #fb923c;
    --chart-color-5: #334155;
    --chart-color-6: #94a3b8;
    --chart-color-7: #0ea5e9;
    --chart-color-8: #dc2626;
}
```

---

### Issue 3: Unused Dark Mode CSS

**Problem**: ~100 lines of dark mode CSS exist but are never used (light mode enforced).

**Location**: `docs/css/style.css` - `@media (prefers-color-scheme: dark)` block

**Options**:
1. **Keep**: No harm, just unused code (~100 lines)
2. **Remove**: Cleaner codebase, smaller CSS file

**If Removing**: Delete the entire `@media (prefers-color-scheme: dark) { ... }` block from style.css.

---

## Remaining Work: Phase 5

### 5.1 Animation Refinements

The animation keyframes are defined but not consistently applied.

**Already Defined** (style.css):
```css
@keyframes fadeInUp { ... }
@keyframes fadeIn { ... }
@keyframes scaleIn { ... }
```

**Add These Trigger Classes**:

```css
/* File: docs/css/style.css - Add after existing animations */

/* Apply staggered animation when results appear */
.results-section.is-visible > .chart-card,
.results-section.is-visible > .table-card,
.results-section.is-visible > .metric-card {
    animation: fadeInUp 0.4s ease-out backwards;
}

.results-section.is-visible > *:nth-child(1) { animation-delay: 0ms; }
.results-section.is-visible > *:nth-child(2) { animation-delay: 50ms; }
.results-section.is-visible > *:nth-child(3) { animation-delay: 100ms; }
.results-section.is-visible > *:nth-child(4) { animation-delay: 150ms; }
.results-section.is-visible > *:nth-child(5) { animation-delay: 200ms; }
.results-section.is-visible > *:nth-child(6) { animation-delay: 250ms; }
```

**Add JavaScript Trigger**:

```typescript
/* File: docs/js/app.ts - In showResults() method */
private showResults(): void {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.classList.remove('d-none');
        // Trigger staggered animations
        requestAnimationFrame(() => {
            resultsSection.classList.add('is-visible');
        });
    }
}
```

### 5.2 Enhanced Hover States

**Add to style.css**:

```css
/* Enhanced card hover */
.chart-card,
.table-card {
    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

.chart-card:hover,
.table-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

/* Metric card emphasis on hover */
.metric-card {
    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        border-color 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
    border-color: var(--color-primary);
}

/* Table row highlight */
.data-table tbody tr {
    transition: background-color 0.15s ease;
}

.data-table tbody tr:hover {
    background-color: var(--color-primary-light);
}
```

### 5.3 Button Micro-interactions

**Add to style.css**:

```css
/* Button press effect */
.btn {
    transition:
        background-color 0.15s ease,
        transform 0.1s ease,
        box-shadow 0.15s ease;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
}

.btn:active {
    transform: translateY(0);
    box-shadow: none;
}

/* Primary button glow on hover */
.btn-primary:hover {
    box-shadow: 0 4px 12px rgba(255, 95, 0, 0.3);
}
```

### 5.4 Loading State Improvements

**Add to style.css**:

```css
/* Skeleton loading for charts */
.chart-loading {
    background: linear-gradient(
        90deg,
        var(--color-bg-soft) 25%,
        var(--color-bg) 50%,
        var(--color-bg-soft) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: var(--radius-md);
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* Pulse animation for loading indicator */
.loading-indicator {
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

---

## File Reference

### Files to Modify

| File | Changes Needed |
|------|----------------|
| `docs/css/style.css` | Fix overflow issue, sync chart colors, add Phase 5 CSS |
| `docs/js/modules/chart-config.ts` | Adjust per-newscast margin if needed |
| `docs/js/app.ts` | Add animation trigger class |

### Files Already Complete (No Changes Needed)

| File | Status |
|------|--------|
| `docs/index.html` | ✅ Google Fonts, semantic structure |
| `docs/js/modules/theme.ts` | ✅ TEGNA branding complete |
| `docs/js/modules/ChartRenderer.ts` | ✅ Uses unified config |

### Key Line References

| File | Lines | What |
|------|-------|------|
| `style.css` | 888-894 | `.chart-container` overflow issue |
| `style.css` | 903-911 | `.charts-grid` layout |
| `style.css` | 47-54 | Chart color CSS variables |
| `chart-config.ts` | 309-368 | Per-newscast bar config |
| `chart-config.ts` | 363 | Left margin setting (250px) |
| `theme.ts` | 31-40 | Chart palette definition |

---

## Implementation Checklist

### Priority 1: Bug Fixes (Do First)

- [ ] **Fix 5-7am chart overflow**
  - [ ] Remove `overflow: hidden` from `.chart-container` (line 892)
  - [ ] Add `overflow-x: auto` to `.chart-card` (line 867)
  - [ ] Test all per-newscast charts render correctly
  - [ ] Verify labels are not clipped

- [ ] **Sync chart colors**
  - [ ] Update CSS variables (lines 47-54) to match theme.ts
  - [ ] Or remove unused CSS chart color variables

### Priority 2: Phase 5 Polish (Optional but Recommended)

- [ ] **Staggered animations**
  - [ ] Add `.is-visible` CSS rules for results section
  - [ ] Add JavaScript to trigger animation class
  - [ ] Test animation timing feels natural

- [ ] **Hover states**
  - [ ] Add card hover effects (translateY, shadow)
  - [ ] Add table row hover highlight
  - [ ] Add button micro-interactions

- [ ] **Loading states**
  - [ ] Add shimmer/skeleton CSS
  - [ ] Apply to chart containers while loading

### Priority 3: Cleanup (Optional)

- [ ] **Remove dark mode CSS**
  - [ ] Delete `@media (prefers-color-scheme: dark)` block
  - [ ] Remove `prefersDarkMode()` function from theme.ts (or keep returning false)

- [ ] **Code comments**
  - [ ] Add section comments to style.css
  - [ ] Document any non-obvious CSS hacks

### Testing Checklist

After making changes:

- [ ] Upload a test Excel file
- [ ] Verify all 4 chart types render correctly
- [ ] Check "5 - 7 am" chart specifically
- [ ] Check other multi-hour charts (if any)
- [ ] Test responsive layout at 320px, 768px, 1024px, 1920px
- [ ] Verify animations play on results load
- [ ] Test hover states on cards, tables, buttons
- [ ] Export to Excel - verify works
- [ ] Export to PowerPoint - verify chart images

---

## Quick Start for New Session

If starting fresh, here's the fastest path to fixing the main issue:

### Step 1: Fix Chart Overflow (2 minutes)

Edit `docs/css/style.css`:

```css
/* Around line 888 - CHANGE THIS: */
.chart-container {
    min-height: 400px;
    width: 100%;
    position: relative;
    /* overflow: hidden; ← REMOVE THIS LINE */
}

/* Around line 867 - ADD overflow-x: */
.chart-card {
    background: var(--color-white);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    box-shadow: var(--shadow-sm);
    padding: var(--spacing-lg);
    overflow-x: auto;  /* ← ADD THIS LINE */
}
```

### Step 2: Test

1. Run `npm run build` (or the project's build command)
2. Open in browser
3. Upload test file
4. Check "5 - 7 am" chart renders correctly

### Step 3: If Still Broken

Check `docs/js/modules/chart-config.ts` line 363:
- Reduce left margin from 250 to 180 if labels are still clipped
- Ensure `automargin: true` is set on yaxis (line 360)

---

## Architecture Notes

### Data Flow

```
Excel File
    ↓
SheetJS (xlsx.js) - Parse
    ↓
Pyodide Worker (Python)
    ↓
ProcessingResult JSON
    ↓
TypeScript Renderers
    ├─ ChartRenderer → Plotly.js
    ├─ TableRenderer → DOM
    └─ CommentRenderer → DOM
```

### Chart Configuration Chain

```
theme.ts (colors, fonts)
    ↓
chart-config.ts (Plotly layouts)
    ↓
ChartRenderer.ts (rendering logic)
    ↓
Plotly.newPlot() → DOM
```

### Style Cascade

```
:root CSS Variables
    ↓
Component CSS (.chart-card, .data-table, etc.)
    ↓
Utility Classes (.d-flex, .mb-3, etc.)
    ↓
Inline Plotly Styles (layout config)
```

---

*Document updated January 2025 — v2.0*
*Previous version archived as UX_UI_IMPROVEMENT_PLAN_v1.md*
