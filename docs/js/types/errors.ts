/**
 * Error response types.
 *
 * These types mirror the Pydantic schemas in docs/lib/schemas/errors.py
 * and define error response structures from the Python backend.
 */

/**
 * Detailed error information.
 */
export interface ErrorDetail {
    /** Type of error (DataValidationError, ProcessingError, etc.) */
    error_type: string;
    /** Human-readable error message */
    message: string;
    /** Additional error context (e.g., missing_columns, found_columns) */
    details: Record<string, unknown>;
    /** Suggested action for the user to resolve the error */
    user_action: string;
}

/**
 * Error response structure.
 */
export interface ErrorResponse {
    /** Always false for errors */
    success: false;
    /** Error details */
    error: ErrorDetail;
}
