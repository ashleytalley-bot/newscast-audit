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
from typing import Optional, List, Tuple

from .config import COLUMN_MAPPING, METRIC_COLUMNS


def validate_input_data(df: pd.DataFrame) -> None:
    """
    Validate that the Excel file has expected columns.

    Args:
        df: Raw DataFrame from Excel file

    Raises:
        ValueError: If required columns are missing
    """
    critical_columns = ['Which newscast are you auditing?', 'Date of newscast:']
    missing = [col for col in critical_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Excel file is missing required columns: {missing}\n"
            "Ensure you're uploading a newscast audit survey export from Microsoft Forms."
        )


def normalize_newscast(value: Optional[str]) -> Optional[str]:
    """
    Map free-text newscast names to standardized timeslots.

    This function handles various formats like:
    - "5-7am", "5a-7a", "5 - 7 am" → "5 - 7 am"
    - "noon", "12", "12 pm" → "12 pm"
    - "11", "11pm", "11 p.m." → "11 pm"
    - "evening+", "e+" → "E +"

    Args:
        value: Free-text newscast name from survey

    Returns:
        Standardized newscast name, or None if invalid/ambiguous
    """
    if pd.isna(value):
        return None

    v = str(value).strip().lower()

    # Evening+
    if 'evening+' in v or v.startswith('evening') or 'e+' in v:
        return 'E +'

    # PM shows
    if '11' in v and ('pm' in v or 'p' in v):
        return '11 pm'
    if '6' in v and ('pm' in v or 'p' in v) and '5' not in v:
        return '6 pm'
    if '5' in v and ('pm' in v or 'p' in v) and '6' not in v and '7' not in v:
        return '5 pm'
    if 'noon' in v or ('12' in v and ('pm' not in v or 'noon' in v)):
        return '12 pm'

    # Morning shows - check for range patterns first
    # Match: "5-7am", "5a-7a", "5 - 7 am", "5am-7am", "5a - 7a", etc.
    if ('5' in v and '7' in v) and ('a' in v):
        return '5 - 7 am'
    if ('7' in v and '9' in v) and ('a' in v):
        return '7 - 9 am'

    # Single time mentions with am
    if '5' in v and ('am' in v or 'a.m' in v or v.endswith('a')):
        return '5 - 7 am'
    if '7' in v and ('am' in v or 'a.m' in v or v.endswith('a')):
        return '7 - 9 am'

    # Catch-all for generic "am" without specific time - skip these (ambiguous)
    if v == 'am' or v == 'a.m.' or v == 'a.m':
        return None

    # Unknown format - return original value (will sort to end)
    return str(value).strip()


def convert_to_numeric(v) -> pd.NA | int:
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
