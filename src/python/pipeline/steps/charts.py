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
import pandas as pd

# Add docs to path for imports
docs_path = Path(__file__).parent.parent.parent.parent / 'docs'
sys.path.insert(0, str(docs_path))

from lib.config_dynamic import get_config
from lib.utils import question_labels, color_for, with_week_start, sort_newscast_series
from lib.builders import weekly_percent_series
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

        # Weekly trend chart: overall performance over time
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
                    "values": [round(v, 1) if pd.notna(v) else None for v in base_series["pct"]]
                })

            # Filter by newscast
            for nc in newscast_options:
                series = weekly_percent_series(df, metric_columns, newscast=nc)
                if series:
                    filter_options.append({
                        "label": f"Newscast: {nc}",
                        "dates": series["dates"],
                        "values": [round(v, 1) if pd.notna(v) else None for v in series["pct"]]
                    })

            # Filter by question
            for q in metric_columns:
                series = weekly_percent_series(df, metric_columns, question=q)
                if series:
                    filter_options.append({
                        "label": f"Question: {q.replace('_', ' ').title()}",
                        "dates": series["dates"],
                        "values": [round(v, 1) if pd.notna(v) else None for v in series["pct"]]
                    })

        # Update context with charts
        context.set('charts', {
            'overall': overall_chart,
            'per_newscast': per_newscast_charts,
            'weekly': weekly_chart,
            'filter_options': filter_options
        })

        return context
