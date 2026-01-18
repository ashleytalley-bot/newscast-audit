"""
Custom exceptions for newscast audit processing.

Provides structured error hierarchy with detailed context for better debugging
and user-friendly error messages.
"""

from typing import List, Dict, Any, Optional


class NewscastAuditError(Exception):
    """
    Base exception for all newscast audit errors.

    All custom exceptions inherit from this to allow catching all
    audit-related errors with a single except clause.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize audit error with message and optional details.

        Args:
            message: Human-readable error message
            details: Additional context about the error (for debugging/logging)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for JSON serialization.

        Returns:
            Dictionary with error_type, message, and details
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "user_action": self.get_user_action()
        }

    def get_user_action(self) -> str:
        """
        Get user-actionable guidance for fixing this error.

        Returns:
            String describing what the user should do
        """
        return "Please contact support with the error details above."


class DataValidationError(NewscastAuditError):
    """
    Raised when input data fails validation checks.

    Examples:
        - Missing required columns
        - Wrong file format
        - Empty file
    """

    def __init__(self, message: str, missing_columns: Optional[List[str]] = None,
                 found_columns: Optional[List[str]] = None):
        details = {}
        if missing_columns:
            details["missing_columns"] = missing_columns
        if found_columns:
            details["found_columns"] = found_columns

        super().__init__(message, details)
        self.missing_columns = missing_columns or []
        self.found_columns = found_columns or []

    def get_user_action(self) -> str:
        if self.missing_columns:
            return (
                f"Ensure you're uploading the correct file. "
                f"The file should contain these columns: {', '.join(self.missing_columns)}. "
                f"Check that you exported the newscast audit survey from Microsoft Forms."
            )
        return "Verify you uploaded the correct Excel file from the newscast audit survey."


class DataQualityWarning(NewscastAuditError):
    """
    Raised for data quality issues that don't prevent processing.

    Examples:
        - Invalid dates that can be coerced
        - Unknown newscast formats
        - Unexpected values in metric columns
    """

    def __init__(self, message: str, issue_count: int = 0,
                 affected_rows: Optional[List[int]] = None,
                 examples: Optional[List[str]] = None):
        details = {
            "issue_count": issue_count,
            "severity": "warning"
        }
        if affected_rows:
            details["affected_rows"] = affected_rows[:10]  # Limit to first 10
        if examples:
            details["examples"] = examples[:5]  # Limit to 5 examples

        super().__init__(message, details)
        self.issue_count = issue_count
        self.affected_rows = affected_rows or []
        self.examples = examples or []

    def get_user_action(self) -> str:
        action = "The data was processed, but there are quality issues. "
        if self.examples:
            action += f"Review these examples: {', '.join(self.examples[:3])}. "
        return action + "Consider cleaning the source data to improve accuracy."


class ProcessingError(NewscastAuditError):
    """
    Raised when data processing fails unexpectedly.

    Examples:
        - Pandas operations fail
        - Unexpected data types
        - Memory issues
    """

    def __init__(self, message: str, operation: str,
                 original_error: Optional[Exception] = None):
        details = {
            "operation": operation,
            "original_error": str(original_error) if original_error else None
        }
        super().__init__(message, details)
        self.operation = operation
        self.original_error = original_error

    def get_user_action(self) -> str:
        return (
            f"Processing failed during: {self.operation}. "
            "This might be due to corrupted data or an unexpected file format. "
            "Try re-exporting the data from Microsoft Forms and uploading again."
        )


class ConfigurationError(NewscastAuditError):
    """
    Raised when configuration is invalid or missing.

    Examples:
        - Missing environment variables
        - Invalid configuration values
        - Module import failures
    """

    def __init__(self, message: str, config_key: Optional[str] = None,
                 expected_type: Optional[str] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if expected_type:
            details["expected_type"] = expected_type

        super().__init__(message, details)

    def get_user_action(self) -> str:
        return "This is a configuration issue. Please contact the system administrator."


class EmptyDataError(DataValidationError):
    """Raised when the uploaded file contains no data."""

    def __init__(self, row_count: int = 0):
        super().__init__(
            f"The Excel file contains {row_count} rows of data. Cannot process empty file.",
            missing_columns=None,
            found_columns=None
        )
        self.details["row_count"] = row_count

    def get_user_action(self) -> str:
        return (
            "The uploaded file appears to be empty. "
            "Ensure you're uploading an Excel file that contains survey responses."
        )


class InsufficientDataError(DataValidationError):
    """Raised when there's not enough data after cleaning."""

    def __init__(self, initial_count: int, final_count: int, dropped_count: int):
        super().__init__(
            f"Only {final_count} valid responses remain after cleaning "
            f"({dropped_count} of {initial_count} rows were dropped)."
        )
        self.details.update({
            "initial_count": initial_count,
            "final_count": final_count,
            "dropped_count": dropped_count
        })

    def get_user_action(self) -> str:
        return (
            "Most rows were dropped due to missing data. "
            "Review the source survey to ensure responses are complete. "
            "Check that all required questions are being answered."
        )


def create_error_response(error: Exception) -> Dict[str, Any]:
    """
    Create a structured error response from any exception.

    Args:
        error: The exception that was raised

    Returns:
        Dictionary suitable for JSON serialization with error details
    """
    if isinstance(error, NewscastAuditError):
        return error.to_dict()

    # Handle unexpected errors
    return {
        "error_type": "UnexpectedError",
        "message": f"An unexpected error occurred: {str(error)}",
        "details": {
            "exception_type": type(error).__name__,
            "exception_message": str(error)
        },
        "user_action": (
            "An unexpected error occurred. Please try again. "
            "If the problem persists, contact support with this error message."
        )
    }
