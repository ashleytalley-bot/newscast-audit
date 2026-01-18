/* ═══════════════════════════════════════════════════════════════════════════
   NEWSCAST AUDIT REPORT - Refactored Application
   Class-based architecture with better separation of concerns
   ═══════════════════════════════════════════════════════════════════════════ */

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const CHART_DEFAULTS = {
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

const LOADING_MESSAGES = {
    readingFile: 'Reading Excel file...',
    initPython: 'Initializing Python environment...',
    loadingLibs: 'Loading data processing libraries...',
    processing: 'Processing data...',
    rendering: 'Rendering charts...'
};

// ═══════════════════════════════════════════════════════════════════════════
// MAIN APPLICATION CLASS
// ═══════════════════════════════════════════════════════════════════════════

class NewscastAuditApp {
    constructor() {
        this.pyodide = null;
        this.processedData = null;

        // DOM Elements
        this.dom = {
            uploadSection: document.getElementById('upload-section'),
            resultsSection: document.getElementById('results-section'),
            dropZone: document.getElementById('drop-zone'),
            fileInput: document.getElementById('file-input'),
            loadingIndicator: document.getElementById('loading-indicator'),
            loadingText: document.getElementById('loading-text'),
            errorMessage: document.getElementById('error-message')
        };

        this.chartRenderer = new ChartRenderer();
        this.tableRenderer = new TableRenderer();
        this.exporter = new DataExporter();
    }

    /**
     * Initialize the application
     */
    init() {
        console.log('Newscast Audit App v2.0.1 - Deployed: 2026-01-18');
        this.setupEventListeners();
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // File input
        this.dom.dropZone.addEventListener('click', () => this.dom.fileInput.click());
        this.dom.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop
        this.dom.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dom.dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.dom.dropZone.addEventListener('drop', (e) => this.handleDrop(e));

        // Export buttons
        document.getElementById('btn-export-excel').addEventListener('click', () => this.exportExcel());
        document.getElementById('btn-export-pptx').addEventListener('click', () => this.exportPowerPoint());
        document.getElementById('btn-new-file').addEventListener('click', () => this.resetToUpload());
    }

    // ═══════════════════════════════════════════════════════════════════════
    // FILE HANDLING
    // ═══════════════════════════════════════════════════════════════════════

    handleDragOver(e) {
        e.preventDefault();
        this.dom.dropZone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.dom.dropZone.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.dom.dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    /**
     * Process uploaded Excel file
     */
    async processFile(file) {
        try {
            // Validate file type
            if (!file.name.match(/\.xlsx?$/i)) {
                errorUI.showError('Please upload an Excel file (.xlsx or .xls)');
                return;
            }

            this.hideError();
            this.showLoading(LOADING_MESSAGES.readingFile);

            // Parse Excel file
            const jsonData = await this.parseExcelFile(file);

            // Validate data
            if (!jsonData || jsonData.length === 0) {
                errorUI.showError('Excel file appears to be empty');
                return;
            }

            // Initialize Python environment
            this.showLoading(LOADING_MESSAGES.initPython);
            await this.initializePyodide();

            // Process data
            this.showLoading(LOADING_MESSAGES.processing);
            const result = await this.processDataWithPython(jsonData);

            if (!result.success) {
                // Show structured error with ErrorUI
                errorUI.showError(result);
                this.hideLoading();
                return;
            }

            // Show data quality warnings and info
            if (result.quality && (
                (result.quality.warnings && result.quality.warnings.length > 0) ||
                (result.quality.info && result.quality.info.length > 0)
            )) {
                errorUI.showWarnings(result.quality);
            }

            // Render results
            this.showLoading(LOADING_MESSAGES.rendering);
            this.processedData = result;
            this.renderResults();

            this.hideLoading();
            this.showResults();

        } catch (error) {
            this.hideLoading();
            console.error('Processing error:', error);
            errorUI.showError(`Error processing file: ${error.message || error}`);
        }
    }

    /**
     * Parse Excel file to JSON using SheetJS
     */
    async parseExcelFile(file) {
        const arrayBuffer = await file.arrayBuffer();
        // Use cellDates: true to force date parsing (avoids serial numbers like 45971)
        const workbook = XLSX.read(arrayBuffer, { type: 'array', cellDates: true });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        return XLSX.utils.sheet_to_json(firstSheet);
    }

    /**
     * Initialize Pyodide (Python in browser)
     */
    async initializePyodide() {
        if (!this.pyodide) {
            this.pyodide = await loadPyodide();

            this.showLoading(LOADING_MESSAGES.loadingLibs);
            await this.pyodide.loadPackage(['pandas', 'numpy', 'pyyaml']);

            // Load all Python files
            await this.loadPythonFiles();

            // Fetch configuration files
            // We fetch these from the web server so they can be edited without rebuilding the app
            console.log("Fetching configuration files...");
            const [stationYaml, surveyYaml, normYaml] = await Promise.all([
                fetch('config/stations/default.yaml').then(r => r.text()),
                fetch('config/surveys/newscast-audit-v1.yaml').then(r => r.text()),
                fetch('config/normalization/newscast-patterns.yaml').then(r => r.text())
            ]);

            // Initialize configuration
            // We pass the raw YAML strings to Python because Python (PyYAML) is better 
            // at parsing complex YAML structures than JS libraries.
            console.log("Initializing configuration...");
            this.pyodide.globals.set('station_yaml', stationYaml);
            this.pyodide.globals.set('survey_yaml', surveyYaml);
            this.pyodide.globals.set('norm_yaml', normYaml);

            await this.pyodide.runPythonAsync(`
                from lib.config_dynamic import initialize_config
                # Hydrate the global config object with the fetched YAMLs
                initialize_config(station_yaml, survey_yaml, norm_yaml)
            `);

            // Import the processing pipeline
            await this.pyodide.runPythonAsync(`
                from py.pipeline.orchestrator import ProcessingPipeline
                pipeline = ProcessingPipeline()
            `);
        }
    }

    async loadPythonFiles() {
        let files;
        try {
            // Fetch the manifest generated by build.py
            const manifestResponse = await fetch('py-files.json');
            if (!manifestResponse.ok) throw new Error('Failed to load py-files.json manifest');
            files = await manifestResponse.json();
            console.log('Loading Python files from manifest:', files);
        } catch (err) {
            console.error('Failed to load manifest, falling back to core file list:', err);
            // Fallback just in case manifest is missing
            files = [
                'lib/__init__.py',
                'lib/config.py',
                'lib/cleaners.py',
                'lib/builders.py',
                'lib/utils.py',
                'lib/exceptions.py',
                'py/processing.py'
            ];
        }

        // Dynamically identify all unique directories that need to be created
        const dirs = new Set();
        files.forEach(file => {
            const parts = file.split('/');
            if (parts.length > 1) {
                // "py/pipeline/steps/clean.py" -> "py/pipeline/steps"
                // We keep adding parents until we reach top level
                // Actually os.makedirs creates variables parents, so we just need the deepest dir for each file
                const dir = parts.slice(0, parts.length - 1).join('/');
                dirs.add(dir);
            }
        });

        const dirList = Array.from(dirs);
        console.log("Ensuring directories exist:", dirList);

        // Use Python to create directories (robust handling of existing dirs)
        this.pyodide.globals.set('required_dirs', JSON.stringify(dirList));
        this.pyodide.runPython(`
            import os
            import json
            dirs = json.loads(required_dirs)
            for d in dirs:
                os.makedirs(d, exist_ok=True)
        `);

        // Fetch and write files
        for (const file of files) {
            try {
                // Add cache busting to ensure fresh code is loaded
                const response = await fetch(file, { cache: 'no-store' });
                if (!response.ok) throw new Error(`Failed to load ${file}`);
                const content = await response.text();
                // Ensure parent directory exists for nested files inside sub-sub-folders if any
                // (though current structure is flat enough)
                this.pyodide.FS.writeFile(file, content);
            } catch (err) {
                console.error(`Error loading ${file}:`, err);
                throw err;
            }
        }
    }

    /**
     * Process data using Python (via Pyodide)
     */
    async processDataWithPython(jsonData) {
        this.pyodide.globals.set('json_data', JSON.stringify(jsonData));

        const resultJson = await this.pyodide.runPythonAsync(`
            result = pipeline.execute(json_data)
            result
        `);

        return JSON.parse(resultJson);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UI STATE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════

    showLoading(message) {
        this.dom.loadingText.textContent = message;
        this.dom.loadingIndicator.classList.remove('hidden');
    }

    hideLoading() {
        this.dom.loadingIndicator.classList.add('hidden');
    }

    showError(message) {
        this.dom.errorMessage.textContent = message;
        this.dom.errorMessage.classList.remove('hidden');
    }

    hideError() {
        this.dom.errorMessage.classList.add('hidden');
        errorUI.clearAll();
    }

    showResults() {
        this.dom.uploadSection.classList.add('hidden');
        this.dom.resultsSection.classList.remove('hidden');
    }

    resetToUpload() {
        this.dom.resultsSection.classList.add('hidden');
        this.dom.uploadSection.classList.remove('hidden');
        this.dom.fileInput.value = '';
        this.hideError();
        errorUI.clearAll();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // RESULT RENDERING
    // ═══════════════════════════════════════════════════════════════════════

    renderResults() {
        this.renderSummary();
        this.renderTables();
        this.renderCharts();
    }

    renderSummary() {
        const summary = this.processedData.summary;
        document.getElementById('summary-rows').textContent = summary.record_count;
        document.getElementById('summary-metrics').textContent = summary.metric_count;
        document.getElementById('summary-missing').textContent = summary.missing_newscast;
    }

    renderTables() {
        const tables = this.processedData.tables;

        // Overall metrics
        this.tableRenderer.render('table-overall', tables.overall, ['Question', 'Yes %'], this.processedData.config);

        // Data quality
        this.tableRenderer.render('table-quality', tables.data_quality, ['Question', 'Complete %', 'Missing'], this.processedData.config);

        // Recent week (if available)
        if (tables.recent) {
            document.getElementById('recent-week-card').classList.remove('hidden');
            document.getElementById('recent-week-title').textContent =
                `Week of ${tables.recent_week_start}`;
            this.tableRenderer.render('table-recent', tables.recent, ['Question', 'Yes %'], this.processedData.config);
        } else {
            document.getElementById('recent-week-card').classList.add('hidden');
        }

        // Volume by newscast
        if (tables.volume) {
            this.tableRenderer.render('table-volume', tables.volume, ['Newscast', 'Responses'], this.processedData.config);
        }
    }

    renderCharts() {
        const charts = this.processedData.charts;
        const config = this.processedData.config;

        // Overall chart
        this.chartRenderer.renderOverallChart('chart-overall', charts.overall, config);

        // Per-newscast charts
        this.chartRenderer.renderPerNewscastCharts('charts-per-newscast', charts.per_newscast, config);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EXPORT FUNCTIONALITY
    // ═══════════════════════════════════════════════════════════════════════

    async exportExcel() {
        if (!this.processedData) return;
        await this.exporter.exportToExcel(this.processedData);
    }

    async exportPowerPoint() {
        if (!this.processedData) return;
        await this.exporter.exportToPowerPoint(this.processedData, this.chartRenderer);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// CHART RENDERER CLASS
// ═══════════════════════════════════════════════════════════════════════════

class ChartRenderer {
    /**
     * Create a Plotly bar trace
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
     */
    renderOverallChart(containerId, chartData, config) {
        const trace = this.createBarTrace(chartData.labels, chartData.values, chartData.colors);
        const layout = this.createLayout(`Overall Audit Metrics (n=${chartData.n})`, config);

        Plotly.newPlot(containerId, [trace], layout, { responsive: CHART_DEFAULTS.responsive });
    }

    /**
     * Render per-newscast charts
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

            Plotly.newPlot(chartId, [trace], layout, { responsive: CHART_DEFAULTS.responsive });
        });
    }

    /**
     * Capture chart as image (for PowerPoint export)
     */
    async captureChartAsImage(elementId, width = 800, height = 500) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Chart element ${elementId} not found`);
            return null;
        }

        try {
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

// ═══════════════════════════════════════════════════════════════════════════
// TABLE RENDERER CLASS
// ═══════════════════════════════════════════════════════════════════════════

class TableRenderer {
    /**
     * Render a data table
     */
    render(containerId, data, columns, config) {
        const container = document.getElementById(containerId);

        if (!data || data.length === 0) {
            container.innerHTML = '<p>No data available</p>';
            return;
        }

        const thresholds = config.thresholds;
        let html = '<table><thead><tr>';

        // Table headers
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';

        // Table rows
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                const className = this.getCellClass(col, value, thresholds);
                const displayValue = this.formatCellValue(col, value);

                html += `<td class="${className}">${displayValue}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Get CSS class for cell based on value and thresholds
     */
    getCellClass(columnName, value, thresholds) {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            if (value >= thresholds.good) return 'pct-good';
            if (value <= thresholds.poor) return 'pct-poor';
            return 'pct-moderate';
        }
        return '';
    }

    /**
     * Format cell value for display
     */
    formatCellValue(columnName, value) {
        if (columnName === 'Yes %' || columnName === 'Complete %') {
            return value + '%';
        }
        return value;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// DATA EXPORTER CLASS
// ═══════════════════════════════════════════════════════════════════════════

class DataExporter {
    /**
     * Export data to Excel workbook
     */
    async exportToExcel(processedData) {
        const workbook = XLSX.utils.book_new();

        // Overall metrics sheet
        this.addSheetFromData(workbook, processedData.export_data.overall, 'Overall Metrics');

        // Data quality sheet
        this.addSheetFromData(workbook, processedData.export_data.data_quality, 'Data Quality');

        // Recent week sheet (if available)
        if (processedData.export_data.recent && processedData.export_data.recent.length > 0) {
            this.addSheetFromData(workbook, processedData.export_data.recent, 'Recent Week');
        }

        // Volume sheet
        if (processedData.export_data.volume && processedData.export_data.volume.length > 0) {
            this.addSheetFromData(workbook, processedData.export_data.volume, 'Volume by Newscast');
        }

        // Normalized data sheet
        this.addSheetFromData(workbook, processedData.export_data.normalized, 'All Data');

        // Download file
        const timestamp = new Date().toISOString().split('T')[0];
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
        pptx.layout = 'LAYOUT_16x9';
        pptx.author = 'Newscast Audit Tool';
        pptx.company = 'TEGNA';

        // Title slide
        let slide = pptx.addSlide();
        slide.addText('Newscast Audit Report', {
            x: 0.5, y: 2, w: 9, h: 1,
            fontSize: 44, bold: true, color: '045ea8'
        });
        slide.addText(`Generated: ${new Date().toLocaleDateString()}`, {
            x: 0.5, y: 3.5, w: 9, h: 0.5,
            fontSize: 18, color: '666666'
        });

        // Summary slide
        slide = pptx.addSlide();
        slide.addText('Summary', { x: 0.5, y: 0.5, w: 9, h: 0.5, fontSize: 32, bold: true });
        slide.addText([
            { text: `Total Responses: ${processedData.summary.record_count}\n`, options: { breakLine: true } },
            { text: `Metrics Tracked: ${processedData.summary.metric_count}\n`, options: { breakLine: true } },
            { text: `Missing Newscast: ${processedData.summary.missing_newscast}`, options: { breakLine: true } }
        ], { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 18 });

        // Overall chart slide
        const overallChart = await chartRenderer.captureChartAsImage('chart-overall');
        if (overallChart) {
            slide = pptx.addSlide();
            slide.addText('Overall Audit Metrics', { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 28, bold: true });
            slide.addImage({ data: overallChart, x: 0.5, y: 1, w: 9, h: 4.5 });
        }

        // Per-newscast charts
        const perNewscastCharts = processedData.charts.per_newscast;
        for (let i = 0; i < perNewscastCharts.length; i++) {
            const chartId = `chart-newscast-${i}`;
            const chartImg = await chartRenderer.captureChartAsImage(chartId);

            if (chartImg) {
                slide = pptx.addSlide();
                slide.addText(`${perNewscastCharts[i].newscast} (n=${perNewscastCharts[i].n})`, {
                    x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 28, bold: true
                });
                slide.addImage({ data: chartImg, x: 0.5, y: 1, w: 9, h: 4.5 });
            }
        }

        // Download file
        const timestamp = new Date().toISOString().split('T')[0];
        pptx.writeFile({ fileName: `newscast-audit-${timestamp}.pptx` });
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// APPLICATION INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    const app = new NewscastAuditApp();
    app.init();
});
