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
from .datetime_utils import parse_date_column


# Unicode quote normalization mapping
# Maps curly/smart quotes to their ASCII equivalents
QUOTE_NORMALIZATION = {
    '\u201c': '"',  # " left double quotation mark
    '\u201d': '"',  # " right double quotation mark
    '\u2018': "'",  # ' left single quotation mark
    '\u2019': "'",  # ' right single quotation mark
    '\u2032': "'",  # ′ prime (sometimes used as apostrophe)
    '\u2033': '"',  # ″ double prime
}


def normalize_quotes(text: str) -> str:
    """
    Normalize curly/smart quotes to ASCII equivalents.

    MS Forms and other Microsoft products often use typographic quotes
    (U+201C, U+201D, U+2018, U+2019) instead of ASCII quotes. This causes
    exact string matching to fail even when text looks identical.

    Args:
        text: String that may contain curly quotes

    Returns:
        String with all curly quotes replaced by ASCII equivalents
    """
    for curly, straight in QUOTE_NORMALIZATION.items():
        text = text.replace(curly, straight)
    return text


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
        return 0 # User requested blanks/swapped to 0

    s = str(v).strip().lower()

    # Yes responses
    if s in ('yes', 'y', 'true', '1'):
        return 1

    # No responses
    if s in ('no', 'n', 'false', '0'):
        return 0

    # N/A explicitly marked should still be NA
    if s in ('n/a', 'na', 'none'):
        return pd.NA

    # Blanks/Empty strings now treated as "No" (0) per user request
    if s == '':
        return 0

    # Try numeric parsing
    try:
        num = float(s)
        if num == 1:
            return 1
        if num == 0:
            return 0
    except (ValueError, TypeError):
        pass

    # Unknown format - return sentinel for tracking (will be converted to NA after tracking)
    return 'UNKNOWN_VALUE'


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename source columns to snake_case names using COLUMN_MAPPING.

    Uses quote-normalized matching to handle MS Forms curly quotes.
    Both the Excel column headers and config keys are normalized before
    comparison, so "you" matches "you" regardless of quote style.
    """
    config = get_config()

    # Normalize both sides for matching
    # Create lookup: normalized_source -> (original_source, target)
    normalized_config = {
        normalize_quotes(source): (source, target)
        for source, target in config.COLUMN_MAPPING.items()
    }

    rename_map = {}
    for col in df.columns:
        normalized_col = normalize_quotes(col)
        if normalized_col in normalized_config:
            _, target = normalized_config[normalized_col]
            rename_map[col] = target

    return df.rename(columns=rename_map)


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], int]:
    """
    Clean and prepare survey data for analysis.
    """
    config = get_config()
    
    # Step 1: Rename columns
    df = standardize_columns(df)

    # Step 2: Normalize newscast names
    if 'newscast' in df.columns:
        df['newscast_normalized'] = df['newscast'].apply(normalize_newscast)
    else:
        df['newscast_normalized'] = None

    # Step 3: Parse dates using centralized datetime utilities
    # This consolidates the scattered date parsing logic and handles:
    # - Timezone-naive dates (as expected from Excel)
    # - Fallback from newscast_date to start_time
    # - Validation of plausible date ranges (2020-2030)
    if 'newscast_date' in df.columns:
        fallback_series = df.get('start_time', None)
        df['newscast_date_parsed'] = parse_date_column(
            df['newscast_date'],
            fallback_series=fallback_series
        )
    else:
        df['newscast_date_parsed'] = pd.NaT


    # Step 4: Convert yes/no to numeric for present metric columns
    present_metrics = [c for c in config.METRIC_COLUMNS if c in df.columns]
    for col in present_metrics:
        df[col] = df[col].apply(convert_to_numeric)

    # Step 5: Drop empty rows (all metric columns are NA)
    dropped_empty = 0
    if present_metrics:
        mask = df[present_metrics].notna().any(axis=1)
        dropped_empty = (~mask).sum()
        df = df[mask].reset_index(drop=True)

    return df, present_metrics, dropped_empty
