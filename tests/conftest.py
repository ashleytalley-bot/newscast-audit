import sys
import os
import pytest
from pathlib import Path

# Add docs directory to sys.path so we can import 'lib' from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../docs')))

from lib.config_dynamic import initialize_config

@pytest.fixture(autouse=True, scope="session")
def setup_config():
    """
    Initialize global configuration from YAML files for testing.
    This mimics the app loading behavior.
    """
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "docs/config"
    
    # Read files
    with open(config_dir / "stations/default.yaml") as f:
        station_yaml = f.read()
    
    with open(config_dir / "surveys/newscast-audit-v1.yaml") as f:
        survey_yaml = f.read()
        
    with open(config_dir / "normalization/newscast-patterns.yaml") as f:
        norm_yaml = f.read()
        
    # Initialize
    # Note: We do this at session scope to do it once, but 
    # since config is a singleton, it persists.
    initialize_config(station_yaml, survey_yaml, norm_yaml)
