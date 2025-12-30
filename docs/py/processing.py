# ═══════════════════════════════════════════════════════════════════════════
# NEWSCAST AUDIT PROCESSING - Web Version
# Adapted from opex-newscast-audit.qmd for browser execution via Pyodide
# ═══════════════════════════════════════════════════════════════════════════

import pandas as pd
import json
import numpy as np


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles pandas/numpy types."""
    def default(self, obj):
        # Handle pandas NA
        if obj is pd.NA:
            return None
        # Handle numpy types
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            if np.isnan(obj):
                return None
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Handle pandas Timestamp
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        # Handle NaT
        if isinstance(obj, type(pd.NaT)):
            return None
        # Try pd.isna for anything else
        try:
            if pd.isna(obj):
                return None
        except:
            pass
        return super().default(obj)


def safe_json_dumps(obj):
    """Serialize object to JSON, converting NA/NaN to null."""
    # First pass: convert DataFrame dicts which may have NA values
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if o is pd.NA or (isinstance(o, float) and np.isnan(o)):
            return None
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return None if np.isnan(o) else float(o)
        if isinstance(o, pd.Timestamp):
            return o.isoformat() if pd.notna(o) else None
        if isinstance(o, np.ndarray):
            return [clean(v) for v in o.tolist()]
        try:
            if pd.isna(o):
                return None
        except:
            pass
        return o

    cleaned = clean(obj)
    return json.dumps(cleaned)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION SECTION - Safe to customize these settings
# ═══════════════════════════════════════════════════════════════════════════

# Column mapping: Translates MS Forms Excel export column names to clean internal names
# LEFT SIDE (keys): Exact column names from the survey Excel export
# RIGHT SIDE (values): Standardized names used throughout this code
COLUMN_MAPPING = {
    'Id': 'id',
    'Start time': 'start_time',
    'Completion time': 'completion_time',
    'Email': 'email',
    'Name': 'name',
    'Date of newscast:': 'newscast_date',
    'Which newscast are you auditing?': 'newscast',
    'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': 'urgency_and_why_now',
    'Is a tease to streaming in at least every 30 minutes with specific content push for each show?': 'specific_streaming_tease',
    'Did we use streaming content and/or mobile shorts in this show?': 'streaming_or_mobile_shorts',
    'Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?': 'maps_graphics',
    'Is there a clearly defined weather story, supported by graphics or video?': 'weather_story_defined',
    'Does each weather hit focus on new/now/next?': 'new_now_next',
    'Does the story address the audience as "you," end with "Here\'s what you can do today"?': 'address_audience_call_to_action',
    'Are anchors shown three times per show on tight shots with name supers?': 'three_tight_anchor_shots_with_supers',
    'Did we specifically reference every piece of file or non-descript video?': 'reference_file_video',
    'Do anchors add local context to two or more stories and include one community-celebration story per hour?': 'local_context',
    'Additional comments below:': 'additional_comments'
}

# Metric columns: The yes/no audit questions we track and analyze
METRIC_COLUMNS = [
    'urgency_and_why_now',
    'specific_streaming_tease',
    'streaming_or_mobile_shorts',
    'maps_graphics',
    'weather_story_defined',
    'new_now_next',
    'address_audience_call_to_action',
    'three_tight_anchor_shots_with_supers',
    'reference_file_video',
    'local_context'
]

# Performance thresholds: Color-coding for charts
THRESHOLDS = {"good": 80, "poor": 40}

# Newscast timeslot order: Defines how newscasts are sorted (earliest to latest)
NEWSCAST_ORDER = [
    '5 - 7 am',
    '7 - 9 am',
    'noon',
    '5 pm',
    '6 pm',
    '11 pm',
    'E +',
]

# Color palette: Chart and table colors for consistent branding
PALETTE = {
    "primary": "#045ea8",
    "secondary": "#00458c",
    "accent": "#f36f21",
    "alert": "#d64541",
    "muted": "#6d6d6d",
    "bg_soft": "#dbe6f1",
}

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def validate_input_data(df):
    """Validate that the Excel file has expected columns."""
    critical_columns = ['Which newscast are you auditing?', 'Date of newscast:']
    missing = [col for col in critical_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Excel file is missing required columns: {missing}")


def normalize_newscast(value):
    """Map free-text newscast names to standardized timeslots."""
    if pd.isna(value):
        return None
    v = str(value).strip().lower()

    # Remove common separators and normalize for matching
    v_normalized = v.replace('-', ' ').replace(':', ' ').replace('.', ' ')

    # Evening+
    if 'evening+' in v or v.startswith('evening') or 'e+' in v:
        return 'E +'

    # PM shows
    if '11' in v and ('pm' in v or 'p' in v):
        return '11 pm'
    if '6' in v and ('pm' in v or 'p' in v) and '5' not in v:
        return '6 pm'
    if '5' in v and ('pm' in v or 'p' in v) and '6' not in v and '7' not in v:
        return '5 pm'
    if 'noon' in v or ('12' in v and ('pm' not in v or 'noon' in v)):
        return 'noon'

    # Morning shows - check for range patterns first
    # Match: "5-7am", "5a-7a", "5 - 7 am", "5am-7am", "5a - 7a", etc.
    if ('5' in v and '7' in v) and ('a' in v):
        return '5 - 7 am'
    if ('7' in v and '9' in v) and ('a' in v):
        return '7 - 9 am'

    # Single time mentions with am
    if '5' in v and ('am' in v or 'a.m' in v or v.endswith('a')):
        return '5 - 7 am'
    if '7' in v and ('am' in v or 'a.m' in v or v.endswith('a')):
        return '7 - 9 am'

    return str(value).strip()


def convert_to_numeric(v):
    """Convert survey responses into 1/0/NA."""
    if pd.isna(v):
        return pd.NA
    s = str(v).strip().lower()
    if s in ('yes', 'y', 'true', '1'):
        return 1
    if s in ('no', 'n', 'false', '0'):
        return 0
    if s in ('n/a', 'na', 'none', ''):
        return pd.NA
    try:
        num = float(s)
        if num == 1:
            return 1
        if num == 0:
            return 0
    except Exception:
        pass
    return pd.NA


def standardize_columns(df):
    """Rename source columns to snake_case names."""
    rename_map = {source: target for source, target in COLUMN_MAPPING.items() if source in df.columns}
    return df.rename(columns=rename_map)


def clean_data(df):
    """Clean and prepare survey data for analysis."""
    df = standardize_columns(df)
    if 'newscast' in df.columns:
        df['newscast_normalized'] = df['newscast'].apply(normalize_newscast)
    else:
        df['newscast_normalized'] = None

    df['newscast_date_parsed'] = pd.to_datetime(df.get('newscast_date'), errors='coerce') if 'newscast_date' in df.columns else pd.NaT

    present_metrics = [c for c in METRIC_COLUMNS if c in df.columns]
    for col in present_metrics:
        df[col] = df[col].apply(convert_to_numeric)
        df[col] = df[col].astype('Int64')

    dropped_empty = 0
    if present_metrics:
        mask = df[present_metrics].notna().any(axis=1)
        dropped_empty = (~mask).sum()
        df = df[mask].reset_index(drop=True)

    return df, present_metrics, dropped_empty


def question_labels(columns):
    """Human-friendly labels for chart/table display."""
    return [c.replace('_', ' ').title() for c in columns]


def _newscast_sort_key(values):
    """Helper: map newscast names to an order index."""
    order_lookup = {name: idx for idx, name in enumerate(NEWSCAST_ORDER)}
    unknown_rank = len(order_lookup)
    return values.map(lambda v: order_lookup.get(v, unknown_rank))


def sort_newscast_series(s):
    """Sort a series of newscast names by the predefined NEWSCAST_ORDER."""
    return s.sort_values(key=_newscast_sort_key)


def color_for(percent):
    """Pick a palette color based on thresholded performance bands."""
    if pd.isna(percent):
        return PALETTE["muted"]
    if percent >= THRESHOLDS['good']:
        return PALETTE["primary"]
    if percent <= THRESHOLDS['poor']:
        return PALETTE["alert"]
    return PALETTE["accent"]


def with_week_start(df, date_col='newscast_date_parsed'):
    """Add a 'week_start' column showing the Monday of each newscast's week."""
    if date_col not in df.columns or df[date_col].isna().all():
        return None
    out = df.dropna(subset=[date_col]).copy()
    out['week_start'] = out[date_col] - pd.to_timedelta(out[date_col].dt.weekday, unit='D')
    return out


