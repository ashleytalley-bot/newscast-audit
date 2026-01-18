"""
Data cleaning and validation functions.

This module handles:
- Input validation
- Newscast name normalization
- Response conversion (Yes/No → 1/0/NA)
- Column standardization
- Complete data cleaning pipeline
"""

import pandas as pd
import re
import warnings
from typing import Optional, List, Tuple, Dict

from .config import COLUMN_MAPPING, METRIC_COLUMNS
from .exceptions import (
    DataValidationError,
    DataQualityWarning,
    EmptyDataError,
    InsufficientDataError
)


def validate_input_data(df: pd.DataFrame) -> None:
    """
    Validate that the Excel file has expected columns and data.

    Args:
        df: Raw DataFrame from Excel file

    Raises:
        EmptyDataError: If DataFrame is empty
        DataValidationError: If required columns are missing
    """
    # Check for empty file
    if df.empty or len(df) == 0:
        raise EmptyDataError(row_count=0)

    # Check for required columns
    critical_columns = ['Which newscast are you auditing?', 'Date of newscast:']
    missing = [col for col in critical_columns if col not in df.columns]

    if missing:
        raise DataValidationError(
            message="Excel file is missing required columns.",
            missing_columns=missing,
            found_columns=list(df.columns)
        )


# Newscast normalization patterns (order matters - most specific first)
_NEWSCAST_PATTERNS = [
    # Pattern format: (regex_pattern, output_name, description)

    # Evening Plus (various formats)
    (r'evening\s*\+|e\s*\+|evening\s+plus', 'E +', 'Evening Plus show'),

    # Abbreviated formats (5a-7a, 7a-9a, etc.) - MUST come before general AM patterns
    (r'\b5\s*a\s*[-–]\s*7\s*a\b', '5 - 7 am', '5a-7a abbreviated'),
    (r'\b7\s*a\s*[-–]\s*9\s*a\b', '7 - 9 am', '7a-9a abbreviated'),

    # "To" ranges (5 to 7am, 7 to 9am, 7 to 8am)
    (r'5\s+to\s+7\s*(?:am|a\.m\.?)?', '5 - 7 am', '5 to 7 range'),
    (r'7\s+to\s+[89]\s*(?:am|a\.m\.?)?', '7 - 9 am', '7 to 8/9 range'),

    # Time ranges with full AM notation
    (r'5\s*[-–:]\s*7\s*(?:am|a\.m\.)', '5 - 7 am', '5-7am range'),
    (r'7\s*[-–:]\s*9\s*(?:am|a\.m\.)', '7 - 9 am', '7-9am range'),

    # PM shows (specific times, avoiding ranges)
    (r'\b11\s*(?:pm?|p\.m\.?)\b', '11 pm', '11 PM newscast'),
    (r'\b11\b(?!\s*[-–:])', '11 pm', '11 (assume PM)'),
    (r'\b6\s*(?:pm?|p\.m\.?)\b(?!\s*[-–:])', '6 pm', '6 PM newscast'),
    (r'\b5\s*(?:pm?|p\.m\.?)\b(?!\s*[-–:])', '5 pm', '5 PM newscast'),
    
    # Half-hour variations (customer request: 5:30 -> 5pm)
    (r'\b5:30\s*(?:pm?|p\.m\.?)?', '5 pm', '5:30 PM -> 5 PM'),
    (r'\b6:30\s*(?:pm?|p\.m\.?)?', '6 pm', '6:30 PM -> 6 PM'),
    (r'\b11:30\s*(?:pm?|p\.m\.?)?', '11 pm', '11:30 PM -> 11 PM'),

    # Noon variations
    (r'\b(?:noon|12\s*(?:pm?|p\.m\.?)|midday)\b', '12 pm', 'Noon/12pm newscast'),
    (r'\b12\b(?!\s*[-–:])', '12 pm', '12 (assume noon)'),

    # Single AM times (map to ranges)
    (r'\b5\s*(?:am|a\.m\.?)\b(?!\s*[-–:])', '5 - 7 am', '5am (assume 5-7 range)'),
    (r'\b7\s*(?:am|a\.m\.?)\b(?!\s*[-–:])', '7 - 9 am', '7am (assume 7-9 range)'),
]

# Ambiguous patterns that should be rejected
_AMBIGUOUS_PATTERNS = [
    (r'^\s*(?:am?|a\.m\.?)\s*$', 'Just "am" without time'),
    (r'^\s*(?:pm?|p\.m\.?)\s*$', 'Just "pm" without time'),
    (r'^\s*morning\s*$', 'Generic "morning"'),
    (r'^\s*evening\s*$', 'Generic "evening" (use "evening+" for Evening Plus)'),
    (r'^\s*afternoon\s*$', 'Generic "afternoon"'),
]


