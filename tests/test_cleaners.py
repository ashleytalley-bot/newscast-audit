"""
Unit tests for lib/cleaners.py

Tests data validation, newscast normalization, and response conversion.
"""

import pytest
import pandas as pd
import numpy as np
import warnings

from lib.cleaners import (
    validate_input_data,
    normalize_newscast,
    convert_to_numeric,
    standardize_columns,
    clean_data
)
from lib.exceptions import DataValidationError


class TestValidateInputData:
    """Tests for validate_input_data() function."""

    def test_valid_data_passes(self):
        """Should not raise error for valid data with required columns."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Date of newscast:': ['2024-01-01'],
            'Other Column': ['data']
        })
        # Should not raise
        validate_input_data(df)

    def test_missing_newscast_column_fails(self):
        """Should raise ValueError when newscast column is missing."""
        df = pd.DataFrame({
            'Date of newscast:': ['2024-01-01'],
            'Other Column': ['data']
        })
        with pytest.raises(DataValidationError, match="missing required columns"):
            validate_input_data(df)

    def test_missing_date_column_fails(self):
        """Should raise ValueError when date column is missing."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Other Column': ['data']
        })
        with pytest.raises(DataValidationError, match="missing required columns"):
            validate_input_data(df)

    def test_error_message_helpful(self):
        """Should provide helpful error message with missing columns."""
        df = pd.DataFrame({'Other Column': ['data']})
        with pytest.raises(DataValidationError, match="Excel file is missing required columns."):
            validate_input_data(df)


