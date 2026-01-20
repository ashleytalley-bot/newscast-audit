import { LOADING_MESSAGES } from './modules/config.js';
import { ChartRenderer } from './modules/ChartRenderer.js';
import { TableRenderer } from './modules/TableRenderer.js';
import { DataExporter } from './modules/DataExporter.js';
import { CommentRenderer } from './modules/CommentRenderer.js';
import { DateSlider } from './modules/DateSlider.js';
import { PyodideService } from './services/PyodideService.js';
import { ErrorUI } from './modules/ErrorUI.js';
import { isProcessingResult, ProcessingOutput } from './types/index.js';
import type { ProcessingResult } from './types/output';
import type { ErrorResponse } from './types/errors';

// External library type definitions (since we load them via CDN/script tags)
declare const XLSX: any;

interface DOMElements {
    uploadSection: HTMLElement;
    resultsSection: HTMLElement;
    dropZone: HTMLElement;
    fileInput: HTMLInputElement;
    loadingIndicator: HTMLElement;
    loadingText: HTMLElement;
    errorMessage: HTMLElement;
    headerControls: HTMLElement;
}

/* ═══════════════════════════════════════════════════════════════════════════
   NEWSCAST AUDIT REPORT - Refactored Application
   Class-based architecture with better separation of concerns
   ═══════════════════════════════════════════════════════════════════════════ */

export class NewscastAuditApp {
    public pyodideService: PyodideService;
    private processedData: ProcessingResult | null = null;
    private jsonData: any[] | null = null; // Raw Excel data
    private dateSlider: DateSlider | null = null;

    private dom: DOMElements;

    private chartRenderer: ChartRenderer;
    private tableRenderer: TableRenderer;
    private commentRenderer: CommentRenderer;
    private exporter: DataExporter;
    private errorUI: ErrorUI;

    constructor() {
        this.pyodideService = new PyodideService();

        // DOM Elements
        this.dom = {
            uploadSection: document.getElementById('upload-section')!,
            resultsSection: document.getElementById('results-section')!,
            dropZone: document.getElementById('drop-zone')!,
            fileInput: document.getElementById('file-input') as HTMLInputElement,
            loadingIndicator: document.getElementById('loading-indicator')!,
            loadingText: document.getElementById('loading-text')!,
            errorMessage: document.getElementById('error-message')!,
            headerControls: document.getElementById('header-controls')!
        };

        this.validateDom();

        this.chartRenderer = new ChartRenderer();
        this.tableRenderer = new TableRenderer();
        this.commentRenderer = new CommentRenderer();
        this.exporter = new DataExporter();
        this.errorUI = new ErrorUI();
    }

    private validateDom() {
        for (const [key, element] of Object.entries(this.dom)) {
            if (!element) {
                console.error(`CRITICAL: DOM element '${key}' not found!`);
                const errDiv = document.getElementById('error-message');
                if (errDiv) {
                    errDiv.classList.remove('hidden');
                    errDiv.textContent = `Error: DOM element '${key}' missing. Page structure incorrect.`;
                }
            }
        }
    }

    /**
     * Initialize the application
     */
    init() {
        console.log('Newscast Audit App v2.2.3 - Deployed: 2026-01-18');
        this.setupEventListeners();

        // Register Progress Callback from Worker
        this.pyodideService.setOnProgress((msg: string) => {
            this.updateLoadingText(msg);
        });
    }

    /**
     * Set up all event listeners
     */
    private setupEventListeners() {
        // File input
        this.dom.dropZone.addEventListener('click', () => this.dom.fileInput.click());
        this.dom.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop
        this.dom.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dom.dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.dom.dropZone.addEventListener('drop', (e) => this.handleDrop(e));

        // Export buttons
        document.getElementById('btn-export-excel')?.addEventListener('click', () => this.exportExcel());
        document.getElementById('btn-export-pptx')?.addEventListener('click', () => this.exportPowerPoint());
        document.getElementById('btn-new-file')?.addEventListener('click', () => this.resetToUpload());

        // Filter buttons
        document.getElementById('btn-copy-comments')?.addEventListener('click', () => this.copyCommentsToClipboard());
    }

    async applyDateFilter() {
        const startInput = document.getElementById('filter-start-date') as HTMLInputElement;
        const endInput = document.getElementById('filter-end-date') as HTMLInputElement;

        const start = startInput?.value;
        const end = endInput?.value;

        console.log(`Apply Filter Triggered: [${start}] to [${end}]`);
        if (!this.jsonData) return;

        this.showLoading('Applying filters...');
        try {
            const options = {
                filter_start_date: start || null,
                filter_end_date: end || null
            };

            const result = await this.pyodideService.processData(this.jsonData, options);

            if (result.success) {
                this.processedData = result as ProcessingResult;
                this.renderResults();
            } else {
                this.errorUI.showError(result);
            }
        } catch (e) {
            console.error(e);
            this.errorUI.showError("Failed to apply filter");
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
            if (btn) {
                const originalText = btn.innerHTML;
                btn.innerHTML = 'Copied!';
                setTimeout(() => { btn.innerHTML = originalText; }, 2000);
            }
        } catch (err) {
            console.error('Failed to copy comments: ', err);
            alert("Failed to copy to clipboard.");
        }
    }

