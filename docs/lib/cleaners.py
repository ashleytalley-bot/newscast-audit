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

from .config_dynamic import get_config
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
    # We use the raw keys from the column mapping to verify presence
    config = get_config()
    required_cols = list(config.COLUMN_MAPPING.keys())
    
    # We only check for a subset of critical columns to be safe
    # (e.g. sometimes comments or extra fields might be missing)
    critical_subtext = ['Which newscast are you auditing?', 'Date of newscast:']
    
    missing = []
    for crit in critical_subtext:
        found = False
        for col in df.columns:
            if crit in str(col):
                found = True
                break
        if not found:
            missing.append(crit)

    if missing:
        raise DataValidationError(
            message="Excel file is missing required columns.",
            missing_columns=missing,
            found_columns=list(df.columns)
        )


def normalize_newscast(value: Optional[str], warn_on_unknown: bool = False) -> Optional[str]:
    """
    Map free-text newscast names to standardized timeslots using regex patterns.
    """
    if pd.isna(value):
        return None

    # Get patterns from dynamic config
    config = get_config()
    ambiguous_patterns = config.AMBIGUOUS_PATTERNS
    normalization_patterns = config.NORMALIZATION_PATTERNS
    
    # Clean and lowercase for matching
    original = str(value).strip()
    v = original.lower()

    # Remove extra whitespace
    v = re.sub(r'\s+', ' ', v)

    # Check for ambiguous patterns first
    for pattern, reason in ambiguous_patterns:
        if re.search(pattern, v, re.IGNORECASE):
            if warn_on_unknown:
                warnings.warn(
                    f"Ambiguous newscast name '{original}': {reason}. Returning None.",
                    UserWarning
                )
            return None

    # Try to match against known patterns
    for pattern, output, description in normalization_patterns:
        if re.search(pattern, v, re.IGNORECASE):
            return output

    # Unknown format
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
    """
    config = get_config()
    rename_map = {
        source: target
        for source, target in config.COLUMN_MAPPING.items()
        if source in df.columns
    }
    return df.rename(columns=rename_map)


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], int]:
    """
    Clean and prepare survey data for analysis.
    """
    config = get_config()
    
    # Step 1: Rename columns
    print("DEBUG: Raw Columns from Excel:", df.columns.tolist())
    df = standardize_columns(df)
    print("DEBUG: Renamed Columns:", df.columns.tolist())

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
        
        # Filter out implausible past dates
        mask_invalid_date = df['newscast_date_parsed'].dt.year < 2020
        df.loc[mask_invalid_date, 'newscast_date_parsed'] = pd.NaT
    else:
        df['newscast_date_parsed'] = pd.NaT

    # Fallback: Use 'start_time' if 'newscast_date' is missing/invalid
    if 'start_time' in df.columns:
        start_ts = pd.to_datetime(df['start_time'], errors='coerce')
        # Find rows where we have no valid newscast date BUT we do have a valid start time
        mask_fill = df['newscast_date_parsed'].isna() & start_ts.notna() & (start_ts.dt.year >= 2020)
        
        fill_count = mask_fill.sum()
        if fill_count > 0:
            print(f"DEBUG: Recovered {fill_count} rows using 'start_time'")
            print("DEBUG: Recovered examples:", start_ts[mask_fill].head().tolist())
            # Use the date component of start_time
            df.loc[mask_fill, 'newscast_date_parsed'] = start_ts[mask_fill].dt.floor('D')
        else:
            print("DEBUG: No rows recovered using 'start_time' (either none needed or start_time invalid)")
            if df['newscast_date_parsed'].isna().sum() > 0:
                 print("DEBUG: Still have missing dates. Start time examples:", df['start_time'].head().tolist())
    else:
        print("DEBUG: 'start_time' column NOT found for fallback")


    # Step 4: Convert yes/no to numeric for present metric columns
    present_metrics = [c for c in config.METRIC_COLUMNS if c in df.columns]
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
