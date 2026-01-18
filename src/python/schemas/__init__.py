"""
Pydantic schemas for configuration and data validation.

This package contains type-safe schemas that:
- Validate YAML configuration files
- Define contracts for data interchange
- Provide runtime type checking
- Generate documentation
"""

from .config import (
    NewscastSlot,
    StationConfig,
    SurveyMetric,
    SurveyConfig,
    NormalizationPattern,
    NormalizationConfig,
)

__all__ = [
    "NewscastSlot",
    "StationConfig",
    "SurveyMetric",
    "SurveyConfig",
    "NormalizationPattern",
    "NormalizationConfig",
]
