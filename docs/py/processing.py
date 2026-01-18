"""
Newscast Audit Processing - Enhanced Error Handling

This is an enhanced version of processing.py with comprehensive error handling,
structured error responses, and data quality warnings.

Use this version for production deployments where detailed error feedback is critical.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import traceback
import numpy as np
import json
from typing import List, Dict, Any, Optional

from lib import (
    # Config
    get_config,
    # Cleaners
    validate_input_data,
    clean_data,
    # Builders
    build_yes_percent_table,
    build_data_quality_table,
    weekly_percent_series,
    # Utils
    safe_json_dumps,
    question_labels,
    color_for,
    with_week_start,
    sort_newscast_series,
    # Exceptions
    NewscastAuditError,
    DataValidationError,
    DataQualityWarning,
    ProcessingError,
    EmptyDataError,
    InsufficientDataError,
    create_error_response
)


class DataQualityTracker:
    """Tracks data quality issues during processing."""

    def __init__(self):
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []

    def add_warning(self, message: str, count: int = 0, examples: Optional[List[str]] = None):
        """Add a data quality warning."""
        self.warnings.append({
            "level": "warning",
            "message": message,
            "count": count,
            "examples": (examples or [])[:5]  # Limit to 5 examples
        })

    def add_info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Add informational message."""
        info_item = {"level": "info", "message": message}
        if details:
            info_item.update(details)
        self.info.append(info_item)

    def has_warnings(self) -> bool:
        """Check if any warnings were recorded."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "warnings": self.warnings,
            "info": self.info
        }


def validate_and_clean_data(df_raw: pd.DataFrame, quality_tracker: DataQualityTracker):
    """
    Validate and clean data with quality tracking.

    Args:
        df_raw: Raw DataFrame from Excel
        quality_tracker: Quality tracker to record issues

    Returns:
        Tuple of (cleaned_df, metric_columns, dropped_count)

    Raises:
        DataValidationError: If validation fails
        InsufficientDataError: If too many rows are dropped
    """
    initial_row_count = len(df_raw)
    config = get_config()

    # Validate
    try:
        validate_input_data(df_raw)
    except (EmptyDataError, DataValidationError) as e:
        raise  # Re-raise validation errors

    # Clean
    try:
        df, metric_columns, dropped_empty = clean_data(df_raw.copy())
    except Exception as e:
        raise ProcessingError(
            message="Failed to clean data",
            operation="data_cleaning",
            original_error=e
        )

    # Check if too much data was dropped
    if dropped_empty > 0:
        drop_percentage = (dropped_empty / initial_row_count) * 100
        quality_tracker.add_warning(
            f"Dropped {dropped_empty} rows ({drop_percentage:.1f}%) with no metric data",
            count=dropped_empty
        )

        if drop_percentage > 50:
            raise InsufficientDataError(
                initial_count=initial_row_count,
                final_count=len(df),
                dropped_count=dropped_empty
            )

    # Track unknown newscast formats
    if 'newscast_normalized' in df.columns and 'newscast' in df.columns:
        unknown_mask = (df['newscast'].notna()) & (
            ~df['newscast_normalized'].isin(config.NEWSCAST_ORDER)
        ) & (df['newscast_normalized'].notna())

        if unknown_mask.any():
            unknown_count = unknown_mask.sum()
            unknown_examples = df[unknown_mask]['newscast'].unique()[:5].tolist()
            quality_tracker.add_warning(
                f"Found {unknown_count} responses with unrecognized newscast formats",
                count=unknown_count,
                examples=unknown_examples
            )

    # Track invalid dates
    if 'newscast_date' in df.columns and 'newscast_date_parsed' in df.columns:
        invalid_dates = df['newscast_date'].notna() & df['newscast_date_parsed'].isna()
        if invalid_dates.any():
            invalid_count = invalid_dates.sum()
            invalid_examples = df[invalid_dates]['newscast_date'].unique()[:5].tolist()
            quality_tracker.add_warning(
                f"Found {invalid_count} responses with invalid dates",
                count=invalid_count,
                examples=[str(d) for d in invalid_examples]
            )

    # Track missing newscasts
    missing_newscast = df['newscast_normalized'].isna().sum() if 'newscast_normalized' in df.columns else 0
    if missing_newscast > 0:
        quality_tracker.add_info(
            f"{missing_newscast} responses have no newscast specified",
            {"count": missing_newscast}
        )

    return df, metric_columns, dropped_empty


def process_json_data_with_errors(json_str: str) -> str:
    """
    Main entry point with comprehensive error handling.

    This version returns structured error responses and data quality warnings.

    Args:
        json_str: JSON string containing array of survey row objects

    Returns:
        JSON string with either:
        - Success response with data and quality warnings
        - Error response with detailed error information
    """
    quality_tracker = DataQualityTracker()
    
    # Initialize config check
    try:
        config = get_config()
    except Exception as e:
         error_response = {
            "success": False,
            "error": create_error_response(e)
        }
         return safe_json_dumps(error_response)

    try:
        # Parse JSON to DataFrame
        try:
            data = json.loads(json_str)
            df_raw = pd.DataFrame(data)
        except json.JSONDecodeError as e:
            raise ProcessingError(
                message="Failed to parse JSON data",
                operation="json_parsing",
                original_error=e
            )
        except Exception as e:
            raise ProcessingError(
                message="Failed to create DataFrame from data",
                operation="dataframe_creation",
                original_error=e
            )

        # Validate and clean
        df, metric_columns, dropped_empty = validate_and_clean_data(df_raw, quality_tracker)

        if not metric_columns:
            raise DataValidationError(
                message="No metric columns found after cleaning",
                missing_columns=list(config.METRIC_COLUMNS),
                found_columns=list(df.columns)
            )

        record_count = len(df)
        missing_newscast = (
            df['newscast_normalized'].isna().sum()
            if 'newscast_normalized' in df.columns
            else 0
        )

        # Build tables (with error handling)
        try:
            overall_df = build_yes_percent_table(df, metric_columns)
            data_quality_df = build_data_quality_table(df, metric_columns)
        except Exception as e:
            raise ProcessingError(
                message="Failed to build summary tables",
                operation="table_building",
                original_error=e
            )

        # Recent week
        recent_df = None
        recent_week_start = None
        if 'newscast_date_parsed' in df.columns and df['newscast_date_parsed'].notna().any():
            try:
                max_date = df['newscast_date_parsed'].max()
                week_start = max_date - pd.Timedelta(days=max_date.weekday())
                recent = df[df['newscast_date_parsed'] >= week_start]
                if not recent.empty:
                    recent_df = build_yes_percent_table(recent, metric_columns)
                    recent_week_start = week_start.strftime('%B %d, %Y')
            except Exception as e:
                quality_tracker.add_warning(
                    "Failed to calculate recent week metrics",
                    count=1,
                    examples=[str(e)]
                )

        # Volume by newscast
        volume_df = None
        if 'newscast_normalized' in df.columns:
            try:
                volume = (
                    df['newscast_normalized']
                    .value_counts(dropna=False)
                    .rename_axis('Newscast')
                    .reset_index(name='Responses')
                )
                volume['Newscast'] = volume['Newscast'].fillna('Unspecified')
                order_lookup = {name: idx for idx, name in enumerate(config.NEWSCAST_ORDER)}
                volume_df = volume.sort_values(
                    by='Newscast',
                    key=lambda x: x.map(lambda v: order_lookup.get(v, len(order_lookup)))
                ).reset_index(drop=True)
            except Exception as e:
                quality_tracker.add_warning(
                    "Failed to calculate volume by newscast",
                    count=1,
                    examples=[str(e)]
                )

        # Charts (continue building remaining data as before)
        overall_pct = df[metric_columns].mean(skipna=True) * 100
        overall_chart = {
            "labels": question_labels(overall_pct.index.tolist()),
            "values": [round(v, 0) if pd.notna(v) else 0 for v in overall_pct.values],
            "colors": [color_for(v) for v in overall_pct.values],
            "n": record_count
        }

        # Per-newscast charts
        per_newscast_charts = []
        if 'newscast_normalized' in df.columns:
            order_lookup = {name: idx for idx, name in enumerate(config.NEWSCAST_ORDER)}
            unique_newscasts = sorted(
                [nc for nc in df['newscast_normalized'].dropna().unique()],
                key=lambda x: order_lookup.get(x, len(order_lookup) + 1)
            )
            for nc in unique_newscasts:
                sub = df[df['newscast_normalized'] == nc]
                if sub.empty:
                    continue
                sub_mean = (sub[metric_columns].mean(skipna=True) * 100)
                per_newscast_charts.append({
                    "newscast": nc,
                    "labels": question_labels(sub_mean.index.tolist()),
                    "values": [round(v, 0) if pd.notna(v) else 0 for v in sub_mean.values],
                    "colors": [color_for(v) for v in sub_mean.values],
                    "n": len(sub)
                })

        # Weekly trends
        weekly_chart = None
        df_week = with_week_start(df)
        if df_week is not None:
            df_week['overall_mean'] = df_week[metric_columns].mean(axis=1)
            weekly_agg = df_week.groupby('week_start')['overall_mean'].mean() * 100
            if not weekly_agg.empty:
                weekly_chart = {
                    "dates": [d.strftime('%m/%d') for d in weekly_agg.index],
                    "values": [round(v, 1) if pd.notna(v) else None for v in weekly_agg.values],
                    "full_dates": [d.strftime('%Y-%m-%d') for d in weekly_agg.index]
                }

        # Filter options for interactive weekly chart
        filter_options = []
        if 'newscast_normalized' in df.columns:
            newscast_options = sort_newscast_series(
                df['newscast_normalized'].dropna()
            ).unique().tolist()

            base_series = weekly_percent_series(df, metric_columns)
            if base_series:
                filter_options.append({
                    "label": "All newscasts | All questions",
                    "dates": base_series["dates"],
                    "values": [round(v, 1) if pd.notna(v) else None for v in base_series["pct"]]
                })

            for nc in newscast_options:
                series = weekly_percent_series(df, metric_columns, newscast=nc)
                if series:
                    filter_options.append({
                        "label": f"Newscast: {nc}",
                        "dates": series["dates"],
                        "values": [round(v, 1) if pd.notna(v) else None for v in series["pct"]]
                    })

            for q in metric_columns:
                series = weekly_percent_series(df, metric_columns, question=q)
                if series:
                    filter_options.append({
                        "label": f"Question: {q.replace('_', ' ').title()}",
                        "dates": series["dates"],
                        "values": [round(v, 1) if pd.notna(v) else None for v in series["pct"]]
                    })

        # Export data
        export_data = {
            "normalized": df.to_dict(orient='records'),
            "overall": overall_df.to_dict(orient='records') if overall_df is not None else [],
            "recent": recent_df.to_dict(orient='records') if recent_df is not None else [],
            "volume": volume_df.to_dict(orient='records') if volume_df is not None else [],
            "data_quality": data_quality_df.to_dict(orient='records') if data_quality_df is not None else [],
            "weekly": {
                "dates": weekly_chart["full_dates"] if weekly_chart else [],
                "values": weekly_chart["values"] if weekly_chart else []
            }
        }

        # Build success result
        result = {
            "success": True,
            "summary": {
                "record_count": record_count,
                "metric_count": len(metric_columns),
                "missing_newscast": int(missing_newscast),
                "dropped_empty": int(dropped_empty)
            },
            "tables": {
                "overall": overall_df.to_dict(orient='records'),
                "data_quality": data_quality_df.to_dict(orient='records'),
                "recent": recent_df.to_dict(orient='records') if recent_df is not None else None,
                "recent_week_start": recent_week_start,
                "volume": volume_df.to_dict(orient='records') if volume_df is not None else None
            },
            "charts": {
                "overall": overall_chart,
                "per_newscast": per_newscast_charts,
                "weekly": weekly_chart,
                "filter_options": filter_options
            },
            "export_data": export_data,
            "config": {
                "palette": config.PALETTE,
                "thresholds": config.THRESHOLDS,
                "metric_columns": metric_columns
            },
            "quality": quality_tracker.to_dict()
        }

        return safe_json_dumps(result)

    except NewscastAuditError as e:
        # Handle known error types
        error_response = {
            "success": False,
            "error": e.to_dict()
        }
        return safe_json_dumps(error_response)

    except Exception as e:
        # Handle unexpected errors
        error_response = {
            "success": False,
            "error": create_error_response(e)
        }
        return safe_json_dumps(error_response)


# For backwards compatibility, keep the original function name
# but use the enhanced version
def process_json_data(json_str: str) -> str:
    """
    Main entry point for processing (delegates to enhanced version).
    """
    return process_json_data_with_errors(json_str)
