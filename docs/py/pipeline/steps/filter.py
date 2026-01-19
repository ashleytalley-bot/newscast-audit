"""
Filtering pipeline step.

Filters the dataset based on runtime options (e.g., date range).
Preserves the original dataset in context.full_data for historical views.
"""

import pandas as pd
from typing import Optional

from ..base import PipelineStep, PipelineContext
from lib.datetime_utils import filter_by_date_range


class FilteringStep(PipelineStep):
    """
    Filters data based on context options.
    
    If date filters are present:
    1. Saves context.data to context.full_data
    2. Filters context.data by date range
    3. Updates context.data with filtered subset
    """

    @property
    def name(self) -> str:
        return "Data Filtering"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Apply filters to the dataset.
        
        Args:
            context: Pipeline context with cleaned data and options
            
        Returns:
            Context with potentially filtered data
        """
        start_date = context.options.get('filter_start_date')
        end_date = context.options.get('filter_end_date')

        # If no filters, do nothing (full_data remains None)
        if not start_date and not end_date:
            context.full_data = context.data
            return context

        df = context.data
        if df.empty or 'newscast_date_parsed' not in df.columns:
            context.full_data = df
            return context

        # Save full data before filtering
        # (We use copy to ensure full_data isn't modified by subsequent steps)
        context.full_data = df.copy()

        # Apply date filters using centralized datetime utilities
        # This ensures consistent inclusive end-date handling across the app
        # We validate dates manually first to provide proper warnings
        valid_start = True
        valid_end = True

        if start_date:
            try:
                from lib.datetime_utils import parse_date_safe
                parsed_start = parse_date_safe(start_date)
                if parsed_start is None:
                    context.quality_tracker.add_warning("Invalid start date filter ignored")
                    valid_start = False
            except (ValueError, TypeError):
                context.quality_tracker.add_warning("Invalid start date filter ignored")
                valid_start = False

        if end_date:
            try:
                from lib.datetime_utils import parse_date_safe
                parsed_end = parse_date_safe(end_date)
                if parsed_end is None:
                    context.quality_tracker.add_warning("Invalid end date filter ignored")
                    valid_end = False
            except (ValueError, TypeError):
                context.quality_tracker.add_warning("Invalid end date filter ignored")
                valid_end = False

        # Only apply filter if dates are valid
        if valid_start and valid_end:
            df = filter_by_date_range(
                df,
                date_column='newscast_date_parsed',
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None
            )

        # Update context with filtered dataframe
        context.data = df
        
        return context
