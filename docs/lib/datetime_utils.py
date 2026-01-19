"""
Shared datetime utilities for consistent date handling across the pipeline.

This module provides a centralized approach to date parsing, timezone handling,
and date range operations. It eliminates the scattered datetime logic that was
causing bugs in the date slider and filtering.

Key principles:
1. All dates are stored as timezone-naive datetime objects (consistent with Excel)
2. Timezone awareness is applied at the configuration level, not per-operation
3. Date ranges use day-level granularity (no time components)
4. DST transitions are handled transparently
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Union
from zoneinfo import ZoneInfo


# Constants
MIN_VALID_YEAR = 2020  # Filter out dates before 2020 as implausible
MAX_VALID_YEAR = 2030  # Filter out dates far in the future


def parse_date_safe(
    date_input: Union[str, datetime, date, pd.Timestamp, None],
    timezone: Optional[str] = None
) -> Optional[pd.Timestamp]:
    """
    Parse a date input into a timezone-naive pandas Timestamp.

    This is the primary date parsing function. It handles various input types
    and ensures the output is always timezone-naive (as expected by the rest
    of the pipeline).

    Args:
        date_input: Date as string, datetime, or pandas Timestamp
        timezone: Optional timezone string (e.g., "America/New_York") - currently
                 kept for future use but dates are returned naive

    Returns:
        Timezone-naive pandas Timestamp, or None if parsing fails

    Examples:
        >>> parse_date_safe("2024-01-15")
        Timestamp('2024-01-15 00:00:00')

        >>> parse_date_safe("invalid")
        None
    """
    if date_input is None:
        return None

    try:
        # Check for NaN floats (mypy false positive - this IS reachable at runtime)
        if isinstance(date_input, float) and pd.isna(date_input):  # type: ignore[unreachable]
            return None  # type: ignore[unreachable]
        # Convert to pandas Timestamp
        ts = pd.to_datetime(date_input, errors='coerce')

        if pd.isna(ts):
            return None

        # Ensure naive (strip timezone if present from Excel parsing)
        if ts.tz is not None:
            ts = ts.tz_localize(None)

        # Validate year range (sanity check for data quality)
        if ts.year < MIN_VALID_YEAR or ts.year > MAX_VALID_YEAR:
            return None

        return ts

    except (ValueError, TypeError, AttributeError):
        return None


def parse_date_column(
    series: pd.Series,
    fallback_series: Optional[pd.Series] = None,
    timezone: Optional[str] = None
) -> pd.Series:
    """
    Parse a series of dates with optional fallback for missing values.

    This function is designed for DataFrame columns where some dates might be
    missing but can be inferred from another column (e.g., start_time).

    Args:
        series: Primary date column to parse
        fallback_series: Optional fallback column (e.g., start_time timestamps)
        timezone: Optional timezone for future timezone-aware operations

    Returns:
        Series of timezone-naive pandas Timestamps (with NaT for invalid dates)
    """
    # Parse primary series
    parsed = pd.to_datetime(series, errors='coerce')

    # Ensure naive
    if parsed.dt.tz is not None:
        parsed = parsed.dt.tz_localize(None)

    # Filter out implausible dates
    mask_invalid = (parsed.dt.year < MIN_VALID_YEAR) | (parsed.dt.year > MAX_VALID_YEAR)
    parsed.loc[mask_invalid] = pd.NaT  # type: ignore[call-overload]

    # Apply fallback if provided
    if fallback_series is not None and not fallback_series.empty:
        fallback_parsed = pd.to_datetime(fallback_series, errors='coerce')

        # Ensure naive fallback
        if fallback_parsed.dt.tz is not None:
            fallback_parsed = fallback_parsed.dt.tz_localize(None)

        # Find rows needing fallback: no valid primary date BUT valid fallback
        mask_fill = (
            parsed.isna() &
            fallback_parsed.notna() &
            (fallback_parsed.dt.year >= MIN_VALID_YEAR) &
            (fallback_parsed.dt.year <= MAX_VALID_YEAR)
        )

        if mask_fill.any():
            # Use the date component only (strip time)
            parsed[mask_fill] = fallback_parsed[mask_fill].dt.floor('D')

    return parsed


def get_date_range(
    dates: pd.Series
) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """
    Get the minimum and maximum dates from a series.

    Args:
        dates: Series of datetime values

    Returns:
        Tuple of (min_date, max_date) or (None, None) if series is empty
    """
    if dates.empty or dates.isna().all():
        return None, None

    valid_dates = dates.dropna()
    if valid_dates.empty:
        return None, None

    return valid_dates.min(), valid_dates.max()


def filter_by_date_range(
    df: pd.DataFrame,
    date_column: str,
    start_date: Optional[Union[str, datetime, pd.Timestamp]] = None,
    end_date: Optional[Union[str, datetime, pd.Timestamp]] = None
) -> pd.DataFrame:
    """
    Filter a DataFrame by date range (inclusive of both start and end dates).

    This function handles the common pattern of filtering data by a date range
    and ensures that the end date is inclusive (a common source of off-by-one bugs).

    Args:
        df: DataFrame to filter
        date_column: Name of the date column
        start_date: Optional start date (inclusive)
        end_date: Optional end date (inclusive - includes entire day)

    Returns:
        Filtered DataFrame

    Examples:
        >>> df = pd.DataFrame({'date': pd.date_range('2024-01-01', '2024-01-10')})
        >>> filtered = filter_by_date_range(df, 'date', '2024-01-05', '2024-01-07')
        >>> len(filtered)  # Should be 3 days: 5th, 6th, 7th
        3
    """
    if df.empty or date_column not in df.columns:
        return df

    result = df.copy()

    # Apply start date filter
    if start_date is not None:
        ts_start = parse_date_safe(start_date)
        if ts_start is not None:
            result = result[result[date_column] >= ts_start]

    # Apply end date filter (inclusive - include entire end day)
    if end_date is not None:
        ts_end = parse_date_safe(end_date)
        if ts_end is not None:
            # Add 1 day and use < to make it inclusive
            result = result[result[date_column] < (ts_end + pd.Timedelta(days=1))]

    return result


def resample_to_weekly(
    df: pd.DataFrame,
    date_column: str,
    value_columns: list[str],
    aggregation: str = 'mean',
    week_start: str = 'MON'
) -> pd.DataFrame:
    """
    Resample data to weekly intervals with specified aggregation.

    Args:
        df: DataFrame with datetime index or column
        date_column: Name of the date column to resample on
        value_columns: List of columns to aggregate
        aggregation: Aggregation method ('mean', 'sum', 'count', etc.)
        week_start: Day to start the week ('MON', 'SUN', etc.)

    Returns:
        DataFrame with weekly data and DatetimeIndex
    """
    if df.empty or date_column not in df.columns:
        return pd.DataFrame()

    # Set date column as index for resampling
    df_indexed = df.set_index(date_column)

    # Resample to weekly frequency
    resampling_freq = f'W-{week_start}'

    if aggregation == 'mean':
        weekly = df_indexed[value_columns].resample(resampling_freq).mean()
    elif aggregation == 'sum':
        weekly = df_indexed[value_columns].resample(resampling_freq).sum()
    elif aggregation == 'count':
        weekly = df_indexed[value_columns].resample(resampling_freq).count()
    else:
        raise ValueError(f"Unsupported aggregation: {aggregation}")

    return weekly


def to_date_string(dt: Union[datetime, pd.Timestamp, date, None]) -> Optional[str]:
    """
    Convert a datetime to ISO date string (YYYY-MM-DD).

    Args:
        dt: Datetime object or None

    Returns:
        ISO formatted date string or None
    """
    if dt is None:
        return None

    try:
        if isinstance(dt, pd.Timestamp):
            return dt.strftime('%Y-%m-%d')
        elif isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d')
        elif isinstance(dt, date):
            return dt.isoformat()
        else:
            # Try to parse first
            parsed = parse_date_safe(dt)  # type: ignore
            return parsed.strftime('%Y-%m-%d') if parsed else None
    except (ValueError, AttributeError):
        return None


def calculate_day_offset(
    target_date: Union[str, datetime, pd.Timestamp],
    reference_date: Union[str, datetime, pd.Timestamp]
) -> Optional[int]:
    """
    Calculate the number of days between two dates.

    This is used by the frontend date slider to convert dates to day indices.

    Args:
        target_date: The date to calculate offset for
        reference_date: The reference date (usually min date)

    Returns:
        Number of days (can be negative if target is before reference)

    Examples:
        >>> calculate_day_offset('2024-01-05', '2024-01-01')
        4
    """
    target = parse_date_safe(target_date)
    reference = parse_date_safe(reference_date)

    if target is None or reference is None:
        return None

    delta = (target - reference).days
    return delta
