"""
Dynamic configuration loader with YAML support and fallback.

This module provides configuration loading from YAML files when available,
with automatic fallback to hardcoded defaults. Works in both Pyodide and
normal Python environments.

Usage:
    from lib.config_dynamic import get_config

    config = get_config()  # Loads from YAML or uses defaults
    print(config.NEWSCAST_ORDER)
    print(config.THRESHOLDS)
"""

import sys
from typing import Optional, Dict, List

# Try to import YAML loader (may not be available in all environments)
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Import hardcoded defaults as fallback
try:
    from . import config as default_config
except ImportError:
    import config as default_config


class Config:
    """
    Configuration container that can load from YAML or use defaults.

    This class provides the same interface as the original config.py module,
    but can dynamically load from YAML files when available.
    """

    def __init__(self):
        """Initialize with default hardcoded values."""
        # Copy all constants from default_config
        self.COLUMN_MAPPING = default_config.COLUMN_MAPPING.copy()
        self.METRIC_COLUMNS = default_config.METRIC_COLUMNS.copy()
        self.THRESHOLDS = default_config.THRESHOLDS.copy()
        self.NEWSCAST_ORDER = default_config.NEWSCAST_ORDER.copy()
        self.PALETTE = default_config.PALETTE.copy()

        # Track whether YAML config is loaded
        self._yaml_loaded = False
        self._station_id = 'default'
        self._survey_id = 'newscast-audit-v1'

    def load_from_yaml_string(self, station_yaml: str, survey_yaml: str) -> None:
        """
        Load configuration from YAML strings.

        This is the primary loading method for Pyodide environments
        where YAML files are fetched as strings.

        Args:
            station_yaml: Station config YAML content
            survey_yaml: Survey config YAML content

        Raises:
            ValueError: If YAML is invalid or required fields missing
        """
        if not HAS_YAML:
            raise RuntimeError("PyYAML not available - cannot load from YAML")

        try:
            station_data = yaml.safe_load(station_yaml)
            survey_data = yaml.safe_load(survey_yaml)

            # Extract station config
            if 'newscasts' in station_data:
                self.NEWSCAST_ORDER = [nc['label'] for nc in station_data['newscasts']]

            if 'thresholds' in station_data:
                self.THRESHOLDS = station_data['thresholds']

            if 'palette' in station_data:
                self.PALETTE = station_data['palette']

            # Extract survey config
            if 'columns' in survey_data:
                # Flatten nested column structure
                self.COLUMN_MAPPING = {}
                for section in survey_data['columns'].values():
                    self.COLUMN_MAPPING.update(section)

            if 'metrics' in survey_data:
                self.METRIC_COLUMNS = [m['internal_name'] for m in survey_data['metrics']]

            self._yaml_loaded = True

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required config field: {e}")

    def is_yaml_loaded(self) -> bool:
        """Check if YAML configuration has been loaded."""
        return self._yaml_loaded

    def get_station_id(self) -> str:
        """Get current station ID."""
        return self._station_id

    def get_survey_id(self) -> str:
        """Get current survey ID."""
        return self._survey_id


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance (creates one if doesn't exist)

    Example:
        >>> config = get_config()
        >>> print(config.NEWSCAST_ORDER)
        ['5 - 7 am', '7 - 9 am', ...]
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def load_config_from_yaml(station_yaml: str, survey_yaml: str) -> Config:
    """
    Load configuration from YAML strings and return config instance.

    Args:
        station_yaml: Station config YAML content
        survey_yaml: Survey config YAML content

    Returns:
        Updated Config instance

    Example:
        >>> with open('config/stations/default.yaml') as f:
        ...     station_yaml = f.read()
        >>> with open('config/surveys/newscast-audit-v1.yaml') as f:
        ...     survey_yaml = f.read()
        >>> config = load_config_from_yaml(station_yaml, survey_yaml)
    """
    config = get_config()
    config.load_from_yaml_string(station_yaml, survey_yaml)
    return config


# For backward compatibility, export the same interface as config.py
# These will use the singleton instance
def get_column_mapping() -> Dict[str, str]:
    """Get column mapping (for backward compatibility)."""
    return get_config().COLUMN_MAPPING


def get_metric_columns() -> List[str]:
    """Get metric columns (for backward compatibility)."""
    return get_config().METRIC_COLUMNS


def get_newscast_order() -> List[str]:
    """Get newscast order (for backward compatibility)."""
    return get_config().NEWSCAST_ORDER


def get_thresholds() -> Dict[str, int]:
    """Get thresholds (for backward compatibility)."""
    return get_config().THRESHOLDS


def get_palette() -> Dict[str, str]:
    """Get color palette (for backward compatibility)."""
    return get_config().PALETTE