class TestNormalizeNewscast:
    """Tests for normalize_newscast() function."""

    # Morning time ranges
    def test_5_7am_variations(self):
        """Should normalize all variations of 5-7am."""
        variations = [
            '5-7am', '5 - 7 am', '5-7 am', '5a-7a', '5 a - 7 a',
            '5:7am', '5 : 7 am', '5–7am'  # en dash
        ]
        for var in variations:
            assert normalize_newscast(var) == '5 - 7 am', f"Failed for: {var}"

    def test_7_9am_variations(self):
        """Should normalize all variations of 7-9am."""
        variations = [
            '7-9am', '7 - 9 am', '7-9 am', '7a-9a', '7 a - 9 a',
            '7:9am', '7 : 9 am', '7–9am'
        ]
        for var in variations:
            assert normalize_newscast(var) == '7 - 9 am', f"Failed for: {var}"

    def test_single_5am_maps_to_range(self):
        """Should map standalone 5am to 5-7am range."""
        variations = ['5am', '5 am', '5 a.m.', '5a.m.', '5 AM']
        for var in variations:
            assert normalize_newscast(var) == '5 - 7 am', f"Failed for: {var}"

    def test_single_7am_maps_to_range(self):
        """Should map standalone 7am to 7-9am range."""
        variations = ['7am', '7 am', '7 a.m.', '7a.m.', '7 AM']
        for var in variations:
            assert normalize_newscast(var) == '7 - 9 am', f"Failed for: {var}"

    # PM shows
    def test_11pm_variations(self):
        """Should normalize all variations of 11pm."""
        variations = ['11pm', '11 pm', '11 p.m.', '11p.m.', '11 PM', '11']
        for var in variations:
            assert normalize_newscast(var) == '11 pm', f"Failed for: {var}"

    def test_6pm_variations(self):
        """Should normalize all variations of 6pm."""
        variations = ['6pm', '6 pm', '6 p.m.', '6p.m.', '6 PM']
        for var in variations:
            assert normalize_newscast(var) == '6 pm', f"Failed for: {var}"

    def test_5pm_variations(self):
        """Should normalize all variations of 5pm."""
        variations = ['5pm', '5 pm', '5 p.m.', '5p.m.', '5 PM']
        for var in variations:
            assert normalize_newscast(var) == '5 pm', f"Failed for: {var}"

    # Noon
    def test_noon_variations(self):
        """Should normalize all variations of noon to 12 pm."""
        variations = ['noon', 'Noon', 'NOON', '12pm', '12 pm', '12 p.m.',
                      '12', 'midday', 'Midday']
        for var in variations:
            assert normalize_newscast(var) == '12 pm', f"Failed for: {var}"

    # Evening Plus
    def test_evening_plus_variations(self):
        """Should normalize all variations of Evening Plus."""
        variations = ['evening+', 'Evening+', 'e+', 'E+', 'E +',
                      'evening plus', 'Evening Plus']
        for var in variations:
            assert normalize_newscast(var) == 'E +', f"Failed for: {var}"

    # Ambiguous inputs (should return None)
    def test_ambiguous_am_alone(self):
        """Should return None for standalone 'am' (ambiguous)."""
        variations = ['am', 'AM', 'a.m.', 'A.M.']
        for var in variations:
            assert normalize_newscast(var) is None, f"Should reject: {var}"

    def test_ambiguous_pm_alone(self):
        """Should return None for standalone 'pm' (ambiguous)."""
        variations = ['pm', 'PM', 'p.m.', 'P.M.']
        for var in variations:
            assert normalize_newscast(var) is None, f"Should reject: {var}"

    def test_ambiguous_generic_words(self):
        """Should return None for generic time words."""
        variations = ['morning', 'afternoon', 'evening']
        for var in variations:
            assert normalize_newscast(var) is None, f"Should reject: {var}"

    # Edge cases
    def test_none_input(self):
        """Should return None for pd.NA input."""
        assert normalize_newscast(pd.NA) is None
        assert normalize_newscast(None) is None

    def test_empty_string(self):
        """Should handle empty string."""
        result = normalize_newscast('')
        assert result == '' or result is None

    def test_whitespace_handling(self):
        """Should handle extra whitespace correctly."""
        assert normalize_newscast('  5 - 7  am  ') == '5 - 7 am'
        assert normalize_newscast('5    -    7    am') == '5 - 7 am'

    def test_case_insensitivity(self):
        """Should be case insensitive."""
        assert normalize_newscast('5-7AM') == '5 - 7 am'
        assert normalize_newscast('6PM') == '6 pm'
        assert normalize_newscast('NOON') == '12 pm'

    def test_unknown_format_returns_original(self):
        """Should return original value for unknown formats."""
        unknown = 'Some Random Show Name'
        assert normalize_newscast(unknown) == unknown

    def test_warnings_disabled_by_default(self):
        """Should not emit warnings by default."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            normalize_newscast("unknown format")
            assert len(w) == 0

    def test_warnings_enabled(self):
        """Should emit warnings when warn_on_unknown=True."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            normalize_newscast("unknown format", warn_on_unknown=True)
            assert len(w) == 1
            assert "Unknown newscast format" in str(w[0].message)

    def test_ambiguous_warning(self):
        """Should warn about ambiguous inputs when enabled."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            normalize_newscast("am", warn_on_unknown=True)
            assert len(w) == 1
            assert "Ambiguous" in str(w[0].message)


class TestConvertToNumeric:
    """Tests for convert_to_numeric() function."""

    def test_yes_variations(self):
        """Should convert all 'yes' variations to 1."""
        variations = ['yes', 'Yes', 'YES', 'y', 'Y', 'true', 'True', 'TRUE', '1']
        for var in variations:
            assert convert_to_numeric(var) == 1, f"Failed for: {var}"

    def test_no_variations(self):
        """Should convert all 'no' variations to 0."""
        variations = ['no', 'No', 'NO', 'n', 'N', 'false', 'False', 'FALSE', '0']
        for var in variations:
            assert convert_to_numeric(var) == 0, f"Failed for: {var}"

    def test_na_variations(self):
        """Should convert all N/A variations to pd.NA."""
        variations = ['n/a', 'N/A', 'na', 'NA', 'none', 'None', 'NONE', '']
        for var in variations:
            result = convert_to_numeric(var)
            assert pd.isna(result), f"Failed for: {var}"

    def test_numeric_values(self):
        """Should handle numeric inputs."""
        assert convert_to_numeric(1) == 1
        assert convert_to_numeric(0) == 0
        assert convert_to_numeric(1.0) == 1
        assert convert_to_numeric(0.0) == 0

    def test_pd_na_input(self):
        """Should return pd.NA for pd.NA input."""
        result = convert_to_numeric(pd.NA)
        assert pd.isna(result)

    def test_none_input(self):
        """Should return pd.NA for None input."""
        result = convert_to_numeric(None)
        assert pd.isna(result)

    def test_whitespace_handling(self):
        """Should handle whitespace correctly."""
        assert convert_to_numeric('  yes  ') == 1
        assert convert_to_numeric('  no  ') == 0

    def test_unknown_string_returns_na(self):
        """Should return pd.NA for unknown strings."""
        result = convert_to_numeric('maybe')
        assert pd.isna(result)

    def test_numeric_other_than_0_1_returns_na(self):
        """Should return pd.NA for numbers other than 0 or 1."""
        result = convert_to_numeric(0.5)
        assert pd.isna(result)
        result = convert_to_numeric(2)
        assert pd.isna(result)


class TestStandardizeColumns:
    """Tests for standardize_columns() function."""

    def test_renames_known_columns(self):
        """Should rename columns according to COLUMN_MAPPING."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Date of newscast:': ['2024-01-01'],
            'Other Column': ['data']
        })
        result = standardize_columns(df)
        assert 'newscast' in result.columns
        assert 'newscast_date' in result.columns
        assert 'Other Column' in result.columns  # Unknown columns preserved

    def test_preserves_unknown_columns(self):
        """Should preserve columns not in COLUMN_MAPPING."""
        df = pd.DataFrame({
            'Custom Column': ['value'],
            'Another Column': ['value2']
        })
        result = standardize_columns(df)
        assert 'Custom Column' in result.columns
        assert 'Another Column' in result.columns

    def test_handles_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame()
        result = standardize_columns(df)
        assert len(result.columns) == 0


