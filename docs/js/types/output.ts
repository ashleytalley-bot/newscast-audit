/**
 * Output types for pipeline processing results.
 *
 * These types mirror the Pydantic schemas in docs/lib/schemas/output.py
 * and define the contract between Python backend and JavaScript frontend.
 */

/**
 * Summary statistics about the processing run.
 */
export interface ProcessingSummary {
    /** Number of audit records processed */
    record_count: number;
    /** Number of metrics tracked (should be 10) */
    metric_count: number;
    /** Number of records with missing/invalid newscast names */
    missing_newscast: number;
    /** Number of records dropped due to having no metric data */
    dropped_empty: number;
}

/**
 * Data for an overall performance chart.
 */
export interface ChartData {
    /** Human-readable metric names */
    labels: string[];
    /** Percentage values (0-100) for each metric */
    values: number[];
    /** Hex color codes for each bar (from palette) */
    colors: string[];
    /** Number of audits included in this chart */
    n: number;
}

/**
 * Chart data for a specific newscast timeslot.
 */
export interface PerNewscastChart extends ChartData {
    /** Newscast timeslot label (e.g., '5 - 7 am', '6 pm') */
    newscast: string;
}

/**
 * Time series data for weekly trends.
 */
export interface WeeklyChart {
    /** Short date labels (MM/DD format) */
    dates: string[];
    /** Weekly average percentages (can be null for missing weeks) */
    values: (number | null)[];
    /** Full ISO date strings (YYYY-MM-DD) */
    full_dates: string[];
    /** Process center line (mean) */
    center_line?: number | null;
    /** Upper Control Limit values */
    ucl?: (number | null)[] | null;
    /** Lower Control Limit values */
    lcl?: (number | null)[] | null;
}

/**
 * Interactive filter option for weekly trends.
 */
export interface FilterOption {
    /** Filter label shown in dropdown */
    label: string;
    /** Full ISO dates for this filtered series */
    dates: string[];
    /** Weekly percentages for this filter */
    values: (number | null)[];
    /** Process center line (mean) */
    center_line?: number | null;
    /** Upper Control Limit values */
    ucl?: (number | null)[] | null;
    /** Lower Control Limit values */
    lcl?: (number | null)[] | null;
}

/**
 * Collection of all chart data.
 */
export interface ChartsCollection {
    /** Overall performance across all newscasts */
    overall: ChartData;
    /** Performance broken down by newscast timeslot */
    per_newscast: PerNewscastChart[];
    /** Weekly trends over time (null if no date data) */
    weekly: WeeklyChart | null;
    /** Interactive filter options for weekly chart */
    filter_options: FilterOption[];
    /** Min and max dates from raw data for slider */
    date_range: { min: string | null; max: string | null } | null;
}

/**
 * Collection of all summary tables.
 */
export interface TablesCollection {
    /** Overall performance table (Question, Yes %, Count) */
    overall: Record<string, unknown>[];
    /** Data quality metrics (Question, Completeness %, Missing) */
    data_quality: Record<string, unknown>[];
    /** Recent week performance (null if no recent data) */
    recent: Record<string, unknown>[] | null;
    /** Start date of recent week (readable format) */
    recent_week_start: string | null;
    /** Audit volume by newscast */
    volume: Record<string, unknown>[] | null;
}

/**
 * A data quality warning.
 */
export interface QualityWarning {
    /** Severity level (always 'warning') */
    level: 'warning';
    /** Human-readable warning message */
    message: string;
    /** Number of occurrences */
    count: number;
    /** Example values that triggered this warning (max 5) */
    examples: string[];
}

/**
 * Informational quality message.
 */
export interface QualityInfo {
    /** Message level (always 'info') */
    level: 'info';
    /** Human-readable info message */
    message: string;
}

/**
 * Data quality tracking report.
 */
export interface QualityReport {
    /** Non-fatal data quality warnings */
    warnings: QualityWarning[];
    /** Informational messages */
    info: QualityInfo[];
}

/**
 * Data prepared for Excel/PowerPoint export.
 */
export interface ExportData {
    /** Cleaned and normalized audit records */
    normalized: Record<string, unknown>[];
    /** Overall performance table data */
    overall: Record<string, unknown>[];
    /** Recent week data */
    recent: Record<string, unknown>[];
    /** Volume by newscast */
    volume: Record<string, unknown>[];
    /** Data quality metrics */
    data_quality: Record<string, unknown>[];
    /** Weekly trends data */
    weekly: Record<string, unknown>;
}

/**
 * Configuration passed to frontend.
 */
export interface ConfigPassthrough {
    /** Color palette (primary, accent, alert, etc.) */
    palette: Record<string, string>;
    /** Performance thresholds (good, poor) */
    thresholds: Record<string, number>;
    /** List of metric column internal names */
    metric_columns: string[];
}

/**
 * A single user comment from the audit.
 */
export interface Comment {
    /** Date of the newscast */
    date: string;
    /** Newscast audited */
    newscast: string;
    /** The comment text */
    text: string;
}

/**
 * Successful processing result - the main output contract.
 */
export interface ProcessingResult {
    /** Always true for successful processing */
    success: true;
    /** Summary statistics */
    summary: ProcessingSummary;
    /** All summary tables */
    tables: TablesCollection;
    /** All chart data */
    charts: ChartsCollection;
    /** List of all additional comments */
    comments: Comment[];
    /** Data for export functionality */
    export_data: ExportData;
    /** Configuration for frontend */
    config: ConfigPassthrough;
    /** Data quality warnings and info */
    quality: QualityReport;
}
