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
    
    # Calculate mean for the selected columns
    # We need to replicate the charts.py logic:
    # 1. Weekly Average % (Mean of means is okay for the line, but let's be consistent)
    # 2. P-Bar (Center Line) = Total Yes / Total Opportunities
    # 3. Weekly N = Total Opportunities in that week
    
    # Calculate row-wise stats first
    data['row_sum'] = data[cols].sum(axis=1, skipna=True)
    data['row_count'] = data[cols].count(axis=1) # Opportunities per record
    
    # Group by week
    weekly_group = data.groupby('week_start')
    
    # Weekly N = Sum of opportunities in that week
    weekly_n = weekly_group['row_count'].sum()
    
    # Weekly Yes = Sum of Yeses in that week
    weekly_yes = weekly_group['row_sum'].sum()
    
    # Weekly % = Weekly Yes / Weekly N
    # Handle division by zero
    weekly_pct = (weekly_yes / weekly_n * 100).fillna(0)
    
    # Filter out empty weeks (if any)
    valid_weeks = weekly_n > 0
    weekly_pct = weekly_pct[valid_weeks]
    weekly_n = weekly_n[valid_weeks]
    
    if weekly_pct.empty:
        return None

    # Calculate Global P-bar (Center Line)
    # Total Yes / Total N across all selected data
    total_yes = data['row_sum'].sum()
    total_n = data['row_count'].sum()
    
    p_bar = total_yes / total_n if total_n > 0 else 0
    center_line = round(p_bar * 100, 1)
    
    # Calculate Control Limits
    ucl_values = []
    lcl_values = []
    
    for n_i in weekly_n.values:
        if n_i > 0:
            sigma_i = (p_bar * (1 - p_bar) / n_i) ** 0.5
            ucl = (p_bar + 3 * sigma_i) * 100
            lcl = (p_bar - 3 * sigma_i) * 100
            
            ucl_values.append(round(min(ucl, 100.0), 1))
            lcl_values.append(round(max(lcl, 0.0), 1))
        else:
            ucl_values.append(None)
            lcl_values.append(None)

    return {
        "dates": [d.strftime('%m/%d') for d in weekly_pct.index],
        "pct": weekly_pct.values.tolist(),
        "full_dates": [d.strftime('%Y-%m-%d') for d in weekly_pct.index],
        "n": weekly_n.values.tolist(),
        "center_line": center_line,
        "ucl": ucl_values,
        "lcl": lcl_values
    }
