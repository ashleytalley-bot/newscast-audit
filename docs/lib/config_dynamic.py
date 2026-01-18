"""
Dynamic configuration loader with YAML support.

This module acts as the Single Source of Truth for the application's configuration.
Unlike the old hardcoded `config.py`, this module starts EMPTY and must be "hydrated"
with YAML content fetched from the server.

Workflow:
1. Frontend (`app.js`) fetches .yaml files from `docs/config/`.
2. Frontend injects these YAML strings into Python via `initialize_config()`.
3. This module parses the YAML and populates the `Config` singleton.
4. Other modules (`cleaners.py`, `builders.py`) call `get_config()` to access settings.
"""

import sys
from typing import Optional, Dict, List, Tuple
import yaml  # type: ignore

class Config:
    """
    Configuration container populated from YAML.
    """

    def __init__(self):
        """Initialize empty config."""
        self.COLUMN_MAPPING: Dict[str, str] = {}
        self.METRIC_COLUMNS: List[str] = []
        self.THRESHOLDS: Dict[str, int] = {}
        self.NEWSCAST_ORDER: List[str] = []
        self.PALETTE: Dict[str, str] = {}
        
        # New: Normalization patterns
        # List of (pattern, output, description) tuples
        self.NORMALIZATION_PATTERNS: List[Tuple[str, str, str]] = []
        self.AMBIGUOUS_PATTERNS: List[Tuple[str, str]] = []
        self.NORMALIZER_CONFIG: Dict = {}

        self._yaml_loaded = False
        self._station_id = 'default'
        self._survey_id = 'newscast-audit-v1'

    def load_from_yaml_string(self, station_yaml: str, survey_yaml: str, cleaning_yaml: str) -> None:
        """
        Load configuration from YAML strings.

        Args:
            station_yaml: Station config YAML content
            survey_yaml: Survey config YAML content
            cleaning_yaml: Normalization/Cleaning patterns YAML content

        Raises:
            ValueError: If YAML is invalid or required fields missing
        """
        try:
            station_data = yaml.safe_load(station_yaml)
            survey_data = yaml.safe_load(survey_yaml)
            cleaning_data = yaml.safe_load(cleaning_yaml)

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
                # Add metrics to column mapping
                for m in survey_data['metrics']:
                    if 'excel_column' in m and 'internal_name' in m:
                        self.COLUMN_MAPPING[m['excel_column']] = m['internal_name']
                
            # Extract normalization config
            if 'patterns' in cleaning_data:
                 # Convert YAML list of dicts to list of tuples for the cleaner
                 # YAML: - {pattern: '...', output: '...', description: '...'}
                 # Tuple: (pattern, output, description)
                 self.NORMALIZATION_PATTERNS = []
                 for p in cleaning_data['patterns']:
                     self.NORMALIZATION_PATTERNS.append(
                         (p['pattern'], p['output'], p.get('description', ''))
                     )
            
            if 'ambiguous_patterns' in cleaning_data:
                self.AMBIGUOUS_PATTERNS = []
                for p in cleaning_data['ambiguous_patterns']:
                    self.AMBIGUOUS_PATTERNS.append(
                        (p['pattern'], p.get('reason', ''))
                    )
            
            if 'normalizer_config' in cleaning_data:
                self.NORMALIZER_CONFIG = cleaning_data['normalizer_config']

            self._yaml_loaded = True

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required config field: {e}")
        except Exception as e:
            raise ValueError(f"Configuration initialization failed: {e}")

    def is_yaml_loaded(self) -> bool:
        """Check if YAML configuration has been loaded."""
        return self._yaml_loaded


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Raises:
        RuntimeError: If config has not been initialized yet.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    
    # Optional: Strictly enforce initialization
    # if not _config_instance.is_yaml_loaded():
    #    raise RuntimeError("Configuration not initialized! Call initialize_config() first.")
        
    return _config_instance


def initialize_config(station_yaml: str, survey_yaml: str, cleaning_yaml: str) -> None:
    """
    Initialize the global configuration with YAML content.
    """
    config = get_config()
    config.load_from_yaml_string(station_yaml, survey_yaml, cleaning_yaml)
