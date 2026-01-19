"""
Aggregation pipeline step.

Builds summary tables from cleaned data:
- Overall yes percentage table
- Data quality/completeness table
- Recent week metrics
- Volume by newscast

This is extracted from the table-building section of process_json_data_with_errors()
in processing.py (lines ~222-273).
"""

import sys
from pathlib import Path
import pandas as pd


from lib.builders import build_yes_percent_table, build_data_quality_table
from lib.config_dynamic import get_config
from lib.exceptions import ProcessingError, DataValidationError
from ..base import PipelineStep, PipelineContext


class AggregationStep(PipelineStep):
    """
    Aggregates cleaned data into summary tables.

    Builds:
    - Overall % Yes table for all metrics
    - Data quality/completeness table
    - Recent week metrics (if dates available)
    - Volume by newscast

    Updates context with table DataFrames ready for rendering.
    """

    @property
    def name(self) -> str:
        return "Data Aggregation"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Build summary tables from cleaned data.

        Args:
            context: Pipeline context with cleaned data

        Returns:
            Context with summary tables

        Raises:
            ProcessingError: If table building fails
            DataValidationError: If no metric columns found
        """
        df = context.data
        metric_columns = context.get('metric_columns', [])
        quality_tracker = context.quality_tracker

        if not metric_columns:
            raise DataValidationError(
                message="No metric columns found after cleaning",
                missing_columns=list(metric_columns) if metric_columns else [],
                found_columns=list(df.columns)
            )

        # Build overall summary table
        try:
            overall_df = build_yes_percent_table(df, metric_columns)
            data_quality_df = build_data_quality_table(df, metric_columns)
        except Exception as e:
            raise ProcessingError(
                message="Failed to build summary tables",
                operation="table_building",
                original_error=e
            )

        # Build recent week table (if dates available)
        recent_df = None
        recent_week_start = None

        # Use full_data if available (to ignore global filters for this specific table), else current data
        history_df = getattr(context, 'full_data', None)
        if history_df is None or history_df.empty:
            history_df = df

        if 'newscast_date_parsed' in history_df.columns and history_df['newscast_date_parsed'].notna().any():
            try:
                max_date = history_df['newscast_date_parsed'].max()
                week_start = max_date - pd.Timedelta(days=max_date.weekday())
                recent = history_df[history_df['newscast_date_parsed'] >= week_start]
                if not recent.empty:
                    recent_df = build_yes_percent_table(recent, metric_columns)
                    recent_week_start = week_start.strftime('%B %d, %Y')
            except Exception as e:
                quality_tracker.add_warning(
                    "Failed to calculate recent week metrics",
                    count=1,
                    examples=[str(e)]
                )

        # Build volume by newscast table
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

                # Sort by newscast order
                order_lookup = {name: idx for idx, name in enumerate(get_config().NEWSCAST_ORDER)}
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

        # Extract comments
        comments = []
        if 'additional_comments' in df.columns:
            # Filter for non-empty comments
            comments_df = df[df['additional_comments'].notna() & (df['additional_comments'] != '')].copy()
            
            # Sort by date (descending) if possible
            if 'newscast_date' in comments_df.columns:
                # Convert to datetime if needed for sorting (though pipeline likely handled it)
                # Just robustly sort
                comments_df['sort_date'] = pd.to_datetime(comments_df['newscast_date'], errors='coerce')
                comments_df = comments_df.sort_values('sort_date', ascending=False)
            
            for _, row in comments_df.iterrows():
                # Format date
                date_str = "Unknown Date"
                if 'newscast_date' in row and pd.notna(row['newscast_date']):
                    ts = pd.to_datetime(row['newscast_date'])
                    date_str = ts.strftime('%B %d, %Y')
                
                # Format newscast
                newscast_str = row.get('newscast_normalized', 'Unknown Newscast')
                if pd.isna(newscast_str):
                    newscast_str = "Unknown Newscast"

                comments.append({
                    "date": date_str,
                    "newscast": newscast_str,
                    "text": str(row['additional_comments'])
                })

        # Update context with tables and comments
        context.set('tables', {
            'overall': overall_df,
            'data_quality': data_quality_df,
            'recent': recent_df,
            'recent_week_start': recent_week_start,
            'volume': volume_df
        })
        context.set('comments', comments)

        return context
