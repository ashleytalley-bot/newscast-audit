// @ts-check
import { LOADING_MESSAGES } from './modules/config.js';
import { ChartRenderer } from './modules/ChartRenderer.js';
import { TableRenderer } from './modules/TableRenderer.js';
import { DataExporter } from './modules/DataExporter.js';
import { CommentRenderer } from './modules/CommentRenderer.js';

/**
 * @typedef {import('./types').ProcessingResult} ProcessingResult
 * @typedef {import('./types').ErrorResponse} ErrorResponse
 * @typedef {import('./types').ProcessingOutput} ProcessingOutput
 */

/* ═══════════════════════════════════════════════════════════════════════════
   NEWSCAST AUDIT REPORT - Refactored Application
   Class-based architecture with better separation of concerns
   ═══════════════════════════════════════════════════════════════════════════ */

// ═══════════════════════════════════════════════════════════════════════════
// MAIN APPLICATION CLASS
// ═══════════════════════════════════════════════════════════════════════════

export class NewscastAuditApp {
    constructor() {
        console.log("NewscastAuditApp constructor called");
        this.pyodide = null;
        /** @type {ProcessingResult | null} */
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

        // Validate DOM elements
        for (const [key, element] of Object.entries(this.dom)) {
            if (!element) {
                console.error(`CRITICAL: DOM element '${key}' not found!`);
                // Try to show error if possible
                const errDiv = document.getElementById('error-message');
                if (errDiv) {
                    errDiv.classList.remove('hidden');
                    errDiv.textContent = `Error: DOM element '${key}' missing. Page structure incorrect.`;
                }
            }
        }

        this.chartRenderer = new ChartRenderer();
        this.tableRenderer = new TableRenderer();
        this.commentRenderer = new CommentRenderer();
        this.exporter = new DataExporter();
    }

    /**
     * Initialize the application
     */
    init() {
        console.log('Newscast Audit App v2.2.3 - Deployed: 2026-01-18');
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

        // Filter buttons
        document.getElementById('btn-apply-filter').addEventListener('click', () => this.applyDateFilter());
        document.getElementById('btn-copy-comments').addEventListener('click', () => this.copyCommentsToClipboard());
    }

    async applyDateFilter() {
        // Read directly from hidden inputs updated by slider
        const start = /** @type {HTMLInputElement} */ (document.getElementById('filter-start-date')).value;
        const end = /** @type {HTMLInputElement} */ (document.getElementById('filter-end-date')).value;

        if (!this.jsonData) return;

        this.showLoading('Applying filters...');
        try {
            const options = {
                filter_start_date: start || null,
                filter_end_date: end || null
            };
            const result = await this.processDataWithPython(this.jsonData, options);
            if (result.success) {
                // @ts-ignore
                this.processedData = result;
                this.renderResults();
            } else {
                // @ts-ignore
                errorUI.showError(result);
            }
        } catch (e) {
            console.error(e);
            // @ts-ignore
            errorUI.showError("Failed to apply filter");
        } finally {
            this.hideLoading();
        }
    }

