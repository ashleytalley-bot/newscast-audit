"""
Newscast Audit Library

Shared code for processing newscast audit survey data.
"""

from .config_dynamic import (
    get_config,
    initialize_config
)

from .cleaners import (
    validate_input_data,
    normalize_newscast,
    convert_to_numeric,
    standardize_columns,
    clean_data
)

from .builders import (
    build_yes_percent_table,
    build_data_quality_table,
    weekly_percent_series
)

from .utils import (
    safe_json_dumps,
    question_labels,
    sort_newscast_series,
    color_for,
    color_for,
    with_week_start
)

from .quality import DataQualityTracker

from .exceptions import (
    NewscastAuditError,
    DataValidationError,
    DataQualityWarning,
    ProcessingError,
    ConfigurationError,
    EmptyDataError,
    InsufficientDataError,
    create_error_response
)

__all__ = [
    # Config
    'get_config',
    'initialize_config',
    # Cleaners
    'validate_input_data',
    'normalize_newscast',
    'convert_to_numeric',
    'standardize_columns',
    'clean_data',
    # Builders
    'build_yes_percent_table',
    'build_data_quality_table',
    'weekly_percent_series',
    # Utils
    'safe_json_dumps',
    'question_labels',
    'sort_newscast_series',
    'color_for',
    'with_week_start',
    # Quality
    'DataQualityTracker',
    # Exceptions
    'NewscastAuditError',
    'DataValidationError',
    'DataQualityWarning',
    'ProcessingError',
    'ConfigurationError',
    'EmptyDataError',
    'InsufficientDataError',
    'create_error_response',
]
