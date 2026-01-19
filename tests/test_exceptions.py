"""
Tests for custom exception classes.

Validates that exceptions serialize correctly and provide appropriate
user-actionable guidance.
"""

import sys
import pytest
from pathlib import Path

# Add docs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs'))

from lib.exceptions import (
    NewscastAuditError,
    DataValidationError,
    DataQualityWarning,
    ProcessingError,
    ConfigurationError,
    EmptyDataError,
    InsufficientDataError,
    create_error_response,
)


class TestNewscastAuditError:
    """Test base exception class."""

    def test_basic_instantiation(self):
        """Base error can be instantiated with just a message."""
        error = NewscastAuditError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_instantiation_with_details(self):
        """Base error accepts optional details dict."""
        details = {"key": "value", "count": 42}
        error = NewscastAuditError("Error message", details=details)
        assert error.details == details

    def test_to_dict_serialization(self):
        """to_dict() returns expected structure."""
        error = NewscastAuditError("Test error", details={"foo": "bar"})
        result = error.to_dict()

        assert result["error_type"] == "NewscastAuditError"
        assert result["message"] == "Test error"
        assert result["details"] == {"foo": "bar"}
        assert "user_action" in result

    def test_get_user_action_default(self):
        """Base class provides default user action."""
        error = NewscastAuditError("Error")
        assert "contact support" in error.get_user_action().lower()


class TestDataValidationError:
    """Test validation error class."""

    def test_instantiation_with_missing_columns(self):
        """Can specify missing columns."""
        error = DataValidationError(
            "Missing columns",
            missing_columns=["col1", "col2"]
        )
        assert error.missing_columns == ["col1", "col2"]
        assert error.details["missing_columns"] == ["col1", "col2"]

    def test_instantiation_with_found_columns(self):
        """Can specify found columns for debugging."""
        error = DataValidationError(
            "Missing columns",
            missing_columns=["expected"],
            found_columns=["actual1", "actual2"]
        )
        assert error.found_columns == ["actual1", "actual2"]
        assert error.details["found_columns"] == ["actual1", "actual2"]

    def test_user_action_mentions_missing_columns(self):
        """User action includes missing column names."""
        error = DataValidationError(
            "Missing columns",
            missing_columns=["Date of newscast", "Newscast name"]
        )
        action = error.get_user_action()
        assert "Date of newscast" in action
        assert "Microsoft Forms" in action

    def test_user_action_without_missing_columns(self):
        """User action still helpful without column details."""
        error = DataValidationError("Generic validation error")
        action = error.get_user_action()
        assert "Excel file" in action or "correct file" in action.lower()


class TestDataQualityWarning:
    """Test quality warning class."""

    def test_instantiation_basic(self):
        """Can be created with just a message."""
        warning = DataQualityWarning("Some issue detected")
        assert warning.message == "Some issue detected"
        assert warning.issue_count == 0

    def test_instantiation_with_count(self):
        """Tracks issue count."""
        warning = DataQualityWarning("Bad dates", issue_count=5)
        assert warning.issue_count == 5
        assert warning.details["issue_count"] == 5

    def test_affected_rows_limited(self):
        """Affected rows limited to first 10."""
        many_rows = list(range(100))
        warning = DataQualityWarning("Issues", affected_rows=many_rows)
        assert len(warning.details["affected_rows"]) == 10
        assert warning.affected_rows == many_rows  # Original preserved

    def test_examples_limited(self):
        """Examples limited to 5."""
        many_examples = [f"example_{i}" for i in range(20)]
        warning = DataQualityWarning("Issues", examples=many_examples)
        assert len(warning.details["examples"]) == 5

    def test_user_action_includes_examples(self):
        """User action shows example values."""
        warning = DataQualityWarning(
            "Unknown values",
            examples=["5-7", "Morning", "Evening"]
        )
        action = warning.get_user_action()
        assert "5-7" in action or "example" in action.lower()


