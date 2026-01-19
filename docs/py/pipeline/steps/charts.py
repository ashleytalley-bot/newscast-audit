"""
Chart generation pipeline step.

Generates chart data structures for:
- Overall metrics bar chart
- Per-newscast comparison charts
- Weekly trend line chart
- Interactive filter options for trends

This is extracted from the chart-building section of process_json_data_with_errors()
in processing.py (lines ~274-348).
"""

import sys
from pathlib import Path
from typing import Optional
import pandas as pd


from lib.config_dynamic import get_config
from lib.utils import question_labels, color_for, with_week_start, sort_newscast_series
from lib.builders import weekly_percent_series
from lib.schemas.output import WeeklyChart
from ..base import PipelineStep, PipelineContext


class ChartGenerationStep(PipelineStep):
    """
    Generates chart data structures for visualization.

    Creates:
    - Overall metrics bar chart (% Yes by question)
    - Per-newscast comparison charts
    - Weekly trend line chart
    - Interactive filter options (by newscast, by question)

    Updates context with chart data ready for Plotly rendering.
    """

    @property
    def name(self) -> str:
        return "Chart Generation"
    
    @property
    def config(self):
        return get_config()

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Generate chart data structures.

        Args:
            context: Pipeline context with cleaned data and metrics

        Returns:
            Context with chart data structures
        """
        df = context.data
        metric_columns = context.get('metric_columns', [])
        record_count = context.get('record_count', len(df))

        # Overall chart: average % Yes across all questions
        overall_pct = df[metric_columns].mean(skipna=True) * 100
        overall_chart = {
            "labels": question_labels(overall_pct.index.tolist()),
            "values": [round(v, 0) if pd.notna(v) else 0 for v in overall_pct.values],
            "colors": [color_for(v) for v in overall_pct.values],
            "n": record_count
        }

        # Per-newscast charts: separate chart for each newscast
        per_newscast_charts = []
        if 'newscast_normalized' in df.columns:
            order_lookup = {name: idx for idx, name in enumerate(get_config().NEWSCAST_ORDER)}
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

        # Weekly trend chart (uses full history regardless of filter)
        history_df = getattr(context, 'full_data', None)
        if history_df is None or history_df.empty:
            history_df = df
            
        weekly_chart = self._generate_weekly_chart(history_df)
        if weekly_chart:
            # Convert Pydantic model to dict for consistency with other charts
            # (or context expects dicts? The schema calls for WeeklyChart model eventually)
            # The context stores dicts usually, but Orchestrator converts to Pydantic.
            # Let's keep it as dict representation for now to minimize friction
            weekly_chart_dict = weekly_chart.model_dump()
        else:
             weekly_chart_dict = None


        # Interactive filter options for weekly trends
        filter_options = []
        if 'newscast_normalized' in df.columns:
            newscast_options = sort_newscast_series(
                df['newscast_normalized'].dropna()
            ).unique().tolist()

            # All newscasts, all questions
            base_series = weekly_percent_series(df, metric_columns)
            if base_series:
                filter_options.append({
                    "label": "All newscasts | All questions",
                    "dates": base_series["dates"],
                    "values": [round(v, 1) if pd.notna(v) else None for v in base_series["pct"]],
                    "center_line": base_series["center_line"],
                    "ucl": base_series["ucl"],
                    "lcl": base_series["lcl"]
                })

            # Filter by newscast
            for nc in newscast_options:
                series = weekly_percent_series(df, metric_columns, newscast=nc)
                if series:
                    filter_options.append({
                        "label": f"Newscast: {nc}",
                        "dates": series["dates"],
                        "values": [round(v, 1) if pd.notna(v) else None for v in series["pct"]],
                        "center_line": series["center_line"],
                        "ucl": series["ucl"],
                        "lcl": series["lcl"]
                    })

            # Filter by question
            for q in metric_columns:
                series = weekly_percent_series(df, metric_columns, question=q)
                if series:
                    filter_options.append({
                        "label": f"Question: {q.replace('_', ' ').title()}",
                        "dates": series["dates"],
                        "values": [round(v, 1) if pd.notna(v) else None for v in series["pct"]],
                        "center_line": series["center_line"],
                        "ucl": series["ucl"],
                        "lcl": series["lcl"]
                    })

        # Update context with charts
        context.set('charts', {
            'overall': overall_chart,
            'per_newscast': per_newscast_charts,
            'weekly': weekly_chart_dict,
            'filter_options': filter_options,
            'date_range': {
                'min': df['newscast_date_parsed'].min().strftime('%Y-%m-%d') if not df.empty and 'newscast_date_parsed' in df.columns else None,
                'max': df['newscast_date_parsed'].max().strftime('%Y-%m-%d') if not df.empty and 'newscast_date_parsed' in df.columns else None
            }
        })

        return context

    def _generate_weekly_chart(self, df: pd.DataFrame) -> Optional[WeeklyChart]:
        """Generate weekly trend data."""
        if df.empty or 'newscast_date' not in df.columns:
            return None

        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['newscast_date']):
            # Attempt to convert if not already datetime
            try:
                df['newscast_date'] = pd.to_datetime(df['newscast_date'])
            except Exception:
                return None

        # Resample by week (starting Monday)
        # We use 'W-MON' frequency
        weekly = df.set_index('newscast_date').sort_index()
        
        # Calculate weekly average of all metrics
        # First, ensure we only numeric columns
        metric_cols = [c for c in self.config.METRIC_COLUMNS if c in df.columns]
        if not metric_cols:
            return None
            
        weekly_metrics = weekly[metric_cols].resample('W-MON').mean() * 100
        
        # Calculate overall weekly average (mean of means)
        weekly_overall = weekly_metrics.mean(axis=1)
        
        # Drop weeks with no data (NaN)
        weekly_overall = weekly_overall.dropna()
        
        if weekly_overall.empty:
            return None

        # Ensure index is treated as DatetimeIndex for strftime
        dt_index = pd.DatetimeIndex(weekly_overall.index)
        dates = dt_index.strftime('%m/%d').tolist()
        full_dates = dt_index.strftime('%Y-%m-%d').tolist()
        values = weekly_overall.values.tolist()
        
        # Round values
        values = [round(v, 1) for v in values]

        # --- P-Chart Calculations ---
        # 1. Calculate Center Line (CL) = Total Yes / Total Opportunities across all weeks
        # We need the count of metrics evaluated per week to calculate sigma.
        # Approximation: weekly_metrics is average %, but we need raw counts or N.
        # We can get N by resampling count.
        
        # Count of non-null metric values per week
        weekly_counts = weekly[metric_cols].resample('W-MON').count().sum(axis=1)
        # Filter to same weeks as overall
        weekly_counts = weekly_counts.loc[weekly_overall.index]
        
        # Calculate P-bar (Center Line)
        # To be precise, P-bar is (Sum of Yes) / (Sum of N).
        # We have mean % (weekly_overall) and N (weekly_counts).
        # Reconstruct "Yes Count": (Mean % / 100) * N
        estimated_yes = (weekly_overall / 100) * weekly_counts
        total_yes = estimated_yes.sum()
        total_n = weekly_counts.sum()
        
        p_bar = total_yes / total_n if total_n > 0 else 0
        center_line = round(p_bar * 100, 1)

        # 2. Calculate Control Limits per week (Stepped limits)
        # Sigma_i = sqrt( p_bar * (1 - p_bar) / n_i )
        # UCL_i = p_bar + 3 * Sigma_i
        # LCL_i = p_bar - 3 * Sigma_i
        
        ucl_values = []
        lcl_values = []
        
        for n_i in weekly_counts.values:
            if n_i > 0:
                sigma_i = (p_bar * (1 - p_bar) / n_i) ** 0.5
                ucl = (p_bar + 3 * sigma_i) * 100
                lcl = (p_bar - 3 * sigma_i) * 100
                
                # Clamp limits
                ucl = min(ucl, 100.0)
                lcl = max(lcl, 0.0)
                
                ucl_values.append(round(ucl, 1))
                lcl_values.append(round(lcl, 1))
            else:
                ucl_values.append(None)
                lcl_values.append(None)

        return WeeklyChart(
            dates=dates,
            values=values,
            full_dates=full_dates,
            center_line=center_line,
            ucl=ucl_values,
            lcl=lcl_values
        )

