/**
 * Type definitions for Newscast Audit application.
 *
 * These types mirror the Pydantic schemas in docs/lib/schemas/
 * and ensure type safety between Python backend and TypeScript frontend.
 */

// Export all output types
export type {
    ProcessingSummary,
    ChartData,
    PerNewscastChart,
    WeeklyChart,
    FilterOption,
    ChartsCollection,
    TablesCollection,
    QualityWarning,
    QualityInfo,
    QualityReport,
    ExportData,
    ConfigPassthrough,
    ProcessingResult,
} from './output';

// Export all error types
export type {
    ErrorDetail,
    ErrorResponse,
} from './errors';

import type { ProcessingResult } from './output';
import type { ErrorResponse } from './errors';

/**
 * Union type for all possible processing outputs.
 * The pipeline returns either a success result or an error response.
 */
export type ProcessingOutput = ProcessingResult | ErrorResponse;

/**
 * Type guard to check if output is a success result.
 */
export function isProcessingResult(output: ProcessingOutput): output is ProcessingResult {
    return output.success === true;
}

/**
 * Type guard to check if output is an error response.
 */
export function isErrorResponse(output: ProcessingOutput): output is ErrorResponse {
    return output.success === false;
}
