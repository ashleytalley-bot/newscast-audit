"""
Error response schemas.

Defines the structure of error responses returned when processing fails.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ErrorDetail(BaseModel):
    """Detailed error information."""

    error_type: str = Field(
        description="Type of error (DataValidationError, ProcessingError, etc.)"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context (e.g., missing_columns, found_columns)"
    )
    user_action: str = Field(
        description="Suggested action for the user to resolve the error"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_type": "DataValidationError",
                "message": "Excel file is missing required columns.",
                "details": {
                    "missing_columns": ["Which newscast are you auditing?"],
                    "found_columns": ["Id", "Name", "Email"],
                },
                "user_action": "Ensure you're uploading the correct Excel file from Microsoft Forms export.",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response structure."""

    success: bool = Field(
        default=False,
        description="Always false for errors"
    )
    error: ErrorDetail = Field(
        description="Error details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Error response returned when processing fails",
            "example": {
                "success": False,
                "error": {
                    "error_type": "EmptyDataError",
                    "message": "Excel file contains no data rows.",
                    "details": {"row_count": 0},
                    "user_action": "Upload a file with at least one audit response.",
                },
            },
        }
    )
