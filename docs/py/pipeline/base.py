"""
Base classes for pipeline architecture.

Defines the abstract PipelineStep interface and PipelineContext
for passing data between steps.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd


class PipelineContext:
    """
    Context object that flows through the pipeline.

    Stores intermediate results and metadata as steps execute.
    Each step can read from and write to the context.

    Attributes:
        data: The main DataFrame being processed
        metadata: Dictionary of step outputs and intermediate results
        quality_tracker: Tracks data quality warnings and info
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize pipeline context.

        Args:
            data: Initial DataFrame to process
        """
        self.data = data
        self.metadata: Dict[str, Any] = {}
        self.quality_tracker = None  # Will be set by orchestrator

    def set(self, key: str, value: Any) -> None:
        """Store a value in the context."""
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the context."""
        return self.metadata.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a key exists in the context."""
        return key in self.metadata


class PipelineStep(ABC):
    """
    Abstract base class for pipeline steps.

    Each step:
    - Receives a PipelineContext
    - Performs a single, focused operation
    - Updates the context with results
    - Returns the updated context

    Steps should be stateless - all state flows through the context.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name for this step.

        Used in logging and error messages.
        """
        pass

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Execute this pipeline step.

        Args:
            context: Pipeline context with current state

        Returns:
            Updated context with step results

        Raises:
            Any NewscastAuditError subclass for expected failures
            Exception for unexpected errors
        """
        pass

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<{self.__class__.__name__}: {self.name}>"
