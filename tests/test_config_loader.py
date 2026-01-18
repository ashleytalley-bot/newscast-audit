"""
Tests for configuration loading and validation.

Tests both the Pydantic schemas and the YAML loader to ensure:
- YAML files are valid and well-formed
- Schema validation catches errors
- Loaded configs match expected values
- Fallback to defaults works correctly
"""

import pytest
import sys
from pathlib import Path

# Add src/python to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src' / 'python'))

from schemas.config import (
    NewscastSlot,
    StationConfig,
    SurveyConfig,
    SurveyMetric,
    NormalizationConfig,
    Thresholds,
    Palette,
)
from config_loader import load_station_config, load_survey_config, load_normalization_config


class TestNewscastSlot:
    """Test NewscastSlot schema."""

    def test_valid_newscast_slot(self):
        """Test creating a valid newscast slot."""
        slot = NewscastSlot(
            id="morning",
            label="7 - 9 am",
            start_hour=7,
            end_hour=9
        )
        assert slot.id == "morning"
        assert slot.label == "7 - 9 am"
        assert slot.start_hour == 7
        assert slot.is_streaming is False

    def test_streaming_slot(self):
        """Test streaming newscast slot."""
        slot = NewscastSlot(
            id="streaming",
            label="E +",
            is_streaming=True
        )
        assert slot.is_streaming is True
        assert slot.start_hour is None

    def test_invalid_hour(self):
        """Test hour validation."""
        with pytest.raises(ValueError, match="Hour must be 0-24"):
            NewscastSlot(
                id="invalid",
                label="Invalid",
                start_hour=25
            )


