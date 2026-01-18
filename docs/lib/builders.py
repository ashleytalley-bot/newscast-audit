"""
Table and chart data builders.

This module contains functions that compute metrics and build
data structures for tables and charts:
- Overall performance (% Yes per question)
- Data quality metrics (completeness)
- Weekly trend calculations
"""

import pandas as pd
from typing import Optional, List, Dict

from .utils import question_labels, with_week_start


def build_yes_percent_table(
    df: pd.DataFrame,
    metric_columns: List[str]
) -> pd.DataFrame:
    """
    Build a tidy table showing Yes% per question.

    Args:
        df: Cleaned DataFrame with numeric metric columns
        metric_columns: List of metric column names to analyze

    Returns:
        DataFrame with columns: Question, Yes %
    """
    # Calculate mean (treating 1=Yes, 0=No, NA=skip)
    summary = df[metric_columns].mean(skipna=True) * 100

    # Round to integers, preserve NA
    summary = summary.round(0).where(summary.notna(), pd.NA).astype("Int64")

    # Convert to tidy format
    out = summary.rename('Yes %').reset_index().rename(columns={'index': 'Question'})

    # Human-friendly question labels
    out['Question'] = question_labels(out['Question'])

    return out


def build_data_quality_table(
    df: pd.DataFrame,
    metric_columns: List[str]
) -> pd.DataFrame:
    """
    Build a data quality summary showing completeness per question.

    Args:
        df: Cleaned DataFrame with numeric metric columns
        metric_columns: List of metric column names to analyze

    Returns:
        DataFrame with columns: Question, Complete %, Missing
    """
    # Calculate completeness percentage
    completeness = (df[metric_columns].notna().sum() / len(df) * 100).round(1)

    # Calculate missing count
    missing = df[metric_columns].isna().sum()

    # Build table
    quality_df = pd.DataFrame({
        'Question': question_labels(metric_columns),
        'Complete %': completeness.values,
        'Missing': missing.values
    })

    return quality_df


def weekly_percent_series(
    df: pd.DataFrame,
    metric_columns: List[str],
    newscast: Optional[str] = None,
    question: Optional[str] = None
) -> Optional[Dict[str, any]]:
    """
    Compute weekly average percent Yes with optional filters.

    This uses "double averaging":
    1. For each audit, compute the mean across selected questions (row average)
    2. Group by week and compute mean of those row averages (weekly average)

    This approach weights each audit equally regardless of question count,
    which is appropriate when questions are equally important.

    Args:
        df: Cleaned DataFrame with week_start capability
        metric_columns: List of metric columns to consider
        newscast: Optional newscast filter (e.g., "5 - 7 am")
        question: Optional single question filter (e.g., "urgency_and_why_now")

    Returns:
        Dict with "dates" (list of ISO strings) and "pct" (list of percentages),
        or None if no data available
    """
    data = df.copy()

    # Apply newscast filter
    if newscast == "__unspecified":
        data = data[data['newscast_normalized'].isna()]
    elif newscast is not None:
        data = data[data['newscast_normalized'] == newscast]

    if data.empty:
        return None

    # Apply question filter
    metrics = metric_columns
    if question is not None:
        metrics = [question] if question in metric_columns else []

    if not metrics:
        return None

    # Add week_start column
    data = with_week_start(data)
    if data is None or data.empty:
        return None

    # Step 1: Compute row average (mean across questions for each audit)
    data['overall_mean'] = data[metrics].mean(axis=1)

    # Step 2: Compute weekly average (mean of row averages)
    weekly_agg = data.groupby('week_start')['overall_mean'].mean()

    if weekly_agg.empty:
        return None

    return {
        "dates": [d.strftime('%Y-%m-%d') for d in weekly_agg.index],
        "pct": weekly_agg.values * 100,
    }
