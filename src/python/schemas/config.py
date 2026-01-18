"""
Pydantic schemas for configuration validation.

These models define the structure and validation rules for YAML config files.
They provide:
- Runtime validation when loading YAML
- Type hints for IDE autocomplete
- Clear documentation of expected structure
- Default values for optional fields
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class NewscastSlot(BaseModel):
    """
    A single newscast timeslot.

    Attributes:
        id: Unique identifier (e.g., "early-morning")
        label: Display name (e.g., "5 - 7 am")
        start_hour: Start hour in 24-hour format (optional)
        end_hour: End hour in 24-hour format (optional)
        is_streaming: True for streaming-only shows
    """
    id: str
    label: str
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
    is_streaming: bool = False

    @field_validator('start_hour', 'end_hour')
    @classmethod
    def validate_hour(cls, v):
        """Validate hour is in valid 24-hour range."""
        if v is not None and (v < 0 or v > 24):
            raise ValueError(f"Hour must be 0-24, got {v}")
        return v


class Thresholds(BaseModel):
    """Performance thresholds for color coding."""
    good: int = Field(default=80, ge=0, le=100)
    poor: int = Field(default=40, ge=0, le=100)

    @field_validator('poor')
    @classmethod
    def poor_less_than_good(cls, v, info):
        """Ensure poor threshold is less than good threshold."""
        if 'good' in info.data and v >= info.data['good']:
            raise ValueError(f"poor threshold ({v}) must be less than good threshold ({info.data['good']})")
        return v


class Palette(BaseModel):
    """Color palette for charts and tables."""
    primary: str = "#045ea8"
    secondary: str = "#00458c"
    accent: str = "#f36f21"
    alert: str = "#d64541"
    muted: str = "#6d6d6d"
    bg_soft: str = "#dbe6f1"


class StationConfig(BaseModel):
    """
    Complete station configuration.

    This defines everything station-specific:
    - Which newscasts exist and their order
    - Performance thresholds
    - Color palette
    """
    station: Dict[str, str]
    newscasts: List[NewscastSlot]
    thresholds: Thresholds = Field(default_factory=Thresholds)
    palette: Palette = Field(default_factory=Palette)

    @property
    def station_id(self) -> str:
        """Get station ID."""
        return self.station.get('id', 'unknown')

    @property
    def station_name(self) -> str:
        """Get station display name."""
        return self.station.get('name', 'Unknown Station')

    @property
    def timezone(self) -> str:
        """Get station timezone."""
        return self.station.get('timezone', 'America/New_York')

    @property
    def newscast_order(self) -> List[str]:
        """Get ordered list of newscast labels for sorting."""
        return [nc.label for nc in self.newscasts]


class SurveyMetric(BaseModel):
    """
    A single survey metric/question.

    Attributes:
        excel_column: Exact column header from MS Forms export
        internal_name: Snake_case name used in code
        label: Display name for charts/tables
        type: Response type (yes_no, numeric, text)
        description: Optional description
    """
    excel_column: str
    internal_name: str
    label: str
    type: str = "yes_no"
    description: Optional[str] = None


class SurveyConfig(BaseModel):
    """
    Complete survey configuration.

    Defines:
    - Survey metadata
    - Column mappings from Excel to internal names
    - Metric definitions
    - Response value mappings
    """
    survey: Dict[str, str]
    columns: Dict[str, Dict[str, str]]
    metrics: List[SurveyMetric]
    response_mappings: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    date_config: Optional[Dict[str, Any]] = None

    @property
    def survey_id(self) -> str:
        """Get survey ID."""
        return self.survey.get('id', 'unknown')

    @property
    def survey_version(self) -> str:
        """Get survey version."""
        return self.survey.get('version', '1.0')

    @property
    def column_mapping(self) -> Dict[str, str]:
        """Get flat column mapping (Excel -> internal)."""
        mapping = {}
        for section in self.columns.values():
            mapping.update(section)
        return mapping

    @property
    def metric_columns(self) -> List[str]:
        """Get list of internal metric column names."""
        return [m.internal_name for m in self.metrics]


class NormalizationPattern(BaseModel):
    """
    A single newscast normalization pattern.

    Attributes:
        pattern: Regex pattern (case-insensitive)
        output: Standardized output label
        description: Human-readable explanation
        test_cases: Example inputs for testing
    """
    pattern: str
    output: str
    description: str
    test_cases: List[str] = Field(default_factory=list)


class NormalizationConfig(BaseModel):
    """
    Complete normalization configuration.

    Defines regex patterns for normalizing free-text newscast names.
    """
    patterns: List[NormalizationPattern]
    ambiguous_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    normalizer_config: Dict[str, bool] = Field(default_factory=dict)

    @property
    def allow_unknown(self) -> bool:
        """Check if unknown formats should pass through."""
        return self.normalizer_config.get('allow_unknown', True)

    @property
    def warn_on_unknown(self) -> bool:
        """Check if warnings should be emitted for unknown formats."""
        return self.normalizer_config.get('warn_on_unknown', False)
