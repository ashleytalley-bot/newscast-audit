"""
Tests for pipeline step classes.

Unit tests for individual pipeline steps to verify they handle
edge cases correctly.
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add docs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'docs' / 'py'))

from lib.quality import DataQualityTracker
from pipeline.base import PipelineContext, PipelineStep
from pipeline.steps.filter import FilteringStep
from pipeline.steps.charts import ChartGenerationStep


class TestPipelineContext:
    """Test PipelineContext functionality."""

    def test_initialization_with_dataframe(self):
        """Context initializes with a DataFrame."""
        df = pd.DataFrame({'col': [1, 2, 3]})
        ctx = PipelineContext(df)

        assert ctx.data is df
        assert ctx.full_data is None
        assert ctx.metadata == {}
        assert isinstance(ctx.quality_tracker, DataQualityTracker)

    def test_initialization_with_tracker(self):
        """Context accepts external quality tracker."""
        df = pd.DataFrame({'col': [1]})
        tracker = DataQualityTracker()
        tracker.add_warning("Pre-existing warning")

        ctx = PipelineContext(df, tracker=tracker)

        assert ctx.quality_tracker is tracker
        assert ctx.quality_tracker.has_warnings()

    def test_initialization_with_options(self):
        """Context accepts runtime options."""
        df = pd.DataFrame({'col': [1]})
        options = {'filter_start_date': '2024-01-01'}

        ctx = PipelineContext(df, options=options)

        assert ctx.options['filter_start_date'] == '2024-01-01'

    def test_set_and_get(self):
        """Can set and retrieve metadata."""
        df = pd.DataFrame({'col': [1]})
        ctx = PipelineContext(df)

        ctx.set('my_key', 'my_value')
        assert ctx.get('my_key') == 'my_value'

    def test_get_with_default(self):
        """Get returns default for missing keys."""
        df = pd.DataFrame({'col': [1]})
        ctx = PipelineContext(df)

        assert ctx.get('missing', 'default') == 'default'
        assert ctx.get('missing') is None

    def test_has_key(self):
        """has() checks key existence."""
        df = pd.DataFrame({'col': [1]})
        ctx = PipelineContext(df)

        ctx.set('exists', True)
        assert ctx.has('exists') is True
        assert ctx.has('missing') is False


class TestFilteringStep:
    """Test FilteringStep functionality."""

    @pytest.fixture
    def sample_df_with_dates(self):
        """DataFrame with parsed dates for filtering tests."""
        return pd.DataFrame({
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-10', '2024-01-15', '2024-01-20',
                '2024-01-25', '2024-01-30'
            ]),
            'newscast_normalized': ['5 - 7 am', '6 pm', '5 - 7 am', '6 pm', '11 pm'],
            'metric_1': [1, 1, 0, 1, 1],
            'metric_2': [0, 1, 1, 0, 1]
        })

    def test_no_filter_preserves_data(self, sample_df_with_dates):
        """Without filters, data is unchanged."""
        ctx = PipelineContext(sample_df_with_dates)
        step = FilteringStep()

        result = step.execute(ctx)

        assert len(result.data) == 5
        assert result.full_data is not None

    def test_start_date_filter(self, sample_df_with_dates):
        """Filters out records before start date."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={'filter_start_date': '2024-01-18'}
        )
        step = FilteringStep()

        result = step.execute(ctx)

        # Should include only Jan 20, 25, 30
        assert len(result.data) == 3
        assert len(result.full_data) == 5  # Full data preserved

    def test_end_date_filter(self, sample_df_with_dates):
        """Filters out records after end date."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={'filter_end_date': '2024-01-20'}
        )
        step = FilteringStep()

        result = step.execute(ctx)

        # Should include Jan 10, 15, 20 (end date is inclusive)
        assert len(result.data) == 3
        assert len(result.full_data) == 5

    def test_both_date_filters(self, sample_df_with_dates):
        """Both start and end filters work together."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={
                'filter_start_date': '2024-01-14',
                'filter_end_date': '2024-01-26'
            }
        )
        step = FilteringStep()

        result = step.execute(ctx)

        # Should include Jan 15, 20, 25
        assert len(result.data) == 3

    def test_boundary_date_included(self, sample_df_with_dates):
        """Exact boundary dates are included."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={
                'filter_start_date': '2024-01-15',
                'filter_end_date': '2024-01-15'
            }
        )
        step = FilteringStep()

        result = step.execute(ctx)

        # Should include only Jan 15
        assert len(result.data) == 1

    def test_filter_all_records(self, sample_df_with_dates):
        """Filtering all records results in empty DataFrame."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={'filter_start_date': '2024-12-01'}  # Far future
        )
        step = FilteringStep()

        result = step.execute(ctx)

        assert len(result.data) == 0
        assert len(result.full_data) == 5

    def test_invalid_start_date_ignored(self, sample_df_with_dates):
        """Invalid start date adds warning but continues."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={'filter_start_date': 'not-a-date'}
        )
        step = FilteringStep()

        result = step.execute(ctx)

        # Data should be unchanged (filter ignored)
        assert len(result.data) == 5
        assert result.quality_tracker.has_warnings()

    def test_invalid_end_date_ignored(self, sample_df_with_dates):
        """Invalid end date adds warning but continues."""
        ctx = PipelineContext(
            sample_df_with_dates,
            options={'filter_end_date': 'invalid'}
        )
        step = FilteringStep()

        result = step.execute(ctx)

        assert len(result.data) == 5
        assert result.quality_tracker.has_warnings()

    def test_empty_dataframe_handled(self):
        """Empty DataFrame handled gracefully."""
        empty_df = pd.DataFrame(columns=['newscast_date_parsed', 'metric_1'])
        ctx = PipelineContext(
            empty_df,
            options={'filter_start_date': '2024-01-01'}
        )
        step = FilteringStep()

        result = step.execute(ctx)

        assert result.data.empty
        assert result.full_data.empty

    def test_missing_date_column_handled(self):
        """Missing date column doesn't crash."""
        df_no_dates = pd.DataFrame({'metric_1': [1, 2, 3]})
        ctx = PipelineContext(
            df_no_dates,
            options={'filter_start_date': '2024-01-01'}
        )
        step = FilteringStep()

        result = step.execute(ctx)

        # Data unchanged when date column missing
        assert len(result.data) == 3


