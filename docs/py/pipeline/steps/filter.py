"""
Filtering pipeline step.

Filters the dataset based on runtime options (e.g., date range).
Preserves the original dataset in context.full_data for historical views.
"""

import pandas as pd
from typing import Optional

from ..base import PipelineStep, PipelineContext


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

        # Apply start date filter
        if start_date:
            try:
                ts_start = pd.to_datetime(start_date)
                df = df[df['newscast_date_parsed'] >= ts_start]
            except (ValueError, TypeError):
                context.quality_tracker.add_warning("Invalid start date filter ignored")

        # Apply end date filter
        if end_date:
            try:
                ts_end = pd.to_datetime(end_date)
                # Include the entire end date by checking if dates are strictly before the next day
                df = df[df['newscast_date_parsed'] < (ts_end + pd.Timedelta(days=1))]
            except (ValueError, TypeError):
                context.quality_tracker.add_warning("Invalid end date filter ignored")

        # Update context with filtered dataframe
        context.data = df
        
        return context
