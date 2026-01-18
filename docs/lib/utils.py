"""
Utility functions for processing.
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict, Union, Optional

from .config_dynamic import get_config


class SafeJSONEncoder(json.JSONEncoder):
    """
    JSON Encoder that handles NaN, Infinity, and NumPy types.
    """
    def default(self, obj):
        if isinstance(obj, float):
            if np.isnan(obj):
                return None
            if np.isinf(obj):
                return None
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)


def safe_json_dumps(data: Union[Dict, List]) -> str:
    """Safely dump JSON handling NaNs and NumPy types."""
    return json.dumps(data, cls=SafeJSONEncoder)


def question_labels(metric_ids: List[str]) -> List[str]:
    """Convert snake_case ids to Title Case labels."""
    # Ideally this would look up from config, but we can do algorithmic for now
    return [s.replace('_', ' ').title() for s in metric_ids]


def color_for(value: float) -> str:
    """
    Return color code based on value and configured thresholds.
    """
    if pd.isna(value):
        return get_config().PALETTE['muted']
        
    config = get_config()
    thresholds = config.THRESHOLDS
    palette = config.PALETTE

    if value >= thresholds.get('good', 80):
        return palette['primary']
    elif value <= thresholds.get('poor', 40):
        return palette['alert']
    else:
        return palette['accent']


def sort_newscast_series(series: pd.Series) -> pd.Series:
    """
    Sort a pandas Series of newscast names according to configured order.
    """
    config = get_config()
    order = config.NEWSCAST_ORDER
    
    # Create a mapping {name: index}
    order_map = {name: idx for idx, name in enumerate(order)}
    max_idx = len(order)
    
    # Sort key function
    def sort_key(s):
        return s.map(lambda x: order_map.get(x, max_idx))
        
    return series.sort_values(key=sort_key)


def with_week_start(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Add week_start column to DataFrame."""
    if 'newscast_date_parsed' not in df.columns:
        return None
        
    df_out = df.copy()
    try:
        # Pylint doesn't like dt accessor sometimes
        df_out['week_start'] = df_out['newscast_date_parsed'].dt.to_period('W-MON').dt.start_time
        return df_out
    except Exception:
        return None
