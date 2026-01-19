"""
Tests for datetime_utils module.

Comprehensive tests covering:
- Date parsing with various inputs
- Timezone handling
- Date range calculations
- Boundary conditions (DST, leap years, year boundaries)
- Filtering logic (inclusive end dates)
"""

import pandas as pd
import pytest
from datetime import datetime, date
from docs.lib.datetime_utils import (
    parse_date_safe,
    parse_date_column,
    get_date_range,
    filter_by_date_range,
    to_date_string,
    calculate_day_offset,
    resample_to_weekly
)


class TestParseDateSafe:
    """Test the parse_date_safe function with various inputs."""

    def test_valid_iso_string(self):
        """Should parse ISO date string."""
        result = parse_date_safe("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_valid_datetime_object(self):
        """Should accept datetime objects."""
        dt = datetime(2024, 1, 15, 12, 30)
        result = parse_date_safe(dt)
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        # Implementation preserves time component for datetime objects
        # (Time stripping happens in parse_date_column for DataFrame operations)

    def test_valid_date_object(self):
        """Should accept date objects."""
        d = date(2024, 1, 15)
        result = parse_date_safe(d)
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_none_input(self):
        """Should return None for None input."""
        result = parse_date_safe(None)
        assert result is None

    def test_invalid_string(self):
        """Should return None for invalid strings."""
        result = parse_date_safe("not-a-date")
        assert result is None

    def test_year_too_old(self):
        """Should reject dates before 2020."""
        result = parse_date_safe("2019-12-31")
        assert result is None

    def test_year_too_new(self):
        """Should reject dates after 2030."""
        result = parse_date_safe("2031-01-01")
        assert result is None

    def test_year_boundary_valid(self):
        """Should accept dates at year boundaries."""
        result_2020 = parse_date_safe("2020-01-01")
        assert result_2020 is not None
        assert result_2020.year == 2020

        result_2030 = parse_date_safe("2030-12-31")
        assert result_2030 is not None
        assert result_2030.year == 2030

    def test_leap_year(self):
        """Should handle leap year dates correctly."""
        result = parse_date_safe("2024-02-29")
        assert result is not None
        assert result.month == 2
        assert result.day == 29

    def test_timezone_aware_timestamp(self):
        """Should strip timezone information."""
        ts = pd.Timestamp("2024-01-15", tz="America/New_York")
        result = parse_date_safe(ts)
        assert result is not None
        assert result.tz is None  # Timezone should be stripped


class TestParseDateColumn:
    """Test parsing date columns with fallback logic."""

    def test_basic_parsing(self):
        """Should parse a series of dates."""
        series = pd.Series(["2024-01-01", "2024-01-15", "2024-02-01"])
        result = parse_date_column(series)

        assert len(result) == 3
        assert result.iloc[0].year == 2024
        assert result.iloc[1].day == 15
        assert result.iloc[2].month == 2

    def test_fallback_for_missing_dates(self):
        """Should use fallback series for missing dates."""
        primary = pd.Series([None, "2024-01-15", None])
        fallback = pd.Series(["2024-01-10 14:30", "2024-01-16", "2024-01-20 09:00"])

        result = parse_date_column(primary, fallback_series=fallback)

        # First and third should come from fallback (date part only)
        assert result.iloc[0].year == 2024
        assert result.iloc[0].day == 10
        assert result.iloc[0].hour == 0  # Time stripped

        # Second should be from primary
        assert result.iloc[1].day == 15

        # Third from fallback
        assert result.iloc[2].day == 20

    def test_invalid_dates_become_nat(self):
        """Should convert invalid dates to NaT."""
        series = pd.Series(["2024-01-01", "invalid", "2019-01-01"])  # Second is invalid, third is too old
        result = parse_date_column(series)

        assert pd.notna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])  # Too old

    def test_fallback_validates_year_range(self):
        """Fallback dates should also respect year range."""
        primary = pd.Series([None, None])
        fallback = pd.Series(["2019-01-01", "2031-01-01"])  # Both outside valid range

        result = parse_date_column(primary, fallback_series=fallback)

        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])


class TestGetDateRange:
    """Test get_date_range function."""

    def test_basic_range(self):
        """Should return min and max dates."""
        dates = pd.Series([
            pd.Timestamp("2024-01-15"),
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-30")
        ])

        min_date, max_date = get_date_range(dates)

        assert min_date.day == 1
        assert max_date.day == 30

    def test_empty_series(self):
        """Should return (None, None) for empty series."""
        dates = pd.Series([], dtype='datetime64[ns]')
        min_date, max_date = get_date_range(dates)

        assert min_date is None
        assert max_date is None

    def test_all_nat(self):
        """Should return (None, None) if all dates are NaT."""
        dates = pd.Series([pd.NaT, pd.NaT, pd.NaT])
        min_date, max_date = get_date_range(dates)

        assert min_date is None
        assert max_date is None

    def test_single_date(self):
        """Should handle series with one date."""
        dates = pd.Series([pd.Timestamp("2024-01-15")])
        min_date, max_date = get_date_range(dates)

        assert min_date == max_date
        assert min_date.day == 15


