"""
Export preparation pipeline step.

Prepares data for Excel and PowerPoint export:
- Normalized data (all rows)
- Summary tables
- Weekly trend data

Converts DataFrames to JSON-serializable dictionaries for download.

This is extracted from the export data section of process_json_data_with_errors()
in processing.py (lines ~350-361).
"""

from ..base import PipelineStep, PipelineContext


class ExportPreparationStep(PipelineStep):
    """
    Prepares data for Excel/PowerPoint export.

    Converts DataFrames to dictionaries for:
    - Normalized data (all cleaned rows)
    - Overall summary table
    - Recent week table
    - Volume by newscast table
    - Data quality table
    - Weekly trend data

    Updates context with export-ready data structures.
    """

    @property
    def name(self) -> str:
        return "Export Preparation"

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Prepare export data structures.

        Args:
            context: Pipeline context with tables and charts

        Returns:
            Context with export data ready for download
        """
        df = context.data
        tables = context.get('tables', {})
        charts = context.get('charts', {})

        # Extract table DataFrames
        overall_df = tables.get('overall')
        recent_df = tables.get('recent')
        volume_df = tables.get('volume')
        data_quality_df = tables.get('data_quality')

        # Extract weekly chart data
        weekly_chart = charts.get('weekly')

        # Convert to JSON-serializable dictionaries
        export_data = {
            "normalized": df.to_dict(orient='records'),
            "overall": overall_df.to_dict(orient='records') if overall_df is not None else [],
            "recent": recent_df.to_dict(orient='records') if recent_df is not None else [],
            "volume": volume_df.to_dict(orient='records') if volume_df is not None else [],
            "data_quality": data_quality_df.to_dict(orient='records') if data_quality_df is not None else [],
            "weekly": {
                "dates": weekly_chart["full_dates"] if weekly_chart else [],
                "values": weekly_chart["values"] if weekly_chart else []
            }
        }

        # Update context
        context.set('export_data', export_data)

        return context
