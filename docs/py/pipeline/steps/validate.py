"""
Validation pipeline step.

Validates input data for:
- Required columns presence
- Non-empty DataFrame
- Basic data integrity

This is extracted from the validate_and_clean_data() function in processing.py.
"""

import sys
from pathlib import Path


from lib.cleaners import validate_input_data
from lib.exceptions import EmptyDataError, DataValidationError
from ..base import PipelineStep, PipelineContext


class ValidationStep(PipelineStep):
    """
    Validates input data structure and presence of required columns.

    Checks:
    - DataFrame is not empty
    - Required columns exist (newscast, date)
    - Basic data integrity

    Raises:
        EmptyDataError: If DataFrame has no rows
        DataValidationError: If required columns missing
    """

    @property
    def name(self) -> str:
        return "Input Validation"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Validate input data.

        Args:
            context: Pipeline context with data to validate

        Returns:
            Context with validation metadata

        Raises:
            EmptyDataError: If data is empty
            DataValidationError: If validation fails
        """
        df = context.data

        # Store initial row count for later tracking
        initial_row_count = len(df)
        context.set('initial_row_count', initial_row_count)

        # Validate using existing validation function
        # This raises EmptyDataError or DataValidationError on failure
        validate_input_data(df)

        # Validation passed
        context.set('validation_passed', True)

        return context
