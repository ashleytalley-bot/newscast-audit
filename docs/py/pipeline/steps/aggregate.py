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

        # Build user accountability table
        users_df = None
        if 'name' in df.columns:
            try:
                # Group by Name
                # Fill missing names
                df['name'] = df['name'].fillna('Unknown User').astype(str)
                
                # Calculate metrics per user
                # 1. Audit Count
                user_counts = df.groupby('name').size().rename('Audits')
                
                # 2. Completeness (Percentage of non-empty fields)
                # Count non-null values in metric columns relative to total columns
                numeric_cols = [c for c in metric_columns if c in df.columns]
                
                most_missed_series = None
                
                if numeric_cols:
                    # Metric A: Completeness %
                    row_filled_counts = df[numeric_cols].notna().sum(axis=1)
                    total_fields = len(numeric_cols)
                    
                    if total_fields > 0:
                        row_completeness = (row_filled_counts / total_fields) * 100
                        user_scores = row_completeness.groupby(df['name']).mean()
                    else:
                        user_scores = pd.Series(0.0, index=user_counts.index)
                    
                    user_scores = user_scores.rename('Completeness')

                    # Metric B: Most Often Missed Field
                    # Identify missing values (True/False)
                    missing_mask = df[numeric_cols].isna()
                    # Group by user and sum misses per column
                    user_miss_counts = missing_mask.groupby(df['name']).sum()
                    
                    # Find column with max misses
                    # If max is 0, then "None"
                    max_misses = user_miss_counts.max(axis=1)
                    most_missed_col = user_miss_counts.idxmax(axis=1)
                    
                    # Create series
                    most_missed_series = most_missed_col.where(max_misses > 0, "None")
                    
                    # Convert internal names to human labels?
                    # We need access to config or map. For now, use internal name.
                    # Or better: clean it up (replace underscores with spaces, title case)
                    most_missed_series = most_missed_series.map(
                        lambda x: x.replace('_', ' ').title() if x != "None" else "None"
                    ).rename("Most Missed Metric")

                else:
                    user_scores = pd.Series(0.0, index=user_counts.index, name='Completeness')
                    most_missed_series = pd.Series("None", index=user_counts.index, name="Most Missed Metric")
                
                # Combine
                users_stats = pd.concat([user_counts, user_scores, most_missed_series], axis=1).reset_index()
                
                # Sort by Audits (desc), then Completeness (desc)
                users_df = users_stats.sort_values(['Audits', 'Completeness'], ascending=[False, False])
                
                # Rename Name column for display
                users_df = users_df.rename(columns={'name': 'User'})
                
                # Format Score to 1 decimal
                users_df['Completeness'] = users_df['Completeness'].map('{:.1f}%'.format)

            except Exception as e:
                quality_tracker.add_warning(
                    "Failed to calculate user metrics",
                    count=1,
                    examples=[str(e)]
                )
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
            'volume': volume_df,
            'users': users_df
        })
        context.set('comments', comments)

        return context
