"""
Pydantic schemas for type-safe data structures.

These schemas define the contracts between:
- Python pipeline and JavaScript frontend
- Pipeline steps (input/output validation)
- Error responses and quality warnings
"""

from .output import (
    ProcessingResult,
    ProcessingSummary,
    ChartData,
    PerNewscastChart,
    WeeklyChart,
    ChartsCollection,
    TablesCollection,
    ExportData,
    QualityReport,
    QualityWarning,
    QualityInfo,
)

from .errors import (
    ErrorResponse,
    ErrorDetail,
)

__all__ = [
    "ProcessingResult",
    "ProcessingSummary",
    "ChartData",
    "PerNewscastChart",
    "WeeklyChart",
    "ChartsCollection",
    "TablesCollection",
    "ExportData",
    "QualityReport",
    "QualityWarning",
    "QualityInfo",
    "ErrorResponse",
    "ErrorDetail",
]
