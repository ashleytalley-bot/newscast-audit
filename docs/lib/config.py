"""
Configuration constants for newscast audit processing.

This module contains all configuration that rarely changes:
- Column mappings from Excel exports
- Metric definitions
- Performance thresholds
- Newscast ordering
- Color palette
"""

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
# Values >= 'good' are colored with primary (blue)
# Values <= 'poor' are colored with alert (red)
# Values in between are colored with accent (orange)
THRESHOLDS = {
    "good": 80,
    "poor": 40
}

# Newscast timeslot order: Defines how newscasts are sorted (earliest to latest)
NEWSCAST_ORDER = [
    '5 - 7 am',
    '7 - 9 am',
    '12 pm',
    '5 pm',
    '6 pm',
    '11 pm',
    'E +',
]

# Color palette: Chart and table colors for consistent TEGNA branding
PALETTE = {
    "primary": "#045ea8",      # TEGNA blue - for good performance
    "secondary": "#00458c",    # Dark blue - alternative
    "accent": "#f36f21",       # Orange - for moderate performance
    "alert": "#d64541",        # Red - for poor performance
    "muted": "#6d6d6d",        # Gray - for missing data
    "bg_soft": "#dbe6f1",      # Light blue background
}
