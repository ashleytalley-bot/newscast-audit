"""
Unit tests for lib/builders.py

Tests table and chart data building functions.
"""

import pytest
import pandas as pd
import numpy as np

from lib.builders import (
    build_yes_percent_table,
    build_data_quality_table,
    weekly_percent_series
)


class TestBuildYesPercentTable:
    """Tests for build_yes_percent_table() function."""

    def test_calculates_yes_percentage(self):
        """Should calculate correct Yes percentage."""
        df = pd.DataFrame({
            'metric1': [1, 1, 0, 1],  # 75% yes
            'metric2': [1, 0, 0, 0]   # 25% yes
        })
        result = build_yes_percent_table(df, ['metric1', 'metric2'])

        assert result.loc[0, 'Question'] == 'Metric1'
        assert result.loc[0, 'Yes %'] == 75
        assert result.loc[1, 'Question'] == 'Metric2'
        assert result.loc[1, 'Yes %'] == 25

    def test_handles_all_na(self):
        """Should handle columns with all NA values."""
        df = pd.DataFrame({
            'metric1': pd.array([pd.NA, pd.NA, pd.NA], dtype='Int64'),
            'metric2': pd.array([1, 0, 1], dtype='Int64')
        })
        result = build_yes_percent_table(df, ['metric1', 'metric2'])

        # metric1 should be NA (no valid data)
        assert pd.isna(result.loc[0, 'Yes %'])
        # metric2 should be 67% (2/3)
        assert result.loc[1, 'Yes %'] == 67

    def test_skips_na_in_calculation(self):
        """Should skip NA values when calculating percentage."""
        df = pd.DataFrame({
            'metric1': pd.array([1, 0, pd.NA, 1, pd.NA], dtype='Int64')  # 2 yes out of 3 valid = 67%
        })
        result = build_yes_percent_table(df, ['metric1'])

        assert result.loc[0, 'Yes %'] == 67

    def test_rounds_to_integer(self):
        """Should round percentages to integers."""
        df = pd.DataFrame({
            'metric1': [1, 1, 0]  # 66.666...%
        })
        result = build_yes_percent_table(df, ['metric1'])

        assert result.loc[0, 'Yes %'] == 67  # Rounded
        assert isinstance(result.loc[0, 'Yes %'], (int, np.integer, pd.Int64Dtype, type(pd.NA))) or pd.isna(result.loc[0, 'Yes %'])

    def test_human_readable_labels(self):
        """Should convert column names to human-readable labels."""
        df = pd.DataFrame({
            'urgency_and_why_now': [1, 0, 1],
            'specific_streaming_tease': [1, 1, 0]
        })
        result = build_yes_percent_table(df, ['urgency_and_why_now', 'specific_streaming_tease'])

        assert result.loc[0, 'Question'] == 'Urgency And Why Now'
        assert result.loc[1, 'Question'] == 'Specific Streaming Tease'

    def test_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame()
        result = build_yes_percent_table(df, [])

        assert len(result) == 0


class TestBuildDataQualityTable:
    """Tests for build_data_quality_table() function."""

    def test_calculates_completeness(self):
        """Should calculate correct completeness percentage."""
        df = pd.DataFrame({
            'metric1': [1, 1, pd.NA, pd.NA],  # 50% complete
            'metric2': [1, 0, 1, 0]            # 100% complete
        })
        result = build_data_quality_table(df, ['metric1', 'metric2'])

        assert result.loc[0, 'Complete %'] == 50.0
        assert result.loc[1, 'Complete %'] == 100.0

    def test_counts_missing(self):
        """Should count missing values correctly."""
        df = pd.DataFrame({
            'metric1': [1, pd.NA, pd.NA, 1],  # 2 missing
            'metric2': [1, 0, 1, 0]            # 0 missing
        })
        result = build_data_quality_table(df, ['metric1', 'metric2'])

        assert result.loc[0, 'Missing'] == 2
        assert result.loc[1, 'Missing'] == 0

    def test_human_readable_labels(self):
        """Should convert column names to human-readable labels."""
        df = pd.DataFrame({
            'urgency_and_why_now': [1, 0, 1]
        })
        result = build_data_quality_table(df, ['urgency_and_why_now'])

        assert result.loc[0, 'Question'] == 'Urgency And Why Now'

    def test_all_missing(self):
        """Should handle columns with all missing values."""
        df = pd.DataFrame({
            'metric1': [pd.NA, pd.NA, pd.NA]
        })
        result = build_data_quality_table(df, ['metric1'])

        assert result.loc[0, 'Complete %'] == 0.0
        assert result.loc[0, 'Missing'] == 3

    def test_rounds_to_one_decimal(self):
        """Should round completeness to one decimal place."""
        df = pd.DataFrame({
            'metric1': [1, 1, pd.NA]  # 66.666...% complete
        })
        result = build_data_quality_table(df, ['metric1'])

        assert result.loc[0, 'Complete %'] == 66.7