def build_yes_percent_table(df, metric_columns):
    """Return a tidy table of Yes% per question."""
    summary = df[metric_columns].mean(skipna=True) * 100
    summary = summary.round(0).where(summary.notna(), pd.NA).astype("Int64")
    out = summary.rename('Yes %').reset_index().rename(columns={'index': 'Question'})
    out['Question'] = question_labels(out['Question'])
    return out


def build_data_quality_table(df, metric_columns):
    """Build a data quality summary showing completeness per question."""
    completeness = (df[metric_columns].notna().sum() / len(df) * 100).round(1)
    missing = df[metric_columns].isna().sum()
    quality_df = pd.DataFrame({
        'Question': question_labels(metric_columns),
        'Complete %': completeness.values,
        'Missing': missing.values
    })
    return quality_df


def weekly_percent_series(df, metric_columns, newscast=None, question=None):
    """Compute weekly average percent Yes with optional filters."""
    data = df.copy()
    if newscast == "__unspecified":
        data = data[data['newscast_normalized'].isna()]
    elif newscast is not None:
        data = data[data['newscast_normalized'] == newscast]
    if data.empty:
        return None

    metrics = metric_columns
    if question is not None:
        metrics = [question] if question in metric_columns else []
    if not metrics:
        return None

    data = with_week_start(data)
    if data is None or data.empty:
        return None

    data['overall_mean'] = data[metrics].mean(axis=1)
    weekly_agg = data.groupby('week_start')['overall_mean'].mean()
    if weekly_agg.empty:
        return None

    return {
        "dates": [d.strftime('%Y-%m-%d') for d in weekly_agg.index],
        "pct": weekly_agg.values * 100,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING FUNCTION - Called from JavaScript
# ═══════════════════════════════════════════════════════════════════════════

def process_json_data(json_str):
    """
    Main entry point: Process JSON data (parsed from Excel by SheetJS) and return all chart/table data.

    Parameters:
        json_str: JSON string containing array of row objects from Excel

    Returns:
        JSON string with all processed data for charts and tables
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
    missing_newscast = df['newscast_normalized'].isna().sum() if 'newscast_normalized' in df.columns else 0

    # Build tables
    overall_df = build_yes_percent_table(df, metric_columns)
    data_quality_df = build_data_quality_table(df, metric_columns)

    # Recent week
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
        volume = df['newscast_normalized'].value_counts(dropna=False).rename_axis('Newscast').reset_index(name='Responses')
        volume['Newscast'] = volume['Newscast'].fillna('Unspecified')
        volume_df = volume.sort_values(by='Newscast', key=_newscast_sort_key).reset_index(drop=True)

    # Overall chart data
    overall_pct = df[metric_columns].mean(skipna=True) * 100
    overall_chart = {
        "labels": question_labels(overall_pct.index.tolist()),
        "values": [round(v, 0) if pd.notna(v) else 0 for v in overall_pct.values],
        "colors": [color_for(v) for v in overall_pct.values],
        "n": record_count
    }

    # Per-newscast chart data
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

    # Weekly trend data
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
        newscast_options = sort_newscast_series(df['newscast_normalized'].dropna()).unique().tolist()

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

    # Prepare export data
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

    # Build result
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