class TestCleanData:
    """Tests for clean_data() function."""

    def test_complete_cleaning_pipeline(self):
        """Should execute complete cleaning pipeline."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am', 'noon', '11pm', '6pm'],
            'Date of newscast:': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes', 'No', 'N/A', 'Yes']
        })

        cleaned_df, metrics, dropped = clean_data(df)

        # Check standardized columns
        assert 'newscast_normalized' in cleaned_df.columns
        assert 'newscast_date_parsed' in cleaned_df.columns

        # Check normalized newscasts (row with all NA will be dropped, so indices shift)
        assert cleaned_df['newscast_normalized'].iloc[0] == '5 - 7 am'
        assert cleaned_df['newscast_normalized'].iloc[1] == '12 pm'
        assert cleaned_df['newscast_normalized'].iloc[2] == '6 pm'  # 11pm row was dropped (N/A)

        # Check numeric conversion
        assert 'urgency_and_why_now' in metrics
        assert cleaned_df['urgency_and_why_now'].iloc[0] == 1
        assert cleaned_df['urgency_and_why_now'].iloc[1] == 0
        assert cleaned_df['urgency_and_why_now'].iloc[2] == 1  # 6pm row

        # Check that 1 row was dropped (the N/A row)
        assert dropped == 1

    def test_drops_empty_rows(self):
        """Should drop rows where all metrics are NA."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am', 'noon'],
            'Date of newscast:': ['2024-01-01', '2024-01-02'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes', pd.NA]
        })

        cleaned_df, metrics, dropped = clean_data(df)

        assert len(cleaned_df) == 1  # Second row should be dropped
        assert dropped == 1

    def test_handles_missing_newscast_column(self):
        """Should handle missing newscast column gracefully."""
        df = pd.DataFrame({
            'Date of newscast:': ['2024-01-01'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes']
        })

        cleaned_df, metrics, dropped = clean_data(df)

        # Should still process, just with None newscast_normalized
        assert cleaned_df['newscast_normalized'].iloc[0] is None

    def test_handles_missing_date_column(self):
        """Should handle missing date column gracefully."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes']
        })

        cleaned_df, metrics, dropped = clean_data(df)

        # Should still process, with NaT for dates
        assert pd.isna(cleaned_df['newscast_date_parsed'].iloc[0])

    def test_parses_dates_correctly(self):
        """Should parse valid dates."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Date of newscast:': ['2024-01-15'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes']
        })

        cleaned_df, metrics, dropped = clean_data(df)

        assert cleaned_df['newscast_date_parsed'].iloc[0] == pd.Timestamp('2024-01-15')

    def test_handles_invalid_dates(self):
        """Should handle invalid dates gracefully (convert to NaT)."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Date of newscast:': ['not a date'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes']
        })

        cleaned_df, metrics, dropped = clean_data(df)

        assert pd.isna(cleaned_df['newscast_date_parsed'].iloc[0])

    def test_returns_present_metrics(self):
        """Should return list of metric columns actually present in data."""
        df = pd.DataFrame({
            'Which newscast are you auditing?': ['5-7am'],
            'Date of newscast:': ['2024-01-01'],
            'Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ': ['Yes'],
            'Is a tease to streaming in at least every 30 minutes with specific content push for each show?': ['No']
        })

        cleaned_df, metrics, dropped = clean_data(df)

        assert 'urgency_and_why_now' in metrics
        assert 'specific_streaming_tease' in metrics
        assert len(metrics) == 2