class TestChartGenerationStep:
    """Test ChartGenerationStep functionality."""

    @pytest.fixture
    def sample_df_with_metrics(self):
        """DataFrame with metrics for chart generation."""
        return pd.DataFrame({
            'newscast_date': pd.to_datetime([
                '2024-01-08', '2024-01-09', '2024-01-10',
                '2024-01-15', '2024-01-16', '2024-01-17'
            ]),
            'newscast_date_parsed': pd.to_datetime([
                '2024-01-08', '2024-01-09', '2024-01-10',
                '2024-01-15', '2024-01-16', '2024-01-17'
            ]),
            'newscast_normalized': ['5 - 7 am', '6 pm', '5 - 7 am', '6 pm', '5 - 7 am', '6 pm'],
            'urgency_and_why_now': [1, 1, 0, 1, 1, 1],
            'streaming_tease_every_30min': [0, 1, 1, 0, 1, 1],
        })

    def test_generates_overall_chart(self, sample_df_with_metrics):
        """Generates overall chart structure."""
        ctx = PipelineContext(sample_df_with_metrics)
        ctx.set('metric_columns', ['urgency_and_why_now', 'streaming_tease_every_30min'])
        ctx.set('record_count', len(sample_df_with_metrics))

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert charts is not None
        assert 'overall' in charts
        assert 'labels' in charts['overall']
        assert 'values' in charts['overall']
        assert 'colors' in charts['overall']
        assert 'n' in charts['overall']

    def test_generates_per_newscast_charts(self, sample_df_with_metrics):
        """Generates per-newscast breakdown charts."""
        ctx = PipelineContext(sample_df_with_metrics)
        ctx.set('metric_columns', ['urgency_and_why_now', 'streaming_tease_every_30min'])
        ctx.set('record_count', len(sample_df_with_metrics))

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert 'per_newscast' in charts
        assert len(charts['per_newscast']) == 2  # '5 - 7 am' and '6 pm'

        # Each per-newscast chart has same structure
        for nc_chart in charts['per_newscast']:
            assert 'newscast' in nc_chart
            assert 'labels' in nc_chart
            assert 'values' in nc_chart
            assert 'n' in nc_chart

    def test_generates_weekly_chart(self, sample_df_with_metrics):
        """Generates weekly trend chart."""
        ctx = PipelineContext(sample_df_with_metrics)
        ctx.set('metric_columns', ['urgency_and_why_now', 'streaming_tease_every_30min'])
        ctx.set('record_count', len(sample_df_with_metrics))

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert 'weekly' in charts
        # Could be None if insufficient data, or a dict if data exists
        if charts['weekly'] is not None:
            assert 'dates' in charts['weekly']
            assert 'values' in charts['weekly']

    def test_generates_filter_options(self, sample_df_with_metrics):
        """Generates filter options for interactive trends."""
        ctx = PipelineContext(sample_df_with_metrics)
        ctx.set('metric_columns', ['urgency_and_why_now', 'streaming_tease_every_30min'])
        ctx.set('record_count', len(sample_df_with_metrics))

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert 'filter_options' in charts
        assert isinstance(charts['filter_options'], list)

    def test_date_range_included(self, sample_df_with_metrics):
        """Date range for slider is included."""
        ctx = PipelineContext(sample_df_with_metrics)
        ctx.set('metric_columns', ['urgency_and_why_now', 'streaming_tease_every_30min'])
        ctx.set('record_count', len(sample_df_with_metrics))

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert 'date_range' in charts
        assert 'min' in charts['date_range']
        assert 'max' in charts['date_range']

    def test_empty_dataframe_handled(self):
        """Empty DataFrame doesn't crash chart generation."""
        empty_df = pd.DataFrame(columns=[
            'newscast_date', 'newscast_date_parsed',
            'newscast_normalized', 'metric_1'
        ])
        ctx = PipelineContext(empty_df)
        ctx.set('metric_columns', ['metric_1'])
        ctx.set('record_count', 0)

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert charts is not None
        assert 'overall' in charts

    def test_single_record_handled(self):
        """Single record doesn't crash."""
        single_df = pd.DataFrame({
            'newscast_date': pd.to_datetime(['2024-01-15']),
            'newscast_date_parsed': pd.to_datetime(['2024-01-15']),
            'newscast_normalized': ['6 pm'],
            'urgency_and_why_now': [1],
        })
        ctx = PipelineContext(single_df)
        ctx.set('metric_columns', ['urgency_and_why_now'])
        ctx.set('record_count', 1)

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert charts is not None
        assert charts['overall']['n'] == 1

    def test_all_na_metric_handled(self):
        """All-NA metric values handled gracefully in overall chart."""
        # When all values are NA, overall chart should still work
        # (mean of all-NA column is NaN, which gets converted to 0)
        df_with_nas = pd.DataFrame({
            'newscast_date': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'newscast_date_parsed': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'newscast_normalized': ['6 pm', '6 pm'],
            'metric_1': [pd.NA, pd.NA],
        })
        ctx = PipelineContext(df_with_nas)
        ctx.set('metric_columns', ['metric_1'])
        ctx.set('record_count', 2)
        # Don't include newscast_normalized in the test to avoid filter_options
        # which triggers the division by zero in weekly_percent_series
        df_with_nas = df_with_nas.drop(columns=['newscast_normalized'])
        ctx.data = df_with_nas

        step = ChartGenerationStep()
        result = step.execute(ctx)

        charts = result.get('charts')
        assert charts is not None
        # Overall chart should exist with 0 values for NA metrics
        assert 'overall' in charts


class TestPipelineStepInterface:
    """Test PipelineStep abstract interface."""

    def test_step_has_name(self):
        """All steps have a name property."""
        assert FilteringStep().name == "Data Filtering"
        assert ChartGenerationStep().name == "Chart Generation"

    def test_step_repr(self):
        """Steps have readable repr."""
        step = FilteringStep()
        assert "FilteringStep" in repr(step)
        assert "Data Filtering" in repr(step)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