class TestProcessingError:
    """Test processing error class."""

    def test_instantiation_with_operation(self):
        """Requires operation name."""
        error = ProcessingError("Failed", operation="data_cleaning")
        assert error.operation == "data_cleaning"
        assert error.details["operation"] == "data_cleaning"

    def test_instantiation_with_original_error(self):
        """Captures original exception."""
        original = ValueError("Original problem")
        error = ProcessingError(
            "Processing failed",
            operation="aggregation",
            original_error=original
        )
        assert error.original_error is original
        assert "Original problem" in error.details["original_error"]

    def test_user_action_mentions_operation(self):
        """User action includes operation name."""
        error = ProcessingError("Failed", operation="chart_generation")
        action = error.get_user_action()
        assert "chart_generation" in action


class TestConfigurationError:
    """Test configuration error class."""

    def test_basic_instantiation(self):
        """Can be created with just a message."""
        error = ConfigurationError("Invalid config")
        assert error.message == "Invalid config"

    def test_with_config_key(self):
        """Can specify which config key is problematic."""
        error = ConfigurationError("Missing key", config_key="THRESHOLD_GOOD")
        assert error.details["config_key"] == "THRESHOLD_GOOD"

    def test_with_expected_type(self):
        """Can specify expected type."""
        error = ConfigurationError(
            "Wrong type",
            config_key="PORT",
            expected_type="integer"
        )
        assert error.details["expected_type"] == "integer"

    def test_user_action_mentions_admin(self):
        """User action directs to admin."""
        error = ConfigurationError("Config issue")
        action = error.get_user_action()
        assert "administrator" in action.lower()


class TestEmptyDataError:
    """Test empty data error class."""

    def test_instantiation(self):
        """Creates appropriate message with row count."""
        error = EmptyDataError(row_count=0)
        assert "0 rows" in error.message
        assert error.details["row_count"] == 0

    def test_inherits_from_validation_error(self):
        """Is a subclass of DataValidationError."""
        error = EmptyDataError()
        assert isinstance(error, DataValidationError)
        assert isinstance(error, NewscastAuditError)

    def test_user_action_mentions_empty(self):
        """User action explains the file is empty."""
        error = EmptyDataError(row_count=0)
        action = error.get_user_action()
        assert "empty" in action.lower()


class TestInsufficientDataError:
    """Test insufficient data error class."""

    def test_instantiation(self):
        """Creates appropriate message with counts."""
        error = InsufficientDataError(
            initial_count=100,
            final_count=5,
            dropped_count=95
        )
        assert "5" in error.message
        assert "95" in error.message
        assert error.details["initial_count"] == 100
        assert error.details["final_count"] == 5
        assert error.details["dropped_count"] == 95

    def test_inherits_from_validation_error(self):
        """Is a subclass of DataValidationError."""
        error = InsufficientDataError(100, 5, 95)
        assert isinstance(error, DataValidationError)

    def test_user_action_mentions_dropped_rows(self):
        """User action explains rows were dropped."""
        error = InsufficientDataError(100, 5, 95)
        action = error.get_user_action()
        assert "dropped" in action.lower() or "missing" in action.lower()


class TestCreateErrorResponse:
    """Test error response factory function."""

    def test_handles_newscast_audit_error(self):
        """Converts NewscastAuditError to dict."""
        error = DataValidationError("Bad data", missing_columns=["col1"])
        response = create_error_response(error)

        assert response["error_type"] == "DataValidationError"
        assert response["message"] == "Bad data"
        assert "col1" in response["details"]["missing_columns"]
        assert "user_action" in response

    def test_handles_unexpected_error(self):
        """Handles arbitrary exceptions gracefully."""
        error = RuntimeError("Something unexpected")
        response = create_error_response(error)

        assert response["error_type"] == "UnexpectedError"
        assert "unexpected" in response["message"].lower()
        assert response["details"]["exception_type"] == "RuntimeError"
        assert "Something unexpected" in response["details"]["exception_message"]
        assert "user_action" in response

    def test_handles_value_error(self):
        """Handles ValueError as unexpected."""
        error = ValueError("Bad value")
        response = create_error_response(error)

        assert response["error_type"] == "UnexpectedError"
        assert response["details"]["exception_type"] == "ValueError"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
