"""
Integration tests for the full processing pipeline.

These tests ensure the pipeline produces the expected output structure
and that schema changes don't break compatibility with the frontend.
"""

import json
import sys
import pytest
from pathlib import Path

# Add docs/py to path for pipeline imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs' / 'py'))

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
        },
        {
            "Id": "2",
            "Start time": "2024-01-15 18:00:00",
            "Completion time": "2024-01-15 18:05:00",
            "Email": "auditor@tegna.com",
            "Name": "Test Auditor",
            "Date of newscast:": "2024-01-15",
            "Which newscast are you auditing?": "6pm",
            "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ": "Yes",
            "Is a tease to streaming in at least every 30 minutes with specific content push for each show?": "No",
            "Did we use streaming content and/or mobile shorts in this show?": "Yes",
            "Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?": "Yes",
            "Is there a clearly defined weather story, supported by graphics or video?": "Yes",
            "Does each weather hit focus on new/now/next?": "No",
            "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "Yes",
            "Are anchors shown three times per show on tight shots with name supers?": "Yes",
            "Did we specifically reference every piece of file or non-descript video?": "No",
            "Do anchors add local context to two or more stories and include one community-celebration story per hour?": "Yes",
            "Additional comments below:": ""
        }
    ]


class TestPipelineOutputStructure:
    """Test that pipeline output matches expected structure."""

    def test_successful_processing_returns_expected_top_level_keys(
        self, sample_survey_data
    ):
        """Verify top-level response structure."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        # Top-level keys
        assert result["success"] is True
        assert "summary" in result
        assert "tables" in result
        assert "charts" in result
        assert "export_data" in result
        assert "config" in result
        assert "quality" in result

    def test_summary_contains_expected_fields(
        self, sample_survey_data
    ):
        """Verify summary statistics structure."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        summary = result["summary"]
        assert "record_count" in summary
        assert "metric_count" in summary
        assert "missing_newscast" in summary
        assert "dropped_empty" in summary

        # Validate values are reasonable
        assert summary["record_count"] == 2
        assert summary["metric_count"] == 10
        assert summary["missing_newscast"] == 0
        assert summary["dropped_empty"] == 0

    def test_tables_structure(self, sample_survey_data):
        """Verify tables output structure."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        tables = result["tables"]
        assert "overall" in tables
        assert "data_quality" in tables
        assert "recent" in tables
        assert "recent_week_start" in tables
        assert "volume" in tables

        # Overall table should be a list of dicts
        assert isinstance(tables["overall"], list)
        assert len(tables["overall"]) > 0

        # Each row should have Question and Yes %
        first_row = tables["overall"][0]
        assert "Question" in first_row
        assert "Yes %" in first_row

    def test_charts_structure(self, sample_survey_data):
        """Verify charts output structure."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        charts = result["charts"]
        assert "overall" in charts
        assert "per_newscast" in charts
        assert "weekly" in charts
        assert "filter_options" in charts

        # Overall chart structure
        overall = charts["overall"]
        assert "labels" in overall
        assert "values" in overall
        assert "colors" in overall
        assert "n" in overall

        assert isinstance(overall["labels"], list)
        assert isinstance(overall["values"], list)
        assert isinstance(overall["colors"], list)
        assert overall["n"] == 2

    def test_config_passthrough(self, sample_survey_data):
        """Verify config is passed through to frontend."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        config = result["config"]
        assert "palette" in config
        assert "thresholds" in config
        assert "metric_columns" in config

        # Verify palette colors
        palette = config["palette"]
        assert "primary" in palette
        assert "accent" in palette
        assert "alert" in palette

        # Verify thresholds
        thresholds = config["thresholds"]
        assert "good" in thresholds
        assert "poor" in thresholds

    def test_quality_warnings_structure(self, sample_survey_data):
        """Verify quality tracking structure."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        quality = result["quality"]
        assert "warnings" in quality
        assert "info" in quality

        assert isinstance(quality["warnings"], list)
        assert isinstance(quality["info"], list)


class TestPipelineErrorHandling:
    """Test error responses match expected structure."""

    def test_empty_data_returns_error_structure(self):
        """Verify error response for empty data."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps([]))
        result = json.loads(result_json)

        assert result["success"] is False
        assert "error" in result

        error = result["error"]
        assert "error_type" in error
        assert "message" in error
        assert "user_action" in error

    def test_missing_columns_returns_validation_error(self):
        """Verify error response for missing columns."""
        bad_data = [{"Id": "1", "Name": "Test"}]  # Missing required columns

        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(bad_data))
        result = json.loads(result_json)

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["error_type"] == "DataValidationError"

    def test_invalid_json_returns_processing_error(self):
        """Verify error response for invalid JSON."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute("not valid json{[")
        result = json.loads(result_json)

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["error_type"] == "ProcessingError"


class TestPipelineDataProcessing:
    """Test actual data processing logic."""

    def test_newscast_normalization(self, sample_survey_data):
        """Verify newscast names are normalized correctly."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        # Check per-newscast charts have normalized names
        per_newscast = result["charts"]["per_newscast"]
        newscasts = [chart["newscast"] for chart in per_newscast]

        assert "5 - 7 am" in newscasts  # "5-7am" normalized
        assert "6 pm" in newscasts      # "6pm" normalized

    def test_metric_calculations(self, sample_survey_data):
        """Verify metric percentages are calculated correctly."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        # Overall chart should have values
        overall = result["charts"]["overall"]
        values = overall["values"]

        # All values should be between 0-100
        assert all(0 <= v <= 100 for v in values)

        # Should have 10 metrics
        assert len(values) == 10

    def test_color_coding(self, sample_survey_data):
        """Verify colors are assigned based on thresholds."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        overall = result["charts"]["overall"]
        colors = overall["colors"]

        # Should have colors for all metrics
        assert len(colors) == 10

        # Colors should be from palette
        palette = result["config"]["palette"]
        valid_colors = [palette["primary"], palette["accent"], palette["alert"]]

        assert all(c in valid_colors for c in colors)


class TestPipelineExportData:
    """Test export data preparation."""

    def test_export_data_contains_all_sections(
        self, sample_survey_data
    ):
        """Verify export data has all expected sections."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        export_data = result["export_data"]

        assert "normalized" in export_data
        assert "overall" in export_data
        assert "recent" in export_data
        assert "volume" in export_data
        assert "data_quality" in export_data
        assert "weekly" in export_data

    def test_export_normalized_data_preserves_records(
        self, sample_survey_data
    ):
        """Verify normalized data preserves all records."""
        pipeline = ProcessingPipeline()
        result_json = pipeline.execute(json.dumps(sample_survey_data))
        result = json.loads(result_json)

        normalized = result["export_data"]["normalized"]
        assert len(normalized) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
