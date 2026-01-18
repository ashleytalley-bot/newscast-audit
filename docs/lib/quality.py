"""
Data Quality Tracking.

Provides utilities for tracking and reporting data quality issues
throughout the processing pipeline.
"""

from typing import List, Dict, Any, Optional


class DataQualityTracker:
    """Tracks data quality issues during processing."""

    def __init__(self):
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []

    def add_warning(self, message: str, count: int = 0, examples: Optional[List[str]] = None):
        """Add a data quality warning."""
        self.warnings.append({
            "level": "warning",
            "message": message,
            "count": count,
            "examples": (examples or [])[:5]  # Limit to 5 examples
        })

    def add_info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Add informational message."""
        info_item = {"level": "info", "message": message}
        if details:
            info_item.update(details)
        self.info.append(info_item)

    def has_warnings(self) -> bool:
        """Check if any warnings were recorded."""
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "warnings": self.warnings,
            "info": self.info
        }
