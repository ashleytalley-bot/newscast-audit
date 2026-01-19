// @ts-check

/**
 * Chart configuration defaults
 */
export const CHART_DEFAULTS = {
    fonts: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        size: 12
    },
    margins: {
        overall: { b: 120, t: 60, l: 60, r: 20 },
        perNewscast: { l: 200, r: 60, t: 20, b: 50 }
    },
    axisRange: [0, 110],
    responsive: true
};

/**
 * User-facing loading messages
 */
export const LOADING_MESSAGES = {
    readingFile: 'Reading Excel file...',
    initPython: 'Initializing Python environment...',
    loadingLibs: 'Loading data processing libraries...',
    processing: 'Processing data...',
    rendering: 'Rendering charts...'
};