class TestThresholds:
    """Test Thresholds schema."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        thresh = Thresholds()
        assert thresh.good == 80
        assert thresh.poor == 40

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresh = Thresholds(good=90, poor=50)
        assert thresh.good == 90
        assert thresh.poor == 50

    def test_poor_must_be_less_than_good(self):
        """Test validation that poor < good."""
        with pytest.raises(ValueError, match="poor threshold.*must be less than good"):
            Thresholds(good=60, poor=70)


class TestStationConfig:
    """Test StationConfig loading and validation."""

    def test_load_default_station(self):
        """Test loading default station config."""
        config = load_station_config('default')

        assert config.station_id == "tegna-default"
        assert config.station_name == "TEGNA Default (Eastern)"
        assert config.timezone == "America/New_York"
        assert len(config.newscasts) == 7

    def test_newscast_order_property(self):
        """Test newscast_order property."""
        config = load_station_config('default')

        order = config.newscast_order
        assert order == [
            '5 - 7 am',
            '7 - 9 am',
            '12 pm',
            '5 pm',
            '6 pm',
            '11 pm',
            'E +',
        ]

    def test_newscasts_have_correct_structure(self):
        """Test newscast slots have expected fields."""
        config = load_station_config('default')

        early_morning = config.newscasts[0]
        assert early_morning.id == "early-morning"
        assert early_morning.label == "5 - 7 am"
        assert early_morning.start_hour == 5
        assert early_morning.end_hour == 7
        assert early_morning.is_streaming is False

        streaming = config.newscasts[-1]
        assert streaming.id == "streaming"
        assert streaming.label == "E +"
        assert streaming.is_streaming is True

    def test_thresholds(self):
        """Test threshold values."""
        config = load_station_config('default')

        assert config.thresholds.good == 80
        assert config.thresholds.poor == 40

    def test_palette(self):
        """Test color palette."""
        config = load_station_config('default')

        assert config.palette.primary == "#045ea8"
        assert config.palette.accent == "#f36f21"
        assert config.palette.alert == "#d64541"


class TestSurveyConfig:
    """Test SurveyConfig loading and validation."""

    def test_load_survey_config(self):
        """Test loading survey config."""
        config = load_survey_config('newscast-audit-v1')

        assert config.survey_id == "newscast-audit-v1"
        assert config.survey_version == "1.0"

    def test_column_mapping_property(self):
        """Test flattened column mapping."""
        config = load_survey_config('newscast-audit-v1')

        mapping = config.column_mapping
        assert 'Id' in mapping
        assert mapping['Id'] == 'id'
        assert 'Which newscast are you auditing?' in mapping
        assert mapping['Which newscast are you auditing?'] == 'newscast'

    def test_metric_columns_property(self):
        """Test metric_columns property."""
        config = load_survey_config('newscast-audit-v1')

        metrics = config.metric_columns
        assert len(metrics) == 10
        assert 'urgency_and_why_now' in metrics
        assert 'specific_streaming_tease' in metrics
        assert 'local_context' in metrics

    def test_metrics_structure(self):
        """Test individual metric structure."""
        config = load_survey_config('newscast-audit-v1')

        first_metric = config.metrics[0]
        assert first_metric.internal_name == 'urgency_and_why_now'
        assert first_metric.label == 'Urgency and Why Now'
        assert first_metric.type == 'yes_no'
        assert first_metric.excel_column.startswith('Does each story create urgency')

    def test_response_mappings(self):
        """Test response value mappings."""
        config = load_survey_config('newscast-audit-v1')

        yes_no = config.response_mappings['yes_no']
        assert 'yes' in yes_no['yes_values']
        assert 'no' in yes_no['no_values']
        assert 'n/a' in yes_no['na_values']


class TestNormalizationConfig:
    """Test NormalizationConfig loading."""

    def test_load_normalization_config(self):
        """Test loading normalization patterns."""
        config = load_normalization_config()

        assert len(config.patterns) > 15  # Should have many patterns

    def test_pattern_structure(self):
        """Test pattern objects have correct structure."""
        config = load_normalization_config()

        first_pattern = config.patterns[0]
        assert hasattr(first_pattern, 'pattern')
        assert hasattr(first_pattern, 'output')
        assert hasattr(first_pattern, 'description')
        assert hasattr(first_pattern, 'test_cases')

    def test_patterns_have_test_cases(self):
        """Test patterns include test cases."""
        config = load_normalization_config()

        # Evening Plus pattern should have test cases
        evening_plus = next(p for p in config.patterns if p.output == "E +")
        assert len(evening_plus.test_cases) > 0
        assert "evening+" in [tc.lower() for tc in evening_plus.test_cases]

    def test_ambiguous_patterns_present(self):
        """Test ambiguous patterns are defined."""
        config = load_normalization_config()

        assert len(config.ambiguous_patterns) > 0

    def test_normalizer_config_properties(self):
        """Test normalizer config properties."""
        config = load_normalization_config()

        # Should have default values
        assert isinstance(config.allow_unknown, bool)
        assert isinstance(config.warn_on_unknown, bool)


class TestConfigConsistency:
    """Test consistency between configs."""

    def test_station_newscasts_match_normalization_outputs(self):
        """Test station newscast labels match normalization outputs."""
        station = load_station_config('default')
        norm = load_normalization_config()

        station_labels = set(station.newscast_order)
        pattern_outputs = set(p.output for p in norm.patterns)

        # All pattern outputs should be in station labels
        # (though station may have more labels for edge cases)
        assert pattern_outputs.issubset(station_labels) or station_labels.issubset(pattern_outputs)

    def test_survey_metrics_count(self):
        """Test survey has expected number of metrics."""
        config = load_survey_config('newscast-audit-v1')

        # Should have 10 metrics as per original config
        assert len(config.metrics) == 10


class TestConfigDynamic:
    """Test dynamic config loader (for Pyodide environments)."""

    def test_dynamic_config_loads_from_yaml(self):
        """Test config_dynamic can load from YAML strings."""
        # Import the dynamic config
        sys.path.insert(0, str(project_root / 'docs' / 'lib'))
        from config_dynamic import Config

        config = Config()

        # Load from actual YAML files
        station_yaml_path = project_root / 'config' / 'stations' / 'default.yaml'
        survey_yaml_path = project_root / 'config' / 'surveys' / 'newscast-audit-v1.yaml'

        with open(station_yaml_path) as f:
            station_yaml = f.read()
        with open(survey_yaml_path) as f:
            survey_yaml = f.read()

        config.load_from_yaml_string(station_yaml, survey_yaml)

        # Check values match
        assert config.NEWSCAST_ORDER == [
            '5 - 7 am',
            '7 - 9 am',
            '12 pm',
            '5 pm',
            '6 pm',
            '11 pm',
            'E +',
        ]
        assert len(config.METRIC_COLUMNS) == 10
        assert config.is_yaml_loaded() is True

    def test_dynamic_config_defaults_without_yaml(self):
        """Test config_dynamic uses hardcoded defaults when YAML not loaded."""
        sys.path.insert(0, str(project_root / 'docs' / 'lib'))
        from config_dynamic import Config

        config = Config()

        # Should have default values from config.py
        assert len(config.NEWSCAST_ORDER) > 0
        assert len(config.METRIC_COLUMNS) == 10
        assert config.THRESHOLDS['good'] == 80
        assert config.is_yaml_loaded() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
