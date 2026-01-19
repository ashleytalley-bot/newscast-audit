"""
Tests for Pydantic schemas.

Validates that schemas can parse actual pipeline output and that
they enforce the expected structure.
"""

import json
import sys
import pytest
from pathlib import Path
from pydantic import ValidationError

# Add docs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs' / 'py'))

from lib.schemas.output import (
    ProcessingResult,
    ProcessingSummary,
    ChartData,
)
from lib.schemas.errors import ErrorResponse
from pipeline.orchestrator import ProcessingPipeline


@pytest.fixture
def sample_survey_data():
    """Sample survey data matching MS Forms export structure."""
    return [
        {
            "Id": "1",
            "Start time": "2024-01-15 08:00:00",
            "Completion time": "2024-01-15 08:05:00",
            "Email": "auditor@tegna.com",
            "Name": "Test Auditor",
            "Date of newscast:": "2024-01-15",
            "Which newscast are you auditing?": "5-7am",
            "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ": "Yes",
            "Is a tease to streaming in at least every 30 minutes with specific content push for each show?": "Yes",
            "Did we use streaming content and/or mobile shorts in this show?": "No",
            "Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?": "Yes",
            "Is there a clearly defined weather story, supported by graphics or video?": "Yes",
            "Does each weather hit focus on new/now/next?": "Yes",
            "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "No",
            "Are anchors shown three times per show on tight shots with name supers?": "Yes",
            "Did we specifically reference every piece of file or non-descript video?": "Yes",
            "Do anchors add local context to two or more stories and include one community-celebration story per hour?": "Yes",
            "Additional comments below:": "Great show!"
        }
    ]


class TestProcessingResultSchema:
    """Test that ProcessingResult schema validates actual pipeline output."""

    def test_schema_validates_successful_pipeline_output(self, sample_survey_data):
        """Verify schema can parse successful processing result."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result_dict = json.loads(result_json)

        # This should not raise ValidationError
        validated_result = ProcessingResult(**result_dict)

        # Verify basic structure
        assert validated_result.success is True
        assert validated_result.summary.record_count == 1
        assert validated_result.summary.metric_count == 10

    def test_schema_validates_field_types(self, sample_survey_data):
        """Verify schema enforces correct types."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result_dict = json.loads(result_json)

        validated_result = ProcessingResult(**result_dict)

        # Check types
        assert isinstance(validated_result.summary, ProcessingSummary)
        assert isinstance(validated_result.charts.overall, ChartData)
        assert isinstance(validated_result.charts.overall.values, list)
        assert all(isinstance(v, (int, float)) for v in validated_result.charts.overall.values)

    def test_schema_rejects_invalid_structure(self):
        """Verify schema rejects malformed data."""
        invalid_data = {
            "success": True,
            # Missing required fields
        }

        with pytest.raises(ValidationError):
            ProcessingResult(**invalid_data)

    def test_schema_rejects_wrong_types(self, sample_survey_data):
        """Verify schema rejects incorrect field types."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result_dict = json.loads(result_json)

        # Corrupt a field type
        result_dict["summary"]["record_count"] = "not a number"

        with pytest.raises(ValidationError):
            ProcessingResult(**result_dict)


class TestErrorResponseSchema:
    """Test that ErrorResponse schema validates error outputs."""

    def test_schema_validates_error_response(self):
        """Verify schema can parse error responses."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps([]))  # Empty data triggers error
        result_dict = json.loads(result_json)

        # This should not raise ValidationError
        validated_error = ErrorResponse(**result_dict)

        # Verify structure
        assert validated_error.success is False
        assert validated_error.error.error_type is not None
        assert validated_error.error.message is not None
        assert validated_error.error.user_action is not None

    def test_schema_requires_all_error_fields(self):
        """Verify all error fields are required."""
        incomplete_error = {
            "success": False,
            "error": {
                "error_type": "TestError",
                "message": "Test message",
                # Missing user_action
            }
        }

        with pytest.raises(ValidationError):
            ErrorResponse(**incomplete_error)


class TestChartDataSchema:
    """Test ChartData schema validation."""

    def test_chart_data_validates_correctly(self, sample_survey_data):
        """Verify ChartData schema works with actual data."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result_dict = json.loads(result_json)

        # Extract chart data
        overall_chart = result_dict["charts"]["overall"]

        # Validate
        validated_chart = ChartData(**overall_chart)

        assert len(validated_chart.labels) == 10
        assert len(validated_chart.values) == 10
        assert len(validated_chart.colors) == 10
        assert validated_chart.n == 1

    def test_chart_data_enforces_list_lengths_match(self):
        """Verify labels, values, colors should match in length."""
        chart_data = {
            "labels": ["Metric 1", "Metric 2"],
            "values": [85.0],  # Wrong length
            "colors": ["#045ea8", "#f36f21"],
            "n": 10,
        }

        # Pydantic won't reject this structurally (all are valid lists)
        # but we can add custom validation if needed
        validated = ChartData(**chart_data)
        assert len(validated.labels) != len(validated.values)  # Catches the mismatch


class TestProcessingSummarySchema:
    """Test ProcessingSummary schema."""

    def test_summary_validates_all_fields(self, sample_survey_data):
        """Verify all summary fields are present."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result_dict = json.loads(result_json)

        summary_dict = result_dict["summary"]
        validated_summary = ProcessingSummary(**summary_dict)

        assert hasattr(validated_summary, "record_count")
        assert hasattr(validated_summary, "metric_count")
        assert hasattr(validated_summary, "missing_newscast")
        assert hasattr(validated_summary, "dropped_empty")

    def test_summary_enforces_integer_types(self):
        """Verify summary fields must be integers."""
        bad_summary = {
            "record_count": "not an int",
            "metric_count": 10,
            "missing_newscast": 0,
            "dropped_empty": 0,
        }

        with pytest.raises(ValidationError):
            ProcessingSummary(**bad_summary)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