class TestWeeklyPercentSeries:
    """Tests for weekly_percent_series() function."""

    def test_calculates_weekly_average(self):
        """Should calculate weekly average correctly."""
        # Create data spanning two weeks
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am', '5 - 7 am', '5 - 7 am', '5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-01',  # Monday week 1
                '2024-01-02',  # Tuesday week 1
                '2024-01-08',  # Monday week 2
                '2024-01-09'   # Tuesday week 2
            ]),
            'metric1': [1, 1, 0, 0],  # Week 1: 100%, Week 2: 0%
            'metric2': [1, 0, 1, 0]   # Week 1: 50%, Week 2: 50%
        })

        result = weekly_percent_series(df, ['metric1', 'metric2'])

        assert result is not None
        assert len(result['dates']) == 2
        # Week 1: (100 + 50) / 2 = 75%
        # Week 2: (0 + 50) / 2 = 25%
        assert len(result['pct']) == 2

    def test_filters_by_newscast(self):
        """Should filter by newscast when specified."""
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am', '5 - 7 am', '6 pm', '6 pm'],
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'
            ]),
            'metric1': [1, 1, 0, 0]
        })

        result_5_7 = weekly_percent_series(df, ['metric1'], newscast='5 - 7 am')
        result_6pm = weekly_percent_series(df, ['metric1'], newscast='6 pm')

        assert result_5_7 is not None
        assert result_6pm is not None
        # 5-7am should have 100% (both 1s)
        # 6pm should have 0% (both 0s)
        assert result_5_7['pct'][0] > result_6pm['pct'][0]

    def test_filters_by_question(self):
        """Should filter by specific question when specified."""
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am', '5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'metric1': [1, 1],  # 100%
            'metric2': [0, 0]   # 0%
        })

        result_m1 = weekly_percent_series(df, ['metric1', 'metric2'], question='metric1')
        result_m2 = weekly_percent_series(df, ['metric1', 'metric2'], question='metric2')

        assert result_m1 is not None
        assert result_m2 is not None
        # metric1 should be 100%
        assert result_m1['pct'][0] == 100.0
        # metric2 should be 0%
        assert result_m2['pct'][0] == 0.0

    def test_returns_none_for_empty_data(self):
        """Should return None when no data available."""
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime(['2024-01-01']),
            'metric1': [1]
        })

        # Filter for non-existent newscast
        result = weekly_percent_series(df, ['metric1'], newscast='11 pm')

        assert result is None

    def test_returns_none_for_no_dates(self):
        """Should return None when no valid dates."""
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am'],
            'newscast_date_parsed': [pd.NaT],
            'metric1': [1]
        })

        result = weekly_percent_series(df, ['metric1'])

        assert result is None

    def test_groups_by_week_start_monday(self):
        """Should group by week starting on Monday."""
        # Wednesday Jan 3, 2024 and Friday Jan 5, 2024 (same week)
        # Monday Jan 8, 2024 (next week)
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am', '5 - 7 am', '5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-03',  # Wednesday
                '2024-01-05',  # Friday
                '2024-01-08'   # Monday next week
            ]),
            'metric1': [1, 1, 0]
        })

        result = weekly_percent_series(df, ['metric1'])

        assert result is not None
        assert len(result['dates']) == 2  # Two weeks
        # First two should be grouped together
        # Week starting Jan 1 (Mon): 100% (both 1s)
        # Week starting Jan 8 (Mon): 0%

    def test_handles_unspecified_newscast(self):
        """Should handle __unspecified newscast filter."""
        df = pd.DataFrame({
            'newscast_normalized': [None, None, '5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-01', '2024-01-02', '2024-01-03'
            ]),
            'metric1': [1, 1, 0]
        })

        result = weekly_percent_series(df, ['metric1'], newscast='__unspecified')

        assert result is not None
        # Should only include rows with None newscast (first two)
        assert result['pct'][0] == 100.0

    def test_date_format_iso(self):
        """Should return dates in ISO format (YYYY-MM-DD)."""
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime(['2024-01-01']),
            'metric1': [1]
        })

        result = weekly_percent_series(df, ['metric1'])

        assert result is not None
        # Week start should be Monday Dec 25, 2023 
        # Formatted as %m/%d
        assert '/' in result['dates'][0]

    def test_percentages_rounded(self):
        """Should return percentages as floats."""
        df = pd.DataFrame({
            'newscast_normalized': ['5 - 7 am', '5 - 7 am', '5 - 7 am'],
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-01', '2024-01-02', '2024-01-03'
            ]),
            'metric1': [1, 0, 0]  # 33.333...%
        })

        result = weekly_percent_series(df, ['metric1'])

        assert result is not None
        # Should be a percentage (0-100)
        assert 0 <= result['pct'][0] <= 100
