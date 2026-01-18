"""
Unit tests for lib/config_dynamic.py
"""

import pytest
import yaml
from lib.config_dynamic import Config, get_config, initialize_config

# Constants for testing
STATION_YAML = """
station:
  id: "test-station"
  name: "Test Station"
  timezone: "America/New_York"

newscasts:
  - id: "morning"
    label: "morning"
    start_hour: 7
    end_hour: 9

thresholds:
  good: 90
  poor: 30

palette:
  primary: "#000000"
"""

SURVEY_YAML = """
survey:
  id: "test-survey"
  version: "1.0"

columns:
  metrics:
    "Test Question?": "test_metric"
    "Another Question": "another_metric"

metrics:
  - excel_column: "Test Question?"
    internal_name: "test_metric"
    label: "Test Metric"
    type: "yes_no"
"""

NORM_YAML = """
patterns:
  - pattern: 'test'
    output: 'Test Output'
    description: 'Test Pattern'
"""

class TestConfigDynamic:
    """Tests for Config class."""

    def test_dynamic_config_loads_from_yaml(self):
        """Should correctly parse YAML content."""
        config = Config()
        config.load_from_yaml_string(STATION_YAML, SURVEY_YAML, NORM_YAML)
        
        assert config.is_yaml_loaded()
        assert config.THRESHOLDS['good'] == 90
        assert config.NEWSCAST_ORDER == ['morning']
        assert config.COLUMN_MAPPING['Test Question?'] == 'test_metric'
        assert 'test_metric' in config.METRIC_COLUMNS
        assert len(config.NORMALIZATION_PATTERNS) == 1
        assert config.NORMALIZATION_PATTERNS[0][1] == 'Test Output'

    def test_singleton_access(self):
        """Should return same instance via get_config()."""
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2
    
    def test_initialization_global(self):
        """Should initialize the global config."""
        initialize_config(STATION_YAML, SURVEY_YAML, NORM_YAML)
        config = get_config()
        
        assert config.is_yaml_loaded()
        assert config.THRESHOLDS['good'] == 90
