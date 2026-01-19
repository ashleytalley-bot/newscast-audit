"""
Output schemas for pipeline processing results.

These schemas define the exact structure of successful pipeline responses.
They serve as the contract between Python backend and JavaScript frontend.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProcessingSummary(BaseModel):
    """Summary statistics about the processing run."""

    record_count: int = Field(
        description="Number of audit records processed"
    )
    metric_count: int = Field(
        description="Number of metrics tracked (should be 10)"
    )
    missing_newscast: int = Field(
        description="Number of records with missing/invalid newscast names"
    )
    dropped_empty: int = Field(
        description="Number of records dropped due to having no metric data"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "record_count": 42,
                "metric_count": 10,
                "missing_newscast": 2,
                "dropped_empty": 1,
            }
        }
    )


class ChartData(BaseModel):
    """Data for an overall performance chart."""

    labels: List[str] = Field(
        description="Human-readable metric names"
    )
    values: List[float] = Field(
        description="Percentage values (0-100) for each metric"
    )
    colors: List[str] = Field(
        description="Hex color codes for each bar (from palette)"
    )
    n: int = Field(
        description="Number of audits included in this chart"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "labels": ["Urgency And Why Now", "Streaming Tease Every 30min"],
                "values": [85.0, 72.0],
                "colors": ["#045ea8", "#f36f21"],
                "n": 42,
            }
        }
    )


class PerNewscastChart(ChartData):
    """Chart data for a specific newscast timeslot."""

    newscast: str = Field(
        description="Newscast timeslot label (e.g., '5 - 7 am', '6 pm')"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "newscast": "6 pm",
                "labels": ["Urgency And Why Now", "Streaming Tease Every 30min"],
                "values": [88.0, 75.0],
                "colors": ["#045ea8", "#f36f21"],
                "n": 15,
            }
        }
    )


class WeeklyChart(BaseModel):
    """Time series data for weekly trends."""

    dates: List[str] = Field(
        description="Short date labels (MM/DD format)"
    )
    values: List[Optional[float]] = Field(
        description="Weekly average percentages (can be null for missing weeks)"
    )
    full_dates: List[str] = Field(
        description="Full ISO date strings (YYYY-MM-DD)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dates": ["01/08", "01/15", "01/22"],
                "values": [82.5, 85.0, 83.2],
                "full_dates": ["2024-01-08", "2024-01-15", "2024-01-22"],
            }
        }
    )


class FilterOption(BaseModel):
    """Interactive filter option for weekly trends."""

    label: str = Field(
        description="Filter label shown in dropdown"
    )
    dates: List[str] = Field(
        description="Full ISO dates for this filtered series"
    )
    values: List[Optional[float]] = Field(
        description="Weekly percentages for this filter"
    )


class ChartsCollection(BaseModel):
    """Collection of all chart data."""

    overall: ChartData = Field(
        description="Overall performance across all newscasts"
    )
    per_newscast: List[PerNewscastChart] = Field(
        description="Performance broken down by newscast timeslot"
    )
    weekly: Optional[WeeklyChart] = Field(
        default=None,
        description="Weekly trends over time (null if no date data)"
    )
    filter_options: List[FilterOption] = Field(
        default_factory=list,
        description="Interactive filter options for weekly chart"
    )


class TablesCollection(BaseModel):
    """Collection of all summary tables."""

    overall: List[Dict[str, Any]] = Field(
        description="Overall performance table (Question, Yes %, Count)"
    )
    data_quality: List[Dict[str, Any]] = Field(
        description="Data quality metrics (Question, Completeness %, Missing)"
    )
    recent: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Recent week performance (null if no recent data)"
    )
    recent_week_start: Optional[str] = Field(
        default=None,
        description="Start date of recent week (readable format)"
    )
    volume: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Audit volume by newscast"
    )


class QualityWarning(BaseModel):
    """A data quality warning."""

    level: str = Field(
        description="Severity level (always 'warning')"
    )
    message: str = Field(
        description="Human-readable warning message"
    )
    count: int = Field(
        default=0,
        description="Number of occurrences"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example values that triggered this warning (max 5)"
    )


class QualityInfo(BaseModel):
    """Informational quality message."""

    level: str = Field(
        description="Message level (always 'info')"
    )
    message: str = Field(
        description="Human-readable info message"
    )


class QualityReport(BaseModel):
    """Data quality tracking report."""

    warnings: List[QualityWarning] = Field(
        default_factory=list,
        description="Non-fatal data quality warnings"
    )
    info: List[QualityInfo] = Field(
        default_factory=list,
        description="Informational messages"
    )


class ExportData(BaseModel):
    """Data prepared for Excel/PowerPoint export."""

    normalized: List[Dict[str, Any]] = Field(
        description="Cleaned and normalized audit records"
    )
    overall: List[Dict[str, Any]] = Field(
        description="Overall performance table data"
    )
    recent: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent week data"
    )
    volume: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Volume by newscast"
    )
    data_quality: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Data quality metrics"
    )
    weekly: Dict[str, Any] = Field(
        default_factory=dict,
        description="Weekly trends data"
    )


class ConfigPassthrough(BaseModel):
    """Configuration passed to frontend."""

    palette: Dict[str, str] = Field(
        description="Color palette (primary, accent, alert, etc.)"
    )
    thresholds: Dict[str, int] = Field(
        description="Performance thresholds (good, poor)"
    )
    metric_columns: List[str] = Field(
        description="List of metric column internal names"
    )


class Comment(BaseModel):
    """A single user comment from the audit."""

    date: str = Field(description="Date of the newscast")
    newscast: str = Field(description="Newscast audited")
    text: str = Field(description="The comment text")


class ProcessingResult(BaseModel):
    """Successful processing result - the main output contract."""

    success: bool = Field(
        default=True,
        description="Always true for successful processing"
    )
    summary: ProcessingSummary = Field(
        description="Summary statistics"
    )
    tables: TablesCollection = Field(
        description="All summary tables"
    )
    charts: ChartsCollection = Field(
        description="All chart data"
    )
    comments: List[Comment] = Field(
        default_factory=list,
        description="List of all additional comments"
    )
    export_data: ExportData = Field(
        description="Data for export functionality"
    )
    config: ConfigPassthrough = Field(
        description="Configuration for frontend"
    )
    quality: QualityReport = Field(
        description="Data quality warnings and info"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Main processing result returned to frontend",
            "example": {
                "success": True,
                "summary": {
                    "record_count": 42,
                    "metric_count": 10,
                    "missing_newscast": 2,
                    "dropped_empty": 1,
                },
                # ... other fields
            },
        }
    )
