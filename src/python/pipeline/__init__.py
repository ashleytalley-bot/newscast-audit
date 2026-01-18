"""
Pipeline framework for processing newscast audit data.

This package contains the pipeline architecture that breaks down
the monolithic processing.py into focused, testable steps.

Each step:
- Has a single responsibility
- Is under 100 lines
- Has clear input/output contracts
- Can be tested independently
- Receives configuration from Phase 1 YAML configs

The pipeline pattern makes the code easier for LLMs to understand
and modify since each step is self-contained.
"""

from .base import PipelineStep, PipelineContext
from .orchestrator import ProcessingPipeline

__all__ = [
    "PipelineStep",
    "PipelineContext",
    "ProcessingPipeline",
]
