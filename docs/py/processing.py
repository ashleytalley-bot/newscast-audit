"""
Newscast Audit Processing - Web Application Entry Point

This module provides the main processing function for the web app.
It orchestrates the data cleaning, analysis, and chart preparation pipeline
using the shared lib/ modules.

Called from JavaScript via Pyodide (Python in the browser).
"""

import sys
import os

# Add parent directories to path so we can import from lib/
# This works in Pyodide browser environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import json

from lib import (
    # Config
    PALETTE,
    THRESHOLDS,
    NEWSCAST_ORDER,
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
    sort_newscast_series
)


def _newscast_sort_key(values):
    """Helper for sorting newscasts by NEWSCAST_ORDER."""
    order_lookup = {name: idx for idx, name in enumerate(NEWSCAST_ORDER)}
    unknown_rank = len(order_lookup)
    return values.map(lambda v: order_lookup.get(v, unknown_rank))


def process_json_data(json_str: str) -> str:
    """
    Main entry point: Process JSON data and return all chart/table data.

    This function orchestrates the complete pipeline:
    1. Parse JSON to DataFrame
    2. Validate required columns exist
    3. Clean data (normalize, convert types, drop empty rows)
    4. Build analysis tables (overall, recent week, volume, quality)
    5. Generate chart data (overall, per-newscast, weekly trends)
    6. Package everything as JSON for the web UI

    Args:
        json_str: JSON string containing array of survey row objects from Excel
                  (parsed by SheetJS on the client side)

    Returns:
        JSON string with structure:
        {
            'summary': {record_count, metric_count, missing_newscast, dropped_empty},
            'tables': {overall, data_quality, recent, recent_week_start, volume},
            'charts': {overall, per_newscast, weekly, filter_options},
            'export_data': {...},
            'config': {palette, thresholds, metric_columns}
        }

    Raises:
        ValueError: If input data is invalid or missing required columns
    """
    # Parse JSON to DataFrame
    data = json.loads(json_str)
    df_raw = pd.DataFrame(data)

    # Validate
    validate_input_data(df_raw)

    # Clean
    df, metric_columns, dropped_empty = clean_data(df_raw.copy())

    if not metric_columns:
        raise ValueError("No metric columns found after cleaning.")

    record_count = len(df)
    missing_newscast = (
        df['newscast_normalized'].isna().sum()
        if 'newscast_normalized' in df.columns
        else 0
    )

    # ═══════════════════════════════════════════════════════════════════
    # BUILD TABLES
    # ═══════════════════════════════════════════════════════════════════

    # Overall metrics table
    overall_df = build_yes_percent_table(df, metric_columns)

    # Data quality table
    data_quality_df = build_data_quality_table(df, metric_columns)

    # Recent week metrics
    recent_df = None
    recent_week_start = None
    if 'newscast_date_parsed' in df.columns and df['newscast_date_parsed'].notna().any():
        max_date = df['newscast_date_parsed'].max()
        week_start = max_date - pd.Timedelta(days=max_date.weekday())
        recent = df[df['newscast_date_parsed'] >= week_start]
        if not recent.empty:
            recent_df = build_yes_percent_table(recent, metric_columns)
            recent_week_start = week_start.strftime('%B %d, %Y')

    # Volume by newscast
    volume_df = None
    if 'newscast_normalized' in df.columns:
        volume = (
            df['newscast_normalized']
            .value_counts(dropna=False)
            .rename_axis('Newscast')
            .reset_index(name='Responses')
        )
        volume['Newscast'] = volume['Newscast'].fillna('Unspecified')
        volume_df = volume.sort_values(
            by='Newscast',
            key=_newscast_sort_key
        ).reset_index(drop=True)

    # ═══════════════════════════════════════════════════════════════════
    # BUILD CHART DATA
    # ═══════════════════════════════════════════════════════════════════

    # Overall chart (all responses, all questions)
    overall_pct = df[metric_columns].mean(skipna=True) * 100
    overall_chart = {
        "labels": question_labels(overall_pct.index.tolist()),
        "values": [round(v, 0) if pd.notna(v) else 0 for v in overall_pct.values],
        "colors": [color_for(v) for v in overall_pct.values],
        "n": record_count
    }

    # Per-newscast charts (one horizontal bar chart per newscast)
    per_newscast_charts = []
    if 'newscast_normalized' in df.columns:
        order_lookup = {name: idx for idx, name in enumerate(NEWSCAST_ORDER)}
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

    # Weekly trend chart (overall performance by week)
    weekly_chart = None
    df_week = with_week_start(df)
    if df_week is not None:
        df_week['overall_mean'] = df_week[metric_columns].mean(axis=1)
        weekly_agg = df_week.groupby('week_start')['overall_mean'].mean() * 100
        if not weekly_agg.empty:
            weekly_chart = {
                "dates": [d.strftime('%m/%d') for d in weekly_agg.index],
                "values": [round(v, 1) for v in weekly_agg.values],
                "full_dates": [d.strftime('%Y-%m-%d') for d in weekly_agg.index]
            }

    # Interactive filter options for weekly chart
    filter_options = []
    if 'newscast_normalized' in df.columns:
        newscast_options = sort_newscast_series(
            df['newscast_normalized'].dropna()
        ).unique().tolist()

        # All newscasts | All questions
        base_series = weekly_percent_series(df, metric_columns)
        if base_series:
            filter_options.append({
                "label": "All newscasts | All questions",
                "dates": base_series["dates"],
                "values": [round(v, 1) for v in base_series["pct"]]
            })

        # By newscast
        for nc in newscast_options:
            series = weekly_percent_series(df, metric_columns, newscast=nc)
            if series:
                filter_options.append({
                    "label": f"Newscast: {nc}",
                    "dates": series["dates"],
                    "values": [round(v, 1) for v in series["pct"]]
                })

        # By question
        for q in metric_columns:
            series = weekly_percent_series(df, metric_columns, question=q)
            if series:
                filter_options.append({
                    "label": f"Question: {q.replace('_', ' ').title()}",
                    "dates": series["dates"],
                    "values": [round(v, 1) for v in series["pct"]]
                })

    # ═══════════════════════════════════════════════════════════════════
    # PREPARE EXPORT DATA
    # ═══════════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════════
    # BUILD RESULT
    # ═══════════════════════════════════════════════════════════════════

    result = {
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
            "palette": PALETTE,
            "thresholds": THRESHOLDS,
            "metric_columns": metric_columns
        }
    }

    return safe_json_dumps(result)