def normalize_newscast(value: Optional[str], warn_on_unknown: bool = False) -> Optional[str]:
    """
    Map free-text newscast names to standardized timeslots using regex patterns.

    This function handles various input formats and normalizes them to standard
    timeslot names. It uses pattern matching with priority ordering to handle
    edge cases correctly.

    Supported formats:
        - Time ranges: "5-7am", "5a-7a", "5 - 7 am", "5:7am"
        - Single times: "5am" → "5 - 7 am", "6pm" → "6 pm"
        - Noon: "noon", "12pm", "12", "midday" → "12 pm"
        - Numbers only: "11" → "11 pm", "12" → "12 pm"
        - Evening Plus: "evening+", "e+", "evening plus" → "E +"

    Ambiguous inputs (returned as None):
        - Just "am" or "pm" without a time
        - Generic words like "morning", "evening", "afternoon"

    Args:
        value: Free-text newscast name from survey response
        warn_on_unknown: If True, emit warnings for unrecognized formats

    Returns:
        Standardized newscast name, or None if invalid/ambiguous

    Examples:
        >>> normalize_newscast("5-7am")
        '5 - 7 am'
        >>> normalize_newscast("6 pm")
        '6 pm'
        >>> normalize_newscast("noon")
        '12 pm'
        >>> normalize_newscast("am")  # Ambiguous
        None
        >>> normalize_newscast("random text")  # Unknown
        'random text'
    """
    if pd.isna(value):
        return None

    # Clean and lowercase for matching
    original = str(value).strip()
    v = original.lower()

    # Remove extra whitespace
    v = re.sub(r'\s+', ' ', v)

    # Check for ambiguous patterns first
    for pattern, reason in _AMBIGUOUS_PATTERNS:
        if re.search(pattern, v, re.IGNORECASE):
            if warn_on_unknown:
                warnings.warn(
                    f"Ambiguous newscast name '{original}': {reason}. Returning None.",
                    UserWarning
                )
            return None

    # Try to match against known patterns
    for pattern, output, description in _NEWSCAST_PATTERNS:
        if re.search(pattern, v, re.IGNORECASE):
            return output

    # Unknown format - return original value with optional warning
    if warn_on_unknown:
        warnings.warn(
            f"Unknown newscast format '{original}'. Returning as-is. "
            f"This may cause sorting issues.",
            UserWarning
        )

    return original


def convert_to_numeric(v):
    """
    Convert survey responses into 1/0/NA.

    Mappings:
    - "Yes", "Y", "True", "1" → 1
    - "No", "N", "False", "0" → 0
    - "N/A", "NA", "None", "" → pd.NA

    Args:
        v: Survey response value

    Returns:
        1 for yes, 0 for no, pd.NA for missing/not applicable
    """
    if pd.isna(v):
        return pd.NA

    s = str(v).strip().lower()

    # Yes responses
    if s in ('yes', 'y', 'true', '1'):
        return 1

    # No responses
    if s in ('no', 'n', 'false', '0'):
        return 0

    # N/A or missing
    if s in ('n/a', 'na', 'none', ''):
        return pd.NA

    # Try numeric parsing
    try:
        num = float(s)
        if num == 1:
            return 1
        if num == 0:
            return 0
    except (ValueError, TypeError):
        pass

    # Unknown format - treat as N/A
    return pd.NA


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename source columns to snake_case names using COLUMN_MAPPING.

    Args:
        df: DataFrame with raw Excel column names

    Returns:
        DataFrame with standardized column names
    """
    rename_map = {
        source: target
        for source, target in COLUMN_MAPPING.items()
        if source in df.columns
    }
    return df.rename(columns=rename_map)


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], int]:
    """
    Clean and prepare survey data for analysis.

    This function performs the complete cleaning pipeline:
    1. Standardize column names
    2. Normalize newscast names
    3. Parse dates
    4. Convert yes/no responses to numeric
    5. Drop rows with no metric data

    Args:
        df: Raw DataFrame from Excel

    Returns:
        Tuple of:
        - Cleaned DataFrame
        - List of metric column names found in the data
        - Count of rows dropped due to missing all metrics
    """
    # Step 1: Rename columns
    df = standardize_columns(df)

    # Step 2: Normalize newscast names
    if 'newscast' in df.columns:
        df['newscast_normalized'] = df['newscast'].apply(normalize_newscast)
    else:
        df['newscast_normalized'] = None

    # Step 3: Parse dates
    if 'newscast_date' in df.columns:
        df['newscast_date_parsed'] = pd.to_datetime(
            df['newscast_date'],
            errors='coerce'
        )
    else:
        df['newscast_date_parsed'] = pd.NaT

    # Step 4: Convert yes/no to numeric for present metric columns
    present_metrics = [c for c in METRIC_COLUMNS if c in df.columns]
    for col in present_metrics:
        df[col] = df[col].apply(convert_to_numeric)
        df[col] = df[col].astype('Int64')

    # Step 5: Drop empty rows (all metric columns are NA)
    dropped_empty = 0
    if present_metrics:
        mask = df[present_metrics].notna().any(axis=1)
        dropped_empty = (~mask).sum()
        df = df[mask].reset_index(drop=True)

    return df, present_metrics, dropped_empty