    /**
     * Initialize date range slider using the DateSlider module.
     *
     * This replaces the previous 114-line inline implementation with a clean,
     * testable class that uses centralized DateUtils for all date math.
     */
    private initializeDateFilters(result: ProcessingResult) {
        try {
            // Create DateSlider instance with callbacks
            this.dateSlider = new DateSlider(
                'date-slider',
                'filter-start-date',
                'filter-end-date',
                'slider-values',
                {
                    onChange: (start, end) => {
                        console.log(`Date filter changed: ${start} to ${end}`);
                        this.applyDateFilter();
                    }
                }
            );

            // Initialize with processing result
            this.dateSlider.initialize(result);
        } catch (err) {
            console.error("Failed to initialize date slider:", err);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // FILE HANDLING
    // ═══════════════════════════════════════════════════════════════════════

    private handleDragOver(e: Event) {
        e.preventDefault();
        this.dom.dropZone.classList.add('drag-over');
    }

    private handleDragLeave(e: Event) {
        e.preventDefault();
        this.dom.dropZone.classList.remove('drag-over');
    }

    private handleDrop(e: DragEvent) {
        e.preventDefault();
        this.dom.dropZone.classList.remove('drag-over');
        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
            this.processFile(files[0]);
        }
    }

    private handleFileSelect(e: Event) {
        const target = e.target as HTMLInputElement;
        const files = target.files;
        if (files && files.length > 0) {
            this.processFile(files[0]);
        }
    }

    /**
     * Process uploaded Excel file
     */
    async processFile(file: File) {
        try {
            this.prepareUIForProcessing();

            // 1. Validate File
            if (!this.isValidExcelFile(file)) {
                this.errorUI.showError('Please upload an Excel file (.xlsx or .xls)');
                this.hideLoading();
                return;
            }

            // 2. Parse File
            this.showLoading(LOADING_MESSAGES.readingFile);
            const jsonData = await this.parseExcelFile(file);

            if (!this.isValidData(jsonData)) {
                this.errorUI.showError('Excel file appears to be empty');
                this.hideLoading();
                return;
            }
            this.jsonData = jsonData;

            // 3. Initialize Python
            this.showLoading(LOADING_MESSAGES.initPython);
            await this.pyodideService.initialize();

            // 4. Process Data
            this.showLoading(LOADING_MESSAGES.processing);
            const result = await this.pyodideService.processData(jsonData);

            // 5. Handle Results
            await this.handleProcessingResult(result);

        } catch (error) {
            this.handleProcessingError(error);
        }
    }

    private prepareUIForProcessing() {
        this.hideError();
        // Clear existing period filters on new file upload
        const startInput = document.getElementById('filter-start-date') as HTMLInputElement;
        const endInput = document.getElementById('filter-end-date') as HTMLInputElement;
        if (startInput) startInput.value = '';
        if (endInput) endInput.value = '';
    }

    private isValidExcelFile(file: File): boolean {
        return !!file.name.match(/\.xlsx?$/i);
    }

    private isValidData(data: any[]): boolean {
        return data && data.length > 0;
    }

    private async handleProcessingResult(result: ProcessingResult | ErrorResponse | ProcessingOutput) {
        if (!result.success) {
            this.errorUI.showError(result);
            this.hideLoading();
            return;
        }

        const successResult = result as ProcessingResult;

        // Show warnings if any
        if (successResult.quality && (
            (successResult.quality.warnings && successResult.quality.warnings.length > 0) ||
            (successResult.quality.info && successResult.quality.info.length > 0)
        )) {
            this.errorUI.showWarnings(successResult.quality);
        }

        // Render UI
        // Render UI
        this.showLoading(LOADING_MESSAGES.rendering);
        this.processedData = successResult;

        // Reveal results section FIRST so Plotly can calculate correct width
        this.showResults();

        this.renderResults();

        this.hideLoading();

        // Initialize Slider
        this.initializeDateFilters(successResult);
    }

    private handleProcessingError(error: unknown) {
        this.hideLoading();
        console.error('Processing error:', error);

        let msg = "Unknown error occurred";
        if (typeof error === 'string') {
            msg = error;
        } else if (error instanceof Error) {
            msg = error.message;
        } else if (typeof error === 'object' && error !== null) {
            const errObj = error as any;
            if (errObj.message) msg = errObj.message;
            else if (errObj.error) msg = errObj.error;
            else {
                try {
                    msg = JSON.stringify(error);
                } catch (e) {
                    msg = "Error object could not be stringified";
                }
            }
        }

        this.errorUI.showError(`Error processing file: ${msg}`);
    }

    /**
     * Parse Excel file to JSON using SheetJS
     */
    async parseExcelFile(file: File): Promise<any[]> {
        const arrayBuffer = await file.arrayBuffer();
        // Use cellDates: true to force date parsing
        const workbook = XLSX.read(arrayBuffer, { type: 'array', cellDates: true });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        return XLSX.utils.sheet_to_json(firstSheet);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // UI STATE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════════

    public updateLoadingText(message: string) {
        if (this.dom.loadingText) {
            this.dom.loadingText.textContent = message;
        }
    }

    public showLoading(message: string) {
        this.updateLoadingText(message);
        this.dom.loadingIndicator.classList.remove('hidden');
    }

    public hideLoading() {
        this.dom.loadingIndicator.classList.add('hidden');
    }

    public hideError() {
        this.dom.errorMessage.classList.add('hidden');
        this.errorUI.clearAll();
    }

    public showResults() {
        this.dom.uploadSection.classList.add('hidden');
        this.dom.resultsSection.classList.remove('hidden');

        // Show header controls
        this.dom.headerControls.classList.remove('hidden');
        this.dom.headerControls.style.display = 'flex';

        // Trigger animations
        requestAnimationFrame(() => {
            this.dom.resultsSection.classList.add('is-visible');
        });
    }

    public resetToUpload() {
        this.dom.resultsSection.classList.add('hidden');
        this.dom.resultsSection.classList.remove('is-visible');
        this.dom.uploadSection.classList.remove('hidden');

        // Hide header controls
        this.dom.headerControls.classList.add('hidden');
        this.dom.headerControls.style.display = 'none';

        this.dom.fileInput.value = '';
        this.hideError();
        this.errorUI.clearAll();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // RESULT RENDERING
    // ═══════════════════════════════════════════════════════════════════════

    private renderResults() {
        if (!this.processedData) return;
        try {
            this.renderSummary();
        } catch (e) {
            console.error('Error rendering summary:', e);
        }

        try {
            this.renderTables();
        } catch (e) {
            console.error('Error rendering tables:', e);
        }

        try {
            this.renderCharts();
        } catch (e) {
            console.error('Error rendering charts:', e);
        }
    }

    private renderSummary() {
        if (!this.processedData) return;
        const summary = this.processedData.summary;
        document.getElementById('summary-rows')!.textContent = summary.record_count.toString();
        document.getElementById('summary-metrics')!.textContent = summary.metric_count.toString();
        document.getElementById('summary-missing')!.textContent = summary.missing_newscast.toString();
    }

    private renderTables() {
        if (!this.processedData) return;
        const tables = this.processedData.tables;

        // Overall metrics
        this.tableRenderer.render('table-overall', tables.overall, ['Question', 'Yes %'], this.processedData.config);

        // Data quality
        this.tableRenderer.render('table-quality', tables.data_quality, ['Question', 'Complete %', 'Missing'], this.processedData.config);

        // Recent week
        const recentCard = document.getElementById('recent-week-card');
        if (tables.recent && recentCard) {
            recentCard.classList.remove('hidden');
            document.getElementById('recent-week-title')!.textContent =
                `Week of ${tables.recent_week_start}`;
            this.tableRenderer.render('table-recent', tables.recent, ['Question', 'Yes %'], this.processedData.config);
        } else if (recentCard) {
            recentCard.classList.add('hidden');
        }

        // Volume by newscast
        if (tables.volume) {
            this.tableRenderer.render('table-volume', tables.volume, ['Newscast', 'Responses'], this.processedData.config);
        }

        // User Accountability
        if (tables.users) {
            this.tableRenderer.render('table-users', tables.users, ['User', 'Audits', 'Completeness', 'Most Missed Metric'], this.processedData.config);
        }
    }

    private renderCharts() {
        if (!this.processedData) return;
        const charts = this.processedData.charts;
        const config = this.processedData.config;

        // Render Charts
        this.chartRenderer.renderOverallChart('chart-overall', charts.overall, config);
        this.chartRenderer.renderPerNewscastCharts('charts-per-newscast', charts.per_newscast, config);

        // Render Weekly Chart
        if (charts.weekly) {
            this.chartRenderer.renderWeeklyChart('chart-weekly', charts.weekly, config);
        }

        // Initialize Weekly Chart Filter
        if (charts.filter_options && charts.filter_options.length > 0) {
            const select = document.getElementById('weekly-chart-filter') as HTMLSelectElement;
            if (select) {
                select.innerHTML = '';
                charts.filter_options.forEach((opt: any, index: number) => {
                    const option = document.createElement('option');
                    option.value = index.toString();
                    option.textContent = opt.label;
                    select.appendChild(option);
                });

                select.onchange = () => {
                    const selectedIndex = parseInt(select.value);
                    const selectedData = charts.filter_options![selectedIndex];
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
                            this.chartRenderer.renderWeeklyChart('chart-weekly', weeklyData, config);
                        } catch (e) {
                            console.error("Error updating chart:", e);
                        }
                    }
                };
            }
        }

        // Render Heatmap
        if (charts.per_newscast && charts.per_newscast.length > 0) {
            this.chartRenderer.renderHeatmap('chart-heatmap', charts.per_newscast, config);
        }

        // Render Comments
        if (this.processedData.comments) {
            this.commentRenderer.renderComments('comments-feed', this.processedData.comments);
        }
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
