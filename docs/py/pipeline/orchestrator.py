"""
Processing pipeline orchestrator.

Composes pipeline steps and executes them in sequence to transform
raw survey data into analysis results.

This replaces the monolithic process_json_data_with_errors() function
from processing.py with a modular, testable pipeline.
"""

import sys
from pathlib import Path
import json
import pandas as pd
from typing import Dict, Any
from pydantic import ValidationError

from lib.config_dynamic import get_config
from lib.utils import safe_json_dumps
from lib.exceptions import NewscastAuditError, ProcessingError, create_error_response

# Import DataQualityTracker from lib
from lib.quality import DataQualityTracker

# Import schemas for validation
from lib.schemas.output import ProcessingResult
from lib.schemas.errors import ErrorResponse

from .base import PipelineStep, PipelineContext
from .steps import (
    ValidationStep,
    CleaningStep,
    AggregationStep,
    ChartGenerationStep,
    ExportPreparationStep,
)


class ProcessingPipeline:
    """
    Orchestrates the data processing pipeline.

    Executes steps in sequence:
    1. ValidationStep - Validate input structure
    2. CleaningStep - Clean and normalize data
    3. AggregationStep - Build summary tables
    4. ChartGenerationStep - Generate chart data
    5. ExportPreparationStep - Prepare export data

    Returns JSON response with results or structured errors.
    """

    def __init__(self):
        """Initialize the pipeline with all steps."""
        self.steps: list[PipelineStep] = [
            ValidationStep(),
            CleaningStep(),
            AggregationStep(),
            ChartGenerationStep(),
            ExportPreparationStep(),
        ]

    def execute(self, json_str: str) -> str:
        """
        Execute the full processing pipeline.

        Args:
            json_str: JSON string containing array of survey row objects

        Returns:
            JSON string with either:
            - Success response with data and quality warnings
            - Error response with detailed error information
        """
        quality_tracker = DataQualityTracker()

        try:
            # Parse JSON to DataFrame
            try:
                data = json.loads(json_str)
                df_raw = pd.DataFrame(data)
            except json.JSONDecodeError as e:
                raise ProcessingError(
                    message="Failed to parse JSON data",
                    operation="json_parsing",
                    original_error=e
                )
            except Exception as e:
                raise ProcessingError(
                    message="Failed to create DataFrame from data",
                    operation="dataframe_creation",
                    original_error=e
                )

            # Create pipeline context
            context = PipelineContext(df_raw, tracker=quality_tracker)

            # Execute each step in sequence
            for step in self.steps:
                try:
                    context = step.execute(context)
                except NewscastAuditError:
                    # Re-raise known errors
                    raise
                except Exception as e:
                    # Wrap unexpected errors with step context
                    raise ProcessingError(
                        message=f"Pipeline failed at step: {step.name}",
                        operation=step.name.lower().replace(' ', '_'),
                        original_error=e
                    )

            # Build success result from context
            result = self._build_result(context)

            return safe_json_dumps(result)

        except NewscastAuditError as e:
            # Handle known error types
            error_response = {
                "success": False,
                "error": e.to_dict()
            }
            # Validate error response against schema
            try:
                ErrorResponse.model_validate(error_response)
                # Validation passed, return original dict
                return safe_json_dumps(error_response)
            except ValidationError:
                # If error response doesn't match schema, return it anyway
                # (better to show a malformed error than fail silently)
                return safe_json_dumps(error_response)

        except Exception as e:
            # Handle unexpected errors
            error_response = {
                "success": False,
                "error": create_error_response(e)
            }
            # Validate error response against schema
            try:
                ErrorResponse.model_validate(error_response)
                # Validation passed, return original dict
                return safe_json_dumps(error_response)
            except ValidationError:
                # If error response doesn't match schema, return it anyway
                return safe_json_dumps(error_response)

    def _build_result(self, context: PipelineContext) -> Dict[str, Any]:
        """
        Build final result dictionary from pipeline context.

        Args:
            context: Completed pipeline context

        Returns:
            Result dictionary ready for JSON serialization

        Raises:
            ProcessingError: If result doesn't match expected schema
        """
        # Extract from context
        metric_columns = context.get('metric_columns', [])
        record_count = context.get('record_count', 0)
        dropped_empty = context.get('dropped_empty', 0)
        missing_newscast = context.get('missing_newscast', 0)

        tables = context.get('tables', {})
        charts = context.get('charts', {})
        export_data = context.get('export_data', {})

        # Extract table DataFrames
        overall_df = tables.get('overall')
        data_quality_df = tables.get('data_quality')
        recent_df = tables.get('recent')
        recent_week_start = tables.get('recent_week_start')
        volume_df = tables.get('volume')

        # Build result structure (matches original processing.py output)
        result = {
            "success": True,
            "summary": {
                "record_count": record_count,
                "metric_count": len(metric_columns),
                "missing_newscast": int(missing_newscast),
                "dropped_empty": int(dropped_empty)
            },
            "tables": {
                "overall": overall_df.to_dict(orient='records') if overall_df is not None else [],
                "data_quality": data_quality_df.to_dict(orient='records') if data_quality_df is not None else [],
                "recent": recent_df.to_dict(orient='records') if recent_df is not None else None,
                "recent_week_start": recent_week_start,
                "volume": volume_df.to_dict(orient='records') if volume_df is not None else None
            },
            "charts": charts,
            "export_data": export_data,
            "config": {
                "palette": get_config().PALETTE,
                "thresholds": get_config().THRESHOLDS,
                "metric_columns": metric_columns
            },
            "quality": context.quality_tracker.to_dict()
        }

        # Validate result against Pydantic schema
        try:
            ProcessingResult.model_validate(result)
            # Validation passed, return original dict
            return result
        except ValidationError as e:
            # Schema validation failed - this is a bug in the pipeline
            raise ProcessingError(
                message="Pipeline output validation failed",
                operation="schema_validation",
                original_error=e
            )
