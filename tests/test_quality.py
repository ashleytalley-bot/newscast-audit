"""
Tests for DataQualityTracker.

Validates warning and info message accumulation, example limiting,
and JSON serialization.
"""

import sys
import pytest
from pathlib import Path

# Add docs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs'))

from lib.quality import DataQualityTracker


class TestDataQualityTrackerInit:
    """Test initialization."""

    def test_starts_empty(self):
        """New tracker has no warnings or info."""
        tracker = DataQualityTracker()
        assert tracker.warnings == []
        assert tracker.info == []

    def test_has_warnings_initially_false(self):
        """has_warnings() returns False on new tracker."""
        tracker = DataQualityTracker()
        assert tracker.has_warnings() is False


class TestAddWarning:
    """Test warning accumulation."""

    def test_adds_warning_with_message(self):
        """Can add a warning with just a message."""
        tracker = DataQualityTracker()
        tracker.add_warning("Something is wrong")

        assert len(tracker.warnings) == 1
        assert tracker.warnings[0]["message"] == "Something is wrong"
        assert tracker.warnings[0]["level"] == "warning"

    def test_adds_warning_with_count(self):
        """Can track issue count."""
        tracker = DataQualityTracker()
        tracker.add_warning("Bad values", count=42)

        assert tracker.warnings[0]["count"] == 42

    def test_adds_warning_with_examples(self):
        """Can include example values."""
        tracker = DataQualityTracker()
        tracker.add_warning("Unknown formats", examples=["5-7", "Morning"])

        assert tracker.warnings[0]["examples"] == ["5-7", "Morning"]

    def test_examples_limited_to_five(self):
        """Examples are truncated to 5 items."""
        tracker = DataQualityTracker()
        many_examples = [f"example_{i}" for i in range(20)]
        tracker.add_warning("Too many", examples=many_examples)

        assert len(tracker.warnings[0]["examples"]) == 5
        assert tracker.warnings[0]["examples"] == many_examples[:5]

    def test_multiple_warnings_accumulate(self):
        """Multiple warnings can be added."""
        tracker = DataQualityTracker()
        tracker.add_warning("First issue")
        tracker.add_warning("Second issue")
        tracker.add_warning("Third issue")

        assert len(tracker.warnings) == 3

    def test_has_warnings_true_after_add(self):
        """has_warnings() returns True after adding."""
        tracker = DataQualityTracker()
        tracker.add_warning("Issue detected")

        assert tracker.has_warnings() is True


class TestAddInfo:
    """Test info message accumulation."""

    def test_adds_info_with_message(self):
        """Can add info with just a message."""
        tracker = DataQualityTracker()
        tracker.add_info("Processing completed")

        assert len(tracker.info) == 1
        assert tracker.info[0]["message"] == "Processing completed"
        assert tracker.info[0]["level"] == "info"

    def test_adds_info_with_details(self):
        """Can include additional details dict."""
        tracker = DataQualityTracker()
        tracker.add_info("Stats", details={"count": 100, "avg": 85.5})

        assert tracker.info[0]["count"] == 100
        assert tracker.info[0]["avg"] == 85.5

    def test_multiple_info_accumulate(self):
        """Multiple info messages can be added."""
        tracker = DataQualityTracker()
        tracker.add_info("Step 1 done")
        tracker.add_info("Step 2 done")

        assert len(tracker.info) == 2

    def test_info_does_not_affect_has_warnings(self):
        """Info messages don't count as warnings."""
        tracker = DataQualityTracker()
        tracker.add_info("Just FYI")

        assert tracker.has_warnings() is False


class TestToDict:
    """Test JSON serialization."""

    def test_empty_tracker_to_dict(self):
        """Empty tracker serializes to empty lists."""
        tracker = DataQualityTracker()
        result = tracker.to_dict()

        assert result == {"warnings": [], "info": []}

    def test_to_dict_includes_warnings(self):
        """Serializes warnings correctly."""
        tracker = DataQualityTracker()
        tracker.add_warning("Issue 1", count=5, examples=["a", "b"])
        tracker.add_warning("Issue 2", count=3)

        result = tracker.to_dict()

        assert len(result["warnings"]) == 2
        assert result["warnings"][0]["message"] == "Issue 1"
        assert result["warnings"][0]["count"] == 5
        assert result["warnings"][1]["message"] == "Issue 2"

    def test_to_dict_includes_info(self):
        """Serializes info messages correctly."""
        tracker = DataQualityTracker()
        tracker.add_info("Note 1")
        tracker.add_info("Note 2", details={"extra": "data"})

        result = tracker.to_dict()

        assert len(result["info"]) == 2
        assert result["info"][0]["message"] == "Note 1"
        assert result["info"][1]["extra"] == "data"

    def test_to_dict_combined(self):
        """Serializes both warnings and info."""
        tracker = DataQualityTracker()
        tracker.add_warning("Warning 1")
        tracker.add_info("Info 1")
        tracker.add_warning("Warning 2")

        result = tracker.to_dict()

        assert len(result["warnings"]) == 2
        assert len(result["info"]) == 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_examples_list(self):
        """Empty examples list is handled."""
        tracker = DataQualityTracker()
        tracker.add_warning("No examples", examples=[])

        assert tracker.warnings[0]["examples"] == []

    def test_none_examples_becomes_empty_list(self):
        """None examples defaults to empty list."""
        tracker = DataQualityTracker()
        tracker.add_warning("No examples", examples=None)

        assert tracker.warnings[0]["examples"] == []

    def test_zero_count(self):
        """Zero count is valid."""
        tracker = DataQualityTracker()
        tracker.add_warning("Zero issues", count=0)

        assert tracker.warnings[0]["count"] == 0

    def test_none_details_does_not_add_keys(self):
        """None details doesn't pollute info dict."""
        tracker = DataQualityTracker()
        tracker.add_info("Simple message", details=None)

        # Should only have level and message
        assert set(tracker.info[0].keys()) == {"level", "message"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
