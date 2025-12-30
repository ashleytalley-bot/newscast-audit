/* ═══════════════════════════════════════════════════════════════════════════
   NEWSCAST AUDIT REPORT - Main Application
   Handles file upload, Pyodide processing, chart rendering, and exports
   ═══════════════════════════════════════════════════════════════════════════ */

// Global state
let pyodide = null;
let processedData = null;

// DOM Elements
const uploadSection = document.getElementById('upload-section');
const resultsSection = document.getElementById('results-section');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const loadingIndicator = document.getElementById('loading-indicator');
const loadingText = document.getElementById('loading-text');
const errorMessage = document.getElementById('error-message');

// ═══════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // File input
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // Export buttons
    document.getElementById('btn-export-excel').addEventListener('click', exportExcel);
    document.getElementById('btn-export-pptx').addEventListener('click', exportPowerPoint);
    document.getElementById('btn-new-file').addEventListener('click', resetToUpload);

    // Weekly filter
    document.getElementById('weekly-filter').addEventListener('change', updateWeeklyChart);
}

// ═══════════════════════════════════════════════════════════════════════════
// FILE HANDLING
// ═══════════════════════════════════════════════════════════════════════════

function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

async function processFile(file) {
    // Validate file type
    if (!file.name.match(/\.xlsx?$/i)) {
        showError('Please upload an Excel file (.xlsx or .xls)');
        return;
    }

    hideError();
    showLoading('Initializing Python environment...');

    try {
        // Initialize Pyodide if needed
        if (!pyodide) {
            pyodide = await loadPyodide();
            showLoading('Loading data processing libraries...');
            await pyodide.loadPackage(['pandas', 'openpyxl']);

            // Load processing script
            showLoading('Loading processing script...');
            const response = await fetch('py/processing.py');
            const pythonCode = await response.text();
            await pyodide.runPythonAsync(pythonCode);
        }

        showLoading('Processing Excel file...');

        // Read file as array buffer
        const arrayBuffer = await file.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);

        // Pass to Python
        pyodide.globals.set('excel_bytes', uint8Array);

        // Process the file
        const resultJson = await pyodide.runPythonAsync(`
import json
result = process_excel_bytes(bytes(excel_bytes))
result
        `);

        // Parse result
        processedData = JSON.parse(resultJson);

        hideLoading();
        renderResults();

    } catch (error) {
        hideLoading();
        console.error('Processing error:', error);
        showError(`Error processing file: ${error.message || error}`);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════════════════════════════════════

function showLoading(message) {
    loadingText.textContent = message;
    loadingIndicator.classList.remove('hidden');
    dropZone.classList.add('hidden');
}

function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    dropZone.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function resetToUpload() {
    resultsSection.classList.add('hidden');
    uploadSection.classList.remove('hidden');
    dropZone.classList.remove('hidden');
    fileInput.value = '';
}

// ═══════════════════════════════════════════════════════════════════════════
// RENDER RESULTS
// ═══════════════════════════════════════════════════════════════════════════

function renderResults() {
    uploadSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    // Summary
    document.getElementById('summary-rows').textContent = processedData.summary.record_count;
    document.getElementById('summary-metrics').textContent = processedData.summary.metric_count;
    document.getElementById('summary-missing').textContent = processedData.summary.missing_newscast;

    // Tables
    renderTable('table-overall', processedData.tables.overall, ['Question', 'Yes %']);
    renderTable('table-quality', processedData.tables.data_quality, ['Question', 'Complete %', 'Missing']);

    if (processedData.tables.recent) {
        document.getElementById('recent-week-title').textContent =
            `Current Week (${processedData.tables.recent_week_start})`;
        renderTable('table-recent', processedData.tables.recent, ['Question', 'Yes %']);
    } else {
        document.getElementById('recent-week-card').classList.add('hidden');
    }

    if (processedData.tables.volume) {
        renderTable('table-volume', processedData.tables.volume, ['Newscast', 'Responses']);
    }

    // Charts
    renderOverallChart();
    renderWeeklyChart();
    renderPerNewscastCharts();

    // Populate weekly filter
    populateWeeklyFilter();
}

function renderTable(containerId, data, columns) {
    const container = document.getElementById(containerId);
    if (!data || data.length === 0) {
        container.innerHTML = '<p>No data available</p>';
        return;
    }

    const thresholds = processedData.config.thresholds;

    let html = '<table><thead><tr>';
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            let className = '';

            // Color code percentage columns
            if (col === 'Yes %' || col === 'Complete %') {
                if (value >= thresholds.good) {
                    className = 'pct-good';
                } else if (value <= thresholds.poor) {
                    className = 'pct-poor';
                } else {
                    className = 'pct-moderate';
                }
                value = value + '%';
            }

            html += `<td class="${className}">${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════════════
// CHART RENDERING
// ═══════════════════════════════════════════════════════════════════════════

function renderOverallChart() {
    const chartData = processedData.charts.overall;
    const palette = processedData.config.palette;

    const trace = {
        x: chartData.labels,
        y: chartData.values,
        type: 'bar',
        marker: {
            color: chartData.colors
        },
        text: chartData.values.map(v => v + '%'),
        textposition: 'outside',
        textfont: {
            color: palette.primary
        }
    };

    const layout = {
        title: `Overall Audit Metrics (n=${chartData.n})`,
        yaxis: {
            title: 'Percent Yes',
            range: [0, 110],
            ticksuffix: '%'
        },
        xaxis: {
            tickangle: -35
        },
        margin: { b: 120, t: 60 },
        font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }
    };

    Plotly.newPlot('chart-overall', [trace], layout, { responsive: true });
}

function renderWeeklyChart(filterIndex = 0) {
    const filterOptions = processedData.charts.filter_options;
    if (!filterOptions || filterOptions.length === 0) {
        document.getElementById('chart-weekly').innerHTML = '<p>No weekly data available</p>';
        return;
    }

    const data = filterOptions[filterIndex];
    const palette = processedData.config.palette;

    const trace = {
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: palette.primary,
            width: 2
        },
        marker: {
            color: palette.primary,
            size: 9
        },
        name: 'Weekly percent'
    };

    // Add annotation for last point
    const annotations = [];
    if (data.values.length > 0) {
        const lastIdx = data.values.length - 1;
        annotations.push({
            x: data.dates[lastIdx],
            y: data.values[lastIdx],
            text: data.values[lastIdx].toFixed(0) + '%',
            showarrow: false,
            yshift: 15,
            font: { color: palette.primary }
        });
    }

    const layout = {
        title: 'Overall Percent Yes Over Time (Weekly)',
        xaxis: {
            title: 'Week Starting (Monday)',
            tickangle: -45
        },
        yaxis: {
            title: 'Percent (%)',
            range: [40, 100],
            ticksuffix: '%'
        },
        annotations: annotations,
        margin: { b: 80, t: 60 },
        font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }
    };

    Plotly.newPlot('chart-weekly', [trace], layout, { responsive: true });
}

function populateWeeklyFilter() {
    const select = document.getElementById('weekly-filter');
    const filterOptions = processedData.charts.filter_options;

    select.innerHTML = '';
    filterOptions.forEach((option, index) => {
        const opt = document.createElement('option');
        opt.value = index;
        opt.textContent = option.label;
        select.appendChild(opt);
    });
}

function updateWeeklyChart() {
    const select = document.getElementById('weekly-filter');
    renderWeeklyChart(parseInt(select.value));
}

function renderPerNewscastCharts() {
    const container = document.getElementById('charts-per-newscast');
    const perNewscast = processedData.charts.per_newscast;

    if (!perNewscast || perNewscast.length === 0) {
        container.innerHTML = '<p>No newscast data available</p>';
        return;
    }

    container.innerHTML = '';

    perNewscast.forEach((data, index) => {
        const chartId = `chart-newscast-${index}`;
        const card = document.createElement('div');
        card.className = 'chart-card';
        card.innerHTML = `<h3>${data.newscast} (n=${data.n})</h3><div id="${chartId}" class="chart-container"></div>`;
        container.appendChild(card);

        const trace = {
            y: data.labels,
            x: data.values,
            type: 'bar',
            orientation: 'h',
            marker: {
                color: data.colors
            },
            text: data.values.map(v => v + '%'),
            textposition: 'outside',
            textfont: {
                color: processedData.config.palette.primary
            }
        };

        const layout = {
            xaxis: {
                title: 'Percent Yes',
                range: [0, 110],
                ticksuffix: '%'
            },
            margin: { l: 200, r: 60, t: 20, b: 50 },
            font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }
        };

        Plotly.newPlot(chartId, [trace], layout, { responsive: true });
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// EXCEL EXPORT
// ═══════════════════════════════════════════════════════════════════════════

function exportExcel() {
    if (!processedData) return;

    const wb = XLSX.utils.book_new();
    const exportData = processedData.export_data;

    // Report Info sheet
    const reportInfo = [
        ['Property', 'Value'],
        ['Report Generated', new Date().toISOString()],
        ['Total Responses', processedData.summary.record_count],
        ['Metrics Tracked', processedData.summary.metric_count],
    ];
    const wsInfo = XLSX.utils.aoa_to_sheet(reportInfo);
    XLSX.utils.book_append_sheet(wb, wsInfo, 'Report Info');

    // Data Quality sheet
    if (exportData.data_quality && exportData.data_quality.length > 0) {
        const wsQuality = XLSX.utils.json_to_sheet(exportData.data_quality);
        XLSX.utils.book_append_sheet(wb, wsQuality, 'Data Quality');
    }

    // Overall Metrics sheet
    if (exportData.overall && exportData.overall.length > 0) {
        const wsOverall = XLSX.utils.json_to_sheet(exportData.overall);
        XLSX.utils.book_append_sheet(wb, wsOverall, 'Overall Metrics');
    }

    // Recent Week sheet
    if (exportData.recent && exportData.recent.length > 0) {
        const wsRecent = XLSX.utils.json_to_sheet(exportData.recent);
        XLSX.utils.book_append_sheet(wb, wsRecent, 'Recent Week Metrics');
    }

    // Volume sheet
    if (exportData.volume && exportData.volume.length > 0) {
        const wsVolume = XLSX.utils.json_to_sheet(exportData.volume);
        XLSX.utils.book_append_sheet(wb, wsVolume, 'Responses by Newscast');
    }

    // Weekly data sheet
    if (exportData.weekly && exportData.weekly.dates && exportData.weekly.dates.length > 0) {
        const weeklyData = exportData.weekly.dates.map((date, i) => ({
            'Week Starting': date,
            'Percent Yes': exportData.weekly.values[i]
        }));
        const wsWeekly = XLSX.utils.json_to_sheet(weeklyData);
        XLSX.utils.book_append_sheet(wb, wsWeekly, 'Weekly Trend');
    }

    // Normalized Data sheet
    if (exportData.normalized && exportData.normalized.length > 0) {
        const wsNormalized = XLSX.utils.json_to_sheet(exportData.normalized);
        XLSX.utils.book_append_sheet(wb, wsNormalized, 'Normalized Data');
    }

    // Download
    XLSX.writeFile(wb, 'newscast-audit-export.xlsx');
}

// ═══════════════════════════════════════════════════════════════════════════
// POWERPOINT EXPORT
// ═══════════════════════════════════════════════════════════════════════════

async function exportPowerPoint() {
    if (!processedData) return;

    const pptx = new PptxGenJS();

    // Set presentation properties
    pptx.author = 'TEGNA Newscast Audit';
    pptx.title = 'Newscast Audit Report';
    pptx.subject = 'Audit Results';

    const palette = processedData.config.palette;

    // Helper to convert hex to PptxGenJS color format
    const hexToColor = (hex) => hex.replace('#', '');

    // Title Slide
    let slide = pptx.addSlide();
    slide.addText('Newscast Audit Report', {
        x: 0.5, y: 2, w: 9, h: 1.5,
        fontSize: 36, bold: true, color: '000000',
        align: 'center'
    });
    slide.addText(`${processedData.summary.record_count} Responses | ${processedData.summary.metric_count} Metrics`, {
        x: 0.5, y: 3.5, w: 9, h: 0.5,
        fontSize: 18, color: hexToColor(palette.muted),
        align: 'center'
    });
    slide.addText(new Date().toLocaleDateString(), {
        x: 0.5, y: 4.2, w: 9, h: 0.5,
        fontSize: 14, color: hexToColor(palette.muted),
        align: 'center'
    });

    // Overall Metrics Chart - capture as image
    const overallImg = await captureChartAsImage('chart-overall');
    if (overallImg) {
        slide = pptx.addSlide();
        slide.addText('Overall Audit Metrics', {
            x: 0.5, y: 0.3, w: 9, h: 0.5,
            fontSize: 24, bold: true, color: '000000'
        });
        slide.addImage({
            data: overallImg,
            x: 0.25, y: 1, w: 9.5, h: 5.5
        });
    }

    // Weekly Trend Chart
    const weeklyImg = await captureChartAsImage('chart-weekly');
    if (weeklyImg) {
        slide = pptx.addSlide();
        slide.addText('Weekly Trend', {
            x: 0.5, y: 0.3, w: 9, h: 0.5,
            fontSize: 24, bold: true, color: '000000'
        });
        slide.addImage({
            data: weeklyImg,
            x: 0.25, y: 1, w: 9.5, h: 5.5
        });
    }

    // Per-Newscast Charts
    const perNewscastCharts = processedData.charts.per_newscast;
    for (let i = 0; i < perNewscastCharts.length; i++) {
        const chartId = `chart-newscast-${i}`;
        const chartImg = await captureChartAsImage(chartId);
        if (chartImg) {
            slide = pptx.addSlide();
            slide.addText(`${perNewscastCharts[i].newscast} Metrics`, {
                x: 0.5, y: 0.3, w: 9, h: 0.5,
                fontSize: 24, bold: true, color: '000000'
            });
            slide.addImage({
                data: chartImg,
                x: 0.25, y: 1, w: 9.5, h: 5.5
            });
        }
    }

    // Summary Table Slide
    slide = pptx.addSlide();
    slide.addText('Overall Metrics Summary', {
        x: 0.5, y: 0.3, w: 9, h: 0.5,
        fontSize: 24, bold: true, color: '000000'
    });

    const tableData = processedData.tables.overall.map(row => [
        { text: row['Question'], options: { align: 'left' } },
        {
            text: row['Yes %'] + '%',
            options: {
                align: 'center',
                color: row['Yes %'] >= 80 ? hexToColor(palette.primary) :
                       row['Yes %'] <= 40 ? hexToColor(palette.alert) :
                       hexToColor(palette.accent),
                bold: true
            }
        }
    ]);

    slide.addTable(
        [
            [
                { text: 'Question', options: { fill: 'EEEEEE', bold: true } },
                { text: 'Yes %', options: { fill: 'EEEEEE', bold: true, align: 'center' } }
            ],
            ...tableData
        ],
        {
            x: 0.5, y: 1, w: 9, h: 5,
            fontSize: 12,
            border: { pt: 0.5, color: 'CCCCCC' },
            colW: [6.5, 2.5]
        }
    );

    // Save file
    pptx.writeFile({ fileName: 'newscast-audit-report.pptx' });
}

async function captureChartAsImage(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return null;

    try {
        const dataUrl = await Plotly.toImage(element, {
            format: 'png',
            width: 1200,
            height: 700,
            scale: 2
        });
        return dataUrl;
    } catch (error) {
        console.error('Error capturing chart:', error);
        return null;
    }
}