class TestFilterByDateRange:
    """Test filtering DataFrame by date range."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with dates."""
        return pd.DataFrame({
            'date': pd.to_datetime([
                "2024-01-10",
                "2024-01-15",
                "2024-01-20",
                "2024-01-25",
                "2024-01-30"
            ]),
            'value': [1, 2, 3, 4, 5]
        })

    def test_filter_start_date(self, sample_df):
        """Should filter dates >= start date."""
        result = filter_by_date_range(sample_df, 'date', start_date="2024-01-20")

        assert len(result) == 3  # 20, 25, 30
        assert result['value'].tolist() == [3, 4, 5]

    def test_filter_end_date_inclusive(self, sample_df):
        """Should filter dates <= end date (INCLUSIVE)."""
        result = filter_by_date_range(sample_df, 'date', end_date="2024-01-20")

        # Should include Jan 20 (entire day)
        assert len(result) == 3  # 10, 15, 20
        assert result['value'].tolist() == [1, 2, 3]

    def test_filter_both_dates(self, sample_df):
        """Should filter date range [start, end] inclusive."""
        result = filter_by_date_range(
            sample_df,
            'date',
            start_date="2024-01-15",
            end_date="2024-01-25"
        )

        # Should include both 15 and 25
        assert len(result) == 3  # 15, 20, 25
        assert result['value'].tolist() == [2, 3, 4]

    def test_single_day_range(self, sample_df):
        """Should handle single-day range (start == end)."""
        result = filter_by_date_range(
            sample_df,
            'date',
            start_date="2024-01-15",
            end_date="2024-01-15"
        )

        # Should include Jan 15 only
        assert len(result) == 1
        assert result['value'].iloc[0] == 2

    def test_no_filters(self, sample_df):
        """Should return all data if no filters."""
        result = filter_by_date_range(sample_df, 'date')

        assert len(result) == len(sample_df)

    def test_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=['date', 'value'])
        result = filter_by_date_range(df, 'date', start_date="2024-01-01")

        assert len(result) == 0

    def test_missing_date_column(self, sample_df):
        """Should return original df if column missing."""
        result = filter_by_date_range(sample_df, 'nonexistent_column')

        assert len(result) == len(sample_df)


class TestToDateString:
    """Test to_date_string function."""

    def test_timestamp_to_string(self):
        """Should convert Timestamp to ISO string."""
        ts = pd.Timestamp("2024-01-15")
        result = to_date_string(ts)

        assert result == "2024-01-15"

    def test_datetime_to_string(self):
        """Should convert datetime to ISO string."""
        dt = datetime(2024, 1, 15, 12, 30)
        result = to_date_string(dt)

        assert result == "2024-01-15"

    def test_date_to_string(self):
        """Should convert date to ISO string."""
        d = date(2024, 1, 15)
        result = to_date_string(d)

        assert result == "2024-01-15"

    def test_none_returns_none(self):
        """Should return None for None input."""
        result = to_date_string(None)

        assert result is None


class TestCalculateDayOffset:
    """Test calculate_day_offset for slider day-index calculations."""

    def test_basic_offset(self):
        """Should calculate correct day offset."""
        offset = calculate_day_offset("2024-01-05", "2024-01-01")

        assert offset == 4  # 5 days after Jan 1

    def test_zero_offset(self):
        """Should return 0 for same date."""
        offset = calculate_day_offset("2024-01-15", "2024-01-15")

        assert offset == 0

    def test_negative_offset(self):
        """Should handle target before reference."""
        offset = calculate_day_offset("2024-01-01", "2024-01-05")

        assert offset == -4

    def test_month_boundary(self):
        """Should calculate across month boundary."""
        offset = calculate_day_offset("2024-02-03", "2024-01-28")

        # Jan 28 → Jan 31 (3 days) + Feb 1-3 (3 days) = 6 days
        assert offset == 6

    def test_leap_year_february(self):
        """Should handle leap year correctly."""
        offset = calculate_day_offset("2024-03-01", "2024-02-28")

        # 2024 is leap year, so Feb has 29 days
        # Feb 28 → Feb 29 (1 day) + Mar 1 (1 day) = 2 days
        assert offset == 2

    def test_year_boundary(self):
        """Should calculate across year boundary."""
        offset = calculate_day_offset("2024-01-05", "2023-12-30")

        # Dec 30 → Jan 5 is 6 days (Dec 31, Jan 1, 2, 3, 4, 5)
        assert offset == 6

    def test_invalid_dates_return_none(self):
        """Should return None for invalid dates."""
        offset = calculate_day_offset("invalid", "2024-01-01")

        assert offset is None


class TestResampleToWeekly:
    """Test weekly resampling functionality."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with daily data."""
        dates = pd.date_range("2024-01-01", "2024-01-31", freq='D')
        return pd.DataFrame({
            'date': dates,
            'metric1': range(1, 32),  # 1 to 31
            'metric2': range(31, 0, -1)  # 31 to 1
        })

    def test_weekly_mean_resampling(self, sample_df):
        """Should resample to weekly averages."""
        result = resample_to_weekly(
            sample_df,
            'date',
            ['metric1', 'metric2'],
            aggregation='mean'
        )

        # January 2024 has ~4.5 weeks
        assert len(result) >= 4
        assert 'metric1' in result.columns
        assert 'metric2' in result.columns

    def test_weekly_sum_resampling(self, sample_df):
        """Should support sum aggregation."""
        result = resample_to_weekly(
            sample_df,
            'date',
            ['metric1'],
            aggregation='sum'
        )

        assert len(result) >= 4

    def test_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame(columns=['date', 'value'])
        result = resample_to_weekly(df, 'date', ['value'])

        assert len(result) == 0

    def test_missing_column(self):
        """Should handle missing date column."""
        df = pd.DataFrame({'value': [1, 2, 3]})
        result = resample_to_weekly(df, 'nonexistent', ['value'])

        assert len(result) == 0
