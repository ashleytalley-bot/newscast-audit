"""
Configuration loader for YAML-based configs.

This module handles loading and validating configuration files.
It works in both normal Python and Pyodide (browser) environments.

Usage:
    from config_loader import load_station_config, load_survey_config

    station = load_station_config('default')
    survey = load_survey_config('newscast-audit-v1')
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional

# Handle both package import and direct import
try:
    from .schemas import StationConfig, SurveyConfig, NormalizationConfig
except ImportError:
    from schemas import StationConfig, SurveyConfig, NormalizationConfig


class ConfigLoader:
    """
    Loads and validates YAML configuration files.

    Supports both file system paths (normal Python) and
    string-based loading (for Pyodide/browser environments).
    """

    def __init__(self, config_root: Optional[str] = None):
        """
        Initialize the config loader.

        Args:
            config_root: Root directory for config files.
                        If None, uses PROJECT_ROOT/config
        """
        if config_root is None:
            # Default: config/ relative to this file's parent
            this_file = Path(__file__)
            project_root = this_file.parent.parent.parent
            config_root = project_root / "config"

        self.config_root = Path(config_root)

    def load_yaml(self, file_path: Path) -> dict:
        """
        Load and parse a YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_yaml_from_string(self, yaml_content: str) -> dict:
        """
        Parse YAML from a string (for Pyodide environments).

        Args:
            yaml_content: YAML content as string

        Returns:
            Parsed YAML as dictionary

        Raises:
            yaml.YAMLError: If YAML is malformed
        """
        return yaml.safe_load(yaml_content)

    def load_station_config(self, station_id: str = 'default') -> StationConfig:
        """
        Load and validate a station configuration.

        Args:
            station_id: Station ID (e.g., 'default', 'central-time')

        Returns:
            Validated StationConfig

        Raises:
            FileNotFoundError: If station config doesn't exist
            pydantic.ValidationError: If config is invalid
        """
        file_path = self.config_root / 'stations' / f'{station_id}.yaml'
        data = self.load_yaml(file_path)
        return StationConfig(**data)

    def load_survey_config(self, survey_id: str = 'newscast-audit-v1') -> SurveyConfig:
        """
        Load and validate a survey configuration.

        Args:
            survey_id: Survey ID (e.g., 'newscast-audit-v1')

        Returns:
            Validated SurveyConfig

        Raises:
            FileNotFoundError: If survey config doesn't exist
            pydantic.ValidationError: If config is invalid
        """
        file_path = self.config_root / 'surveys' / f'{survey_id}.yaml'
        data = self.load_yaml(file_path)
        return SurveyConfig(**data)

    def load_normalization_config(self) -> NormalizationConfig:
        """
        Load and validate newscast normalization patterns.

        Returns:
            Validated NormalizationConfig

        Raises:
            FileNotFoundError: If patterns file doesn't exist
            pydantic.ValidationError: If config is invalid
        """
        file_path = self.config_root / 'normalization' / 'newscast-patterns.yaml'
        data = self.load_yaml(file_path)
        return NormalizationConfig(**data)


# Singleton instance for convenience
_default_loader: Optional[ConfigLoader] = None


def get_loader(config_root: Optional[str] = None) -> ConfigLoader:
    """
    Get or create the default ConfigLoader instance.

    Args:
        config_root: Optional config root directory

    Returns:
        ConfigLoader instance
    """
    global _default_loader
    if _default_loader is None or config_root is not None:
        _default_loader = ConfigLoader(config_root)
    return _default_loader


# Convenience functions for easy importing
def load_station_config(station_id: str = 'default', config_root: Optional[str] = None) -> StationConfig:
    """
    Load a station configuration.

    Args:
        station_id: Station ID (e.g., 'default', 'central-time')
        config_root: Optional config root directory

    Returns:
        Validated StationConfig

    Example:
        >>> station = load_station_config('default')
        >>> print(station.newscast_order)
        ['5 - 7 am', '7 - 9 am', '12 pm', ...]
    """
    return get_loader(config_root).load_station_config(station_id)


def load_survey_config(survey_id: str = 'newscast-audit-v1', config_root: Optional[str] = None) -> SurveyConfig:
    """
    Load a survey configuration.

    Args:
        survey_id: Survey ID
        config_root: Optional config root directory

    Returns:
        Validated SurveyConfig

    Example:
        >>> survey = load_survey_config()
        >>> print(survey.metric_columns)
        ['urgency_and_why_now', 'specific_streaming_tease', ...]
    """
    return get_loader(config_root).load_survey_config(survey_id)


def load_normalization_config(config_root: Optional[str] = None) -> NormalizationConfig:
    """
    Load newscast normalization patterns.

    Args:
        config_root: Optional config root directory

    Returns:
        Validated NormalizationConfig

    Example:
        >>> norm = load_normalization_config()
        >>> print(len(norm.patterns))
        20
    """
    return get_loader(config_root).load_normalization_config()
