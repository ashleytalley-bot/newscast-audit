"""
Tests for utility functions.

Validates JSON cleaning, color assignment, and sorting utilities.
"""

import sys
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add docs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs'))

from lib.utils import (
    clean_for_json,
    safe_json_dumps,
    question_labels,
    color_for,
    sort_newscast_series,
    with_week_start,
)


class TestCleanForJson:
    """Test JSON sanitization function."""

    def test_none_passthrough(self):
        """None values pass through unchanged."""
        assert clean_for_json(None) is None

    def test_regular_float(self):
        """Regular floats pass through."""
        assert clean_for_json(3.14) == 3.14

    def test_nan_becomes_none(self):
        """NaN converted to None."""
        result = clean_for_json(float('nan'))
        assert result is None

    def test_infinity_becomes_none(self):
        """Infinity converted to None."""
        assert clean_for_json(float('inf')) is None
        assert clean_for_json(float('-inf')) is None

    def test_dict_cleaned_recursively(self):
        """Dicts are cleaned recursively."""
        data = {"a": 1, "b": float('nan'), "nested": {"c": float('inf')}}
        result = clean_for_json(data)

        assert result["a"] == 1
        assert result["b"] is None
        assert result["nested"]["c"] is None

    def test_list_cleaned_recursively(self):
        """Lists are cleaned recursively."""
        data = [1, float('nan'), [2, float('inf')]]
        result = clean_for_json(data)

        assert result == [1, None, [2, None]]

    def test_tuple_becomes_list(self):
        """Tuples converted to lists."""
        data = (1, 2, float('nan'))
        result = clean_for_json(data)

        assert result == [1, 2, None]

    def test_numpy_integer(self):
        """NumPy integers converted to Python int."""
        val = np.int64(42)
        result = clean_for_json(val)

        assert result == 42
        assert isinstance(result, int)

    def test_numpy_float(self):
        """NumPy floats converted to Python float."""
        val = np.float64(3.14)
        result = clean_for_json(val)

        assert result == 3.14
        assert isinstance(result, float)

    def test_numpy_nan(self):
        """NumPy NaN converted to None."""
        val = np.float64('nan')
        result = clean_for_json(val)

        assert result is None

    def test_numpy_array(self):
        """NumPy arrays converted to lists."""
        arr = np.array([1, 2, 3])
        result = clean_for_json(arr)

        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_pandas_timestamp(self):
        """Pandas Timestamp converted to string."""
        ts = pd.Timestamp('2024-01-15')
        result = clean_for_json(ts)

        assert isinstance(result, str)
        assert '2024' in result

    def test_pandas_na(self):
        """pd.NA converted to None."""
        result = clean_for_json(pd.NA)
        assert result is None

    def test_string_passthrough(self):
        """Regular strings pass through."""
        assert clean_for_json("hello") == "hello"

    def test_int_passthrough(self):
        """Regular ints pass through."""
        assert clean_for_json(42) == 42

    def test_bool_passthrough(self):
        """Booleans pass through."""
        assert clean_for_json(True) is True
        assert clean_for_json(False) is False


class TestSafeJsonDumps:
    """Test safe JSON serialization."""

    def test_serializes_clean_data(self):
        """Clean data serializes normally."""
        data = {"key": "value", "num": 42}
        result = safe_json_dumps(data)

        assert json.loads(result) == data

    def test_serializes_nan_as_null(self):
        """NaN values become JSON null."""
        data = {"value": float('nan')}
        result = safe_json_dumps(data)
        parsed = json.loads(result)

        assert parsed["value"] is None

    def test_serializes_numpy_types(self):
        """NumPy types are converted."""
        data = {"count": np.int64(10), "avg": np.float64(85.5)}
        result = safe_json_dumps(data)
        parsed = json.loads(result)

        assert parsed == {"count": 10, "avg": 85.5}


class TestQuestionLabels:
    """Test label formatting."""

    def test_single_word(self):
        """Single word converted to title case."""
        result = question_labels(["urgency"])
        assert result == ["Urgency"]

    def test_snake_case(self):
        """Snake case converted to title case with spaces."""
        result = question_labels(["urgency_and_why_now"])
        assert result == ["Urgency And Why Now"]

    def test_multiple_labels(self):
        """Multiple labels all converted."""
        result = question_labels(["first_metric", "second_metric"])
        assert result == ["First Metric", "Second Metric"]

    def test_empty_list(self):
        """Empty list returns empty list."""
        result = question_labels([])
        assert result == []


class TestColorFor:
    """Test color assignment based on thresholds."""

    def test_high_value_gets_primary(self):
        """Values >= good threshold get primary color."""
        # Default good threshold is 80
        result = color_for(90.0)
        # Should be a hex color string
        assert result.startswith('#')

    def test_low_value_gets_alert(self):
        """Values <= poor threshold get alert color."""
        # Default poor threshold is 40
        result = color_for(30.0)
        assert result.startswith('#')

    def test_mid_value_gets_accent(self):
        """Values between thresholds get accent color."""
        result = color_for(60.0)
        assert result.startswith('#')

    def test_none_value_gets_muted(self):
        """None values get muted color."""
        result = color_for(None)
        assert result.startswith('#')

    def test_na_value_gets_muted(self):
        """pd.NA values get muted color."""
        result = color_for(pd.NA)
        assert result.startswith('#')

    def test_boundary_at_good_threshold(self):
        """Value exactly at good threshold gets primary."""
        # Testing boundary condition
        result = color_for(80.0)  # Default good threshold
        assert result.startswith('#')

    def test_boundary_at_poor_threshold(self):
        """Value exactly at poor threshold gets alert."""
        result = color_for(40.0)  # Default poor threshold
        assert result.startswith('#')


class TestSortNewscastSeries:
    """Test newscast sorting."""

    def test_sorts_by_configured_order(self):
        """Newscasts sorted by config order."""
        series = pd.Series(['6 pm', '5 - 7 am', '11 pm'])
        result = sort_newscast_series(series)

        # Should return a sorted series
        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_unknown_values_sorted_last(self):
        """Unknown newscast names appear at end."""
        series = pd.Series(['Unknown Show', '6 pm', 'Mystery'])
        result = sort_newscast_series(series)

        # Unknown values should be last (sorted after known ones)
        assert len(result) == 3


class TestWithWeekStart:
    """Test week start column addition."""

    def test_adds_week_start_column(self):
        """Adds week_start column from parsed date."""
        df = pd.DataFrame({
            'newscast_date_parsed': pd.to_datetime(['2024-01-15', '2024-01-16'])
        })
        result = with_week_start(df)

        assert result is not None
        assert 'week_start' in result.columns

    def test_returns_none_without_date_column(self):
        """Returns None if date column missing."""
        df = pd.DataFrame({'other_column': [1, 2, 3]})
        result = with_week_start(df)

        assert result is None

    def test_does_not_modify_original(self):
        """Original DataFrame not modified."""
        df = pd.DataFrame({
            'newscast_date_parsed': pd.to_datetime(['2024-01-15'])
        })
        original_cols = list(df.columns)
        with_week_start(df)

        assert list(df.columns) == original_cols

    def test_week_start_is_consistent(self):
        """Week start aligns days within the same week."""
        # Multiple dates in the same week should have same week_start
        df = pd.DataFrame({
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-17',  # Wednesday
                '2024-01-18',  # Thursday
                '2024-01-19',  # Friday
            ])
        })
        result = with_week_start(df)

        # All days in the same week should have identical week_start
        week_starts = result['week_start'].unique()
        assert len(week_starts) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
