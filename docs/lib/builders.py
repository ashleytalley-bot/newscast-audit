"""
Metric calculation and table building functions.

This module handles:
- Calculating Yes % for metrics
- Building summary tables
- Identifying data quality issues
- Aggregating weekly trends
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union

from .config_dynamic import get_config


def build_yes_percent_table(df: pd.DataFrame, metric_columns: List[str]) -> pd.DataFrame:
    """
    Calculate 'Yes' percentage for each metric column.
    """
    if df.empty or not metric_columns:
        return pd.DataFrame(columns=['Question', 'Yes %', 'Count'])
        
    config = get_config()

    # Calculate mean of 1s (ignoring NAs), multiply by 100
    means = df[metric_columns].mean(skipna=True) * 100
    counts = df[metric_columns].count()  # Count non-NA values

    # Map internal names to display labels
    # We unfortunately don't have a direct internal->label map in the config object yet 
    # (it is in the YAML but flat mapped in COLUMN_MAPPING).
    # For now, we can inverse lookup COLUMN_MAPPING or just format the snake_case.
    # A robust solution would store labels in config. For this refactor, we'll try to find it.
    
    # Helper to find label from column mapping (Reverse lookup)
    # The COLUMN_MAPPING is 'Excel Header' -> 'internal_name'
    # We want 'internal_name' -> 'Label'
    # Since we don't have explicit labels stored, we will title cased the snake_case
    
    labels = [col.replace('_', ' ').title() for col in metric_columns]

    result = pd.DataFrame({
        'Question': labels,
        'Yes %': means.round(1).values,
        'Count': counts.values
    })

    # Fill NaNs with 0 if needed, or leave as NaN
    # result['Yes %'] = result['Yes %'].fillna(0)

    return result


def build_data_quality_table(df: pd.DataFrame, metric_columns: List[str]) -> pd.DataFrame:
    """
    Calculate data completeness for each metric.
    """
    if df.empty or not metric_columns:
        return pd.DataFrame(columns=['Question', 'Complete %', 'Missing'])

    total_rows = len(df)
    
    # Count non-nulls
    counts = df[metric_columns].count()
    
    # Calculate percentages
    completeness = (counts / total_rows) * 100
    missing = total_rows - counts

    labels = [col.replace('_', ' ').title() for col in metric_columns]

    result = pd.DataFrame({
        'Question': labels,
        'Complete %': completeness.round(1).values,
        'Missing': missing.values
    })

    return result


def weekly_percent_series(df: pd.DataFrame, metric_columns: List[str], 
                         newscast: Optional[str] = None,
                         question: Optional[str] = None) -> Optional[Dict]:
    """
    Calculate weekly aggregate scores, optionally filtered.
    """
    if 'newscast_date_parsed' not in df.columns:
        return None
        
    # Filter by newscast if requested
    data = df.copy()
    if newscast:
        if 'newscast_normalized' not in data.columns:
            return None
        data = data[data['newscast_normalized'] == newscast]
        
    if data.empty:
        return None
        
    # Filter by question if requested
    cols = [question] if question else metric_columns
    
    # Ensure we have date
    data = data.dropna(subset=['newscast_date_parsed'])
    if data.empty:
        return None
        
    # Group by week
    # Sort by date first
    data = data.sort_values('newscast_date_parsed')
    
    # Determine week start (Monday)
    data['week_start'] = data['newscast_date_parsed'].dt.to_period('W-MON').dt.start_time
    
    # Calculate mean for the selected columns
    # If multiple columns, we average them all together per row first?
    # Or average the means? 
    # Standard approach: average of all cells in that block
    
    if len(cols) > 1:
        data['score'] = data[cols].mean(axis=1)
    else:
        data['score'] = data[cols[0]]
        
    weekly = data.groupby('week_start')['score'].mean() * 100
    
    if weekly.empty:
        return None
        
    return {
        "dates": [d.strftime('%m/%d') for d in weekly.index],
        "pct": weekly.values.tolist(),
        "full_dates": [d.strftime('%Y-%m-%d') for d in weekly.index]
    }
