# Newscast Audit Tests

Comprehensive unit tests for the newscast audit library.

## Running Tests

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

Run all tests:
```bash
python3 -m pytest tests/ -v
```

Run specific test file:
```bash
python3 -m pytest tests/test_cleaners.py -v
```

Run with coverage:
```bash
python3 -m pytest tests/ --cov=lib --cov-report=html
```

## Test Structure

- **test_cleaners.py** - Tests for data validation, normalization, and cleaning functions
- **test_builders.py** - Tests for metric calculation and table/chart building functions

## Test Coverage

Current coverage: **63 tests**, all passing ✅

### test_cleaners.py

- `TestValidateInputData` (4 tests) - Input validation
- `TestNormalizeNewscast` (17 tests) - Newscast name normalization
  - Morning time ranges (5-7am, 7-9am)
  - PM shows (5pm, 6pm, 11pm)
  - Noon variations
  - Evening Plus
  - Ambiguous inputs (rejected)
  - Edge cases and warnings
- `TestConvertToNumeric` (9 tests) - Yes/No response conversion
- `TestStandardizeColumns` (3 tests) - Column renaming
- `TestCleanData` (7 tests) - Complete cleaning pipeline

### test_builders.py

- `TestBuildYesPercentTable` (6 tests) - Yes percentage calculation
- `TestBuildDataQualityTable` (5 tests) - Data quality metrics
- `TestWeeklyPercentSeries` (9 tests) - Weekly trend calculations

## Writing New Tests

Follow the existing pattern:

```python
class TestYourFunction:
    """Tests for your_function()."""

    def test_basic_case(self):
        """Should handle basic case correctly."""
        result = your_function(input_data)
        assert result == expected_output

    def test_edge_case(self):
        """Should handle edge case gracefully."""
        result = your_function(edge_case_input)
        assert result is not None
```

## Key Testing Patterns

1. **Test one behavior per test** - Each test should verify a single aspect
2. **Use descriptive names** - Test name should explain what it tests
3. **Include docstrings** - Explain what the test validates
4. **Test edge cases** - Empty data, None, NA values, invalid inputs
5. **Test error cases** - Verify errors are raised appropriately

## Continuous Improvement

When adding new features:
1. Write tests first (TDD approach)
2. Run tests to see them fail
3. Implement the feature
4. Run tests to see them pass
5. Refactor with confidence

When fixing bugs:
1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify the test now passes
4. The test prevents regression