    async copyCommentsToClipboard() {
        if (!this.processedData || !this.processedData.comments) return;

        const comments = this.processedData.comments;
        if (comments.length === 0) {
            alert("No comments to copy.");
            return;
        }

        // Format as CSV-like text
        const text = comments.map(c => `[${c.date}] ${c.newscast}: ${c.text}`).join('\n');

        try {
            await navigator.clipboard.writeText(text);
            const btn = document.getElementById('btn-copy-comments');
            const originalText = btn.innerHTML;
            btn.innerHTML = 'Copied!';
            setTimeout(() => { btn.innerHTML = originalText; }, 2000);
        } catch (err) {
            console.error('Failed to copy comments: ', err);
            alert("Failed to copy to clipboard.");
        }
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
     * @param {File} file 
     */
    async processFile(file) {
        try {
            // Validate file type
            if (!file.name.match(/\.xlsx?$/i)) {
                // @ts-ignore global errorUI
                errorUI.showError('Please upload an Excel file (.xlsx or .xls)');
                return;
            }

            this.hideError();
            this.showLoading(LOADING_MESSAGES.readingFile);

            // Parse Excel file
            const jsonData = await this.parseExcelFile(file);
            this.jsonData = jsonData; // Store for filtering re-runs

            // Validate data
            if (!jsonData || jsonData.length === 0) {
                // @ts-ignore global errorUI
                errorUI.showError('Excel file appears to be empty');
                return;
            }

            // Initialize Python environment
            this.showLoading(LOADING_MESSAGES.initPython);
            await this.initializePyodide();

            // Process data
            this.showLoading(LOADING_MESSAGES.processing);
            const result = await this.processDataWithPython(jsonData); // Initial run (no options)

            if (!result.success) {
                // Show structured error with ErrorUI
                // @ts-ignore global errorUI
                errorUI.showError(result);
                this.hideLoading();
                return;
            }

            // Show data quality warnings and info
            // @ts-ignore
            if (result.quality && (
                (result.quality.warnings && result.quality.warnings.length > 0) ||
                (result.quality.info && result.quality.info.length > 0)
            )) {
                // @ts-ignore
                errorUI.showWarnings(result.quality);
            }

            // Render results
            this.showLoading(LOADING_MESSAGES.rendering);
            // @ts-ignore result is Success here
            this.processedData = result;
            this.renderResults();

            this.hideLoading();
            this.showResults();

            // Initialize Date Filters AFTER showing results so slider can calculate width
            // Fixes "slider stuck" issue
            this.initializeDateFilters(result);

        } catch (error) {
            this.hideLoading();
            console.error('Processing error:', error);
            // @ts-ignore global errorUI
            errorUI.showError(`Error processing file: ${error.message || error}`);
        }
    }

    /**
     * Parse Excel file to JSON using SheetJS
     * @param {File} file 
     */
    async parseExcelFile(file) {
        const arrayBuffer = await file.arrayBuffer();
        // Use cellDates: true to force date parsing (avoids serial numbers like 45971)
        // @ts-ignore XLSX
        const workbook = XLSX.read(arrayBuffer, { type: 'array', cellDates: true });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        // @ts-ignore XLSX
        return XLSX.utils.sheet_to_json(firstSheet);
    }

    /**
     * Initialize Pyodide (Python in browser)
     */
    async initializePyodide() {
        if (!this.pyodide) {
            // @ts-ignore
            this.pyodide = await loadPyodide();

            this.showLoading(LOADING_MESSAGES.loadingLibs);
            await this.pyodide.loadPackage(['pandas', 'numpy', 'pyyaml', 'pydantic']);

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
            const manifestResponse = await fetch(`py-files.json?t=${new Date().getTime()}`);
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
                const response = await fetch(`${file}?t=${new Date().getTime()}`);
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
     * Initialize date range slider
     * @param {ProcessingResult} result 
     */
    initializeDateFilters(result) {
        // Use raw date range from backend if available (better granularity than weekly chart)
        // @ts-ignore
        let minTimestamp, maxTimestamp;
        let pChartDates = [];

        // @ts-ignore
        if (result.charts && result.charts.date_range && result.charts.date_range.min) {
            // @ts-ignore
            minTimestamp = new Date(result.charts.date_range.min).getTime();
            // @ts-ignore
            maxTimestamp = new Date(result.charts.date_range.max).getTime();
            console.log("Using raw daily date range:", result.charts.date_range);
        }
        // Fallback to weekly chart dates
        // @ts-ignore
        else if (result.charts && result.charts.weekly && result.charts.weekly.full_dates) {
            // @ts-ignore
            pChartDates = result.charts.weekly.full_dates.sort();
            if (pChartDates.length > 0) {
                minTimestamp = new Date(pChartDates[0]).getTime();
                maxTimestamp = new Date(pChartDates[pChartDates.length - 1]).getTime();
            }
        }

        if (minTimestamp && maxTimestamp) {
            console.log("Slider Dates Debug:", {
                minT: minTimestamp,
                maxT: maxTimestamp,
                minStr: new Date(minTimestamp).toISOString(),
                maxStr: new Date(maxTimestamp).toISOString()
            });

            // Validate timestamps
            if (isNaN(minTimestamp) || isNaN(maxTimestamp)) {
                console.warn("Invalid dates found for slider logic");
                return;
            }

            // Handle single-date case (min == max) by adding a buffer
            if (minTimestamp === maxTimestamp) {
                minTimestamp -= 259200000; // 3 days
                maxTimestamp += 259200000; // 3 days
            }

            const slider = document.getElementById('date-slider');

            // Destroy existing slider if present
            // @ts-ignore
            if (slider.noUiSlider) {
                // @ts-ignore
                slider.noUiSlider.destroy();
            }

            // Force a minimum range of 3 days to prevent "stuck" slider
            const DAY_MS = 86400000;
            let startTimestamp = Number(minTimestamp);
            let endTimestamp = Number(maxTimestamp);

            // Check if duration is too small (less than 3 days)
            if ((endTimestamp - startTimestamp) < (3 * DAY_MS)) {
                console.log(`Date range small (${(endTimestamp - startTimestamp) / DAY_MS} days). Expanding for usability.`);
                // Calculate center point
                const center = (startTimestamp + endTimestamp) / 2;
                // Expand 2 days in each direction
                startTimestamp = center - (2 * DAY_MS);
                endTimestamp = center + (2 * DAY_MS);
            }

            try {
                // @ts-ignore
                noUiSlider.create(slider, {
                    start: [startTimestamp, endTimestamp],
                    connect: true,
                    behaviour: 'drag-tap',
                    range: {
                        'min': startTimestamp,
                        'max': endTimestamp
                    },
                    step: 86400000, // 1 day
                    format: {
                        to: function (value) {
                            try {
                                return new Date(value).toISOString().split('T')[0];
                            } catch (e) {
                                return new Date().toISOString().split('T')[0];
                            }
                        },
                        from: function (value) {
                            return new Date(value).getTime();
                        }
                    }
                });

                const dateValues = document.getElementById('slider-values');
                const startInput = document.getElementById('filter-start-date');
                const endInput = document.getElementById('filter-end-date');

                // @ts-ignore
                slider.noUiSlider.on('update', function (values, handle) {
                    dateValues.innerHTML = `${values[0]}  —  ${values[1]}`;

                    if (handle === 0) {
                        // @ts-ignore
                        startInput.value = values[0];
                    } else {
                        // @ts-ignore
                        endInput.value = values[1];
                    }
                });
            } catch (err) {
                console.error("Slider creation failed:", err);
            }
        }
    }

    /**
     * Process the data using the Python pipeline
     * @param {any[]} jsonData - The parsed Excel data
     * @param {Object} [options] - Filter options
     * @returns {Promise<ProcessingOutput>} The processing result or error response
     */
    async processDataWithPython(jsonData, options = null) {
        this.pyodide.globals.set('json_data', JSON.stringify(jsonData));

        // Pass options if they exist
        let optionsCode = 'None';
        if (options) {
            this.pyodide.globals.set('opts_json', JSON.stringify(options));
            optionsCode = 'json.loads(opts_json)';
            // Ensure json import is available
            await this.pyodide.runPythonAsync('import json');
        }

        const resultJson = await this.pyodide.runPythonAsync(`
            result = pipeline.execute(json_data, options=${optionsCode})
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

    hideError() {
        this.dom.errorMessage.classList.add('hidden');
        // @ts-ignore global errorUI
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
        // @ts-ignore global errorUI
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
        document.getElementById('summary-rows').textContent = summary.record_count.toString();
        document.getElementById('summary-metrics').textContent = summary.metric_count.toString();
        document.getElementById('summary-missing').textContent = summary.missing_newscast.toString();
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

        // Render Charts
        this.chartRenderer.renderOverallChart('chart-overall', charts.overall, config);
        this.chartRenderer.renderPerNewscastCharts('charts-per-newscast', charts.per_newscast, config);

        // Render Weekly Chart (New)
        if (charts.weekly) {
            this.chartRenderer.renderWeeklyChart('chart-weekly', charts.weekly, config);
        }

        // Initialize Weekly Chart Filter
        if (charts.filter_options && charts.filter_options.length > 0) {
            const select = /** @type {HTMLSelectElement} */ (document.getElementById('weekly-chart-filter'));
            if (select) {
                // Clear existing options (except default?) - simpler to rebuild
                select.innerHTML = '';

                // Add options
                charts.filter_options.forEach((opt, index) => {
                    const option = document.createElement('option');
                    // Store index as value to easily retrieve full object later
                    option.value = index.toString();
                    option.textContent = opt.label;
                    select.appendChild(option);
                });

                // Add event listener (remove old one to avoid duplicates if re-rendering? 
                // A clean way is to clone node or just set onchange property)
                select.onchange = () => {
                    const selectedIndex = parseInt(select.value);
                    const selectedData = charts.filter_options[selectedIndex];
                    if (selectedData) {
                        try {
                            // Construct WeeklyChart object from filter option
                            const weeklyData = {
                                dates: selectedData.dates,
                                values: selectedData.values,
                                full_dates: selectedData.dates, // Fallback
                                center_line: selectedData.center_line, // Pass CL
                                ucl: selectedData.ucl,                 // Pass UCL
                                lcl: selectedData.lcl                  // Pass LCL
                            };

                            this.chartRenderer.renderWeeklyChart('chart-weekly', weeklyData, config);
                        } catch (e) {
                            console.error("Error updating chart:", e);
                        }
                    }
                };
            }
        }

        // Render Heatmap (New)
        // Only if per_newscast data exists
        if (charts.per_newscast && charts.per_newscast.length > 0) {
            this.chartRenderer.renderHeatmap('chart-heatmap', charts.per_newscast, config);
        }

        // Render Tables
        // We use the generic render method for tables
        this.tableRenderer.render('table-overall', this.processedData.tables.overall, ['Question', 'Yes %'], config);
        this.tableRenderer.render('table-quality', this.processedData.tables.data_quality, ['Question', 'Complete %', 'Missing'], config);
        this.tableRenderer.render('table-volume', this.processedData.tables.volume, ['Newscast', 'Responses'], config);

        // Render Comments (New)
        // @ts-ignore
        if (this.processedData.comments) {
            // @ts-ignore
            this.commentRenderer.renderComments('comments-feed', this.processedData.comments);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EXPORT FUNCTIONALITY
    // ═══════════════════════════════════════════════════════════════════════

    async exportExcel() {
        if (!this.processedData) return;
        // @ts-ignore
        await this.exporter.exportToExcel(this.processedData);
    }

    async exportPowerPoint() {
        if (!this.processedData) return;
        await this.exporter.exportToPowerPoint(this.processedData, this.chartRenderer);
    }
}
