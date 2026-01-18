"""
Utility functions and helpers.

This module contains:
- JSON serialization utilities
- Label formatting helpers
- Sorting utilities
- Color mapping functions
- Date manipulation
"""

import json
import pandas as pd
import numpy as np
from typing import List, Optional

from .config import PALETTE, THRESHOLDS, NEWSCAST_ORDER


class SafeJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that handles pandas/numpy types.

    This encoder converts:
    - pandas.NA → null
    - numpy integers → int
    - numpy floats → float (or null if NaN)
    - numpy arrays → list
    - pandas Timestamp → ISO string
    - pandas NaT → null
    """

    def default(self, obj):
        # Handle pandas NA
        if obj is pd.NA:
            return None

        # Handle numpy numeric types
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            if np.isnan(obj):
                return None
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        # Handle pandas temporal types
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, type(pd.NaT)):
            return None

        # Try pd.isna for anything else
        try:
            if pd.isna(obj):
                return None
        except (TypeError, ValueError):
            pass

        return super().default(obj)


def safe_json_dumps(obj) -> str:
    """
    Serialize object to JSON, converting NA/NaN to null.

    This function preprocesses the object to handle pandas/numpy types,
    then uses SafeJSONEncoder for any remaining edge cases.

    Args:
        obj: Object to serialize (typically dict with pandas/numpy values)

    Returns:
        JSON string with all NA/NaN converted to null
    """
    def clean(o):
        """Recursively clean pandas/numpy types."""
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if o is pd.NA or (isinstance(o, float) and np.isnan(o)):
            return None
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return None if np.isnan(o) else float(o)
        if isinstance(o, pd.Timestamp):
            return o.isoformat() if pd.notna(o) else None
        if isinstance(o, np.ndarray):
            return [clean(v) for v in o.tolist()]
        try:
            if pd.isna(o):
                return None
        except (TypeError, ValueError):
            pass
        return o

    cleaned = clean(obj)
    return json.dumps(cleaned, cls=SafeJSONEncoder)


def question_labels(columns: List[str]) -> List[str]:
    """
    Convert internal column names to human-friendly labels for display.

    Converts snake_case to Title Case.

    Args:
        columns: List of internal column names (e.g., "urgency_and_why_now")

    Returns:
        List of human-friendly labels (e.g., "Urgency And Why Now")
    """
    return [c.replace('_', ' ').title() for c in columns]


def _newscast_sort_key(values: pd.Series) -> pd.Series:
    """
    Helper: map newscast names to an order index for sorting.

    Args:
        values: Series of newscast names

    Returns:
        Series of integer sort keys
    """
    order_lookup = {name: idx for idx, name in enumerate(NEWSCAST_ORDER)}
    unknown_rank = len(order_lookup)
    return values.map(lambda v: order_lookup.get(v, unknown_rank))


def sort_newscast_series(s: pd.Series) -> pd.Series:
    """
    Sort a series of newscast names by the predefined NEWSCAST_ORDER.

    Newscasts not in NEWSCAST_ORDER will sort to the end.

    Args:
        s: Series containing newscast names

    Returns:
        Sorted series
    """
    return s.sort_values(key=_newscast_sort_key)


def color_for(percent: Optional[float]) -> str:
    """
    Pick a palette color based on thresholded performance bands.

    Performance bands:
    - >= 80% (THRESHOLDS['good']): primary blue (good)
    - <= 40% (THRESHOLDS['poor']): alert red (poor)
    - Between: accent orange (moderate)
    - NA/missing: muted gray

    Args:
        percent: Performance percentage (0-100)

    Returns:
        Hex color code from PALETTE
    """
    if pd.isna(percent):
        return PALETTE["muted"]
    if percent >= THRESHOLDS['good']:
        return PALETTE["primary"]
    if percent <= THRESHOLDS['poor']:
        return PALETTE["alert"]
    return PALETTE["accent"]


def with_week_start(
    df: pd.DataFrame,
    date_col: str = 'newscast_date_parsed'
) -> Optional[pd.DataFrame]:
    """
    Add a 'week_start' column showing the Monday of each newscast's week.

    Args:
        df: DataFrame with date column
        date_col: Name of the date column (default: 'newscast_date_parsed')

    Returns:
        DataFrame with 'week_start' column, or None if no valid dates
    """
    if date_col not in df.columns or df[date_col].isna().all():
        return None

    out = df.dropna(subset=[date_col]).copy()
    out['week_start'] = out[date_col] - pd.to_timedelta(
        out[date_col].dt.weekday,
        unit='D'
    )

    return out
