"""
Cleaning pipeline step.

Handles data cleaning and normalization:
- Column standardization
- Newscast name normalization
- Date parsing
- Response conversion (Yes/No → 1/0/NA)
- Empty row removal
- Quality issue tracking

This is extracted from the clean_data() and validate_and_clean_data()
functions in processing.py.
"""

import sys
from pathlib import Path


from lib.cleaners import clean_data
from lib.config_dynamic import get_config
from lib.exceptions import ProcessingError, InsufficientDataError
from ..base import PipelineStep, PipelineContext


class CleaningStep(PipelineStep):
    """
    Cleans and normalizes raw survey data.

    Performs:
    - Column renaming (Excel → internal names)
    - Newscast name normalization
    - Date parsing
    - Yes/No response conversion
    - Empty row removal
    - Quality issue tracking

    Updates context with:
    - cleaned DataFrame
    - metric_columns list
    - dropped_empty count
    - quality warnings
    """

    @property
    def name(self) -> str:
        return "Data Cleaning"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Clean and normalize data.

        Args:
            context: Pipeline context with raw data

        Returns:
            Context with cleaned data and metadata

        Raises:
            ProcessingError: If cleaning fails
            InsufficientDataError: If > 50% rows dropped
        """
        df_raw = context.data
        quality_tracker = context.quality_tracker
        initial_row_count = context.get('initial_row_count', len(df_raw))

        # Clean data using existing cleaning function
        try:
            df, metric_columns, dropped_empty = clean_data(df_raw.copy())
        except Exception as e:
            raise ProcessingError(
                message="Failed to clean data",
                operation="data_cleaning",
                original_error=e
            )

        # Check if too much data was dropped
        if dropped_empty > 0:
            drop_percentage = (dropped_empty / initial_row_count) * 100
            quality_tracker.add_warning(
                f"Dropped {dropped_empty} rows ({drop_percentage:.1f}%) with no metric data",
                count=dropped_empty
            )

            if drop_percentage > 50:
                raise InsufficientDataError(
                    initial_count=initial_row_count,
                    final_count=len(df),
                    dropped_count=dropped_empty
                )

        # Track unknown newscast formats
        if 'newscast_normalized' in df.columns and 'newscast' in df.columns:
            unknown_mask = (df['newscast'].notna()) & (
                ~df['newscast_normalized'].isin(get_config().NEWSCAST_ORDER)
            ) & (df['newscast_normalized'].notna())

            if unknown_mask.any():
                unknown_count = unknown_mask.sum()
                unknown_examples = df[unknown_mask]['newscast'].unique()[:5].tolist()
                quality_tracker.add_warning(
                    f"Found {unknown_count} responses with unrecognized newscast formats",
                    count=unknown_count,
                    examples=unknown_examples
                )

        # Track invalid dates
        if 'newscast_date' in df.columns and 'newscast_date_parsed' in df.columns:
            invalid_dates = df['newscast_date'].notna() & df['newscast_date_parsed'].isna()
            if invalid_dates.any():
                invalid_count = invalid_dates.sum()
                invalid_examples = df[invalid_dates]['newscast_date'].unique()[:5].tolist()
                quality_tracker.add_warning(
                    f"Found {invalid_count} responses with invalid dates",
                    count=invalid_count,
                    examples=[str(d) for d in invalid_examples]
                )

        # Track missing newscasts
        missing_newscast = df['newscast_normalized'].isna().sum() if 'newscast_normalized' in df.columns else 0
        if missing_newscast > 0:
            quality_tracker.add_info(
                f"{missing_newscast} responses have no newscast specified",
                {"count": missing_newscast}
            )

        # Update context
        context.data = df
        context.set('metric_columns', metric_columns)
        context.set('dropped_empty', dropped_empty)
        context.set('missing_newscast', missing_newscast)
        context.set('record_count', len(df))

        return context
