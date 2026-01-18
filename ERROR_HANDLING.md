# Error Handling Guide

This document describes the robust error handling system implemented in the newscast audit application.

## Overview

The application uses a multi-layered error handling approach:

1. **Custom Exception Hierarchy** - Python exceptions with structured error data
2. **Structured Error Responses** - JSON responses with error type, message, and guidance
3. **Data Quality Tracking** - Warnings for non-fatal issues
4. **Enhanced Error UI** - User-friendly error display with actionable guidance

## Exception Hierarchy

### Base Exception

**`NewscastAuditError`** - Base class for all application-specific errors

```python
class NewscastAuditError(Exception):
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details

    def to_dict(self) -> Dict:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "user_action": self.get_user_action()
        }
```

### Specific Exceptions

#### DataValidationError
Raised when input data fails validation.

**Examples:**
- Missing required columns
- Wrong file format
- Empty file

**User Action:** Provides specific guidance about which columns are missing and where to find the correct file.

```python
raise DataValidationError(
    message="Excel file is missing required columns.",
    missing_columns=['Which newscast are you auditing?'],
    found_columns=list(df.columns)
)
```

#### EmptyDataError
Raised when uploaded file contains no data.

**User Action:** Tells user to check they uploaded the correct file with survey responses.

#### InsufficientDataError
Raised when too many rows are dropped during cleaning (>50%).

**User Action:** Suggests reviewing source data to ensure completeness.

```python
raise InsufficientDataError(
    initial_count=100,
    final_count=20,
    dropped_count=80
)
```

#### DataQualityWarning
For non-fatal issues that don't prevent processing.

**Examples:**
- Unknown newscast formats
- Invalid dates that can be coerced
- Unexpected values in metric columns

**User Action:** Suggests data cleaning to improve accuracy.

```python
quality_tracker.add_warning(
    message="Found 5 responses with unrecognized newscast formats",
    count=5,
    examples=["xyz news", "test", "unknown"]
)
```

#### ProcessingError
Raised when unexpected errors occur during processing.

**User Action:** Suggests re-exporting data or contacting support.

```python
raise ProcessingError(
    message="Failed to clean data",
    operation="data_cleaning",
    original_error=e
)
```

#### ConfigurationError
Raised for configuration issues (missing env vars, invalid config).

**User Action:** Directs user to contact administrator.

## Usage in Python

### Basic Error Handling

```python
from lib.exceptions import DataValidationError, DataQualityWarning

def process_data(df):
    # Validate
    if df.empty:
        raise EmptyDataError(row_count=0)

    # Track quality issues
    quality_tracker = DataQualityTracker()

    # Add warnings for non-fatal issues
    quality_tracker.add_warning(
        "Found invalid dates",
        count=10,
        examples=["not-a-date", "2024-99-99"]
    )

    return result, quality_tracker
```

### Structured Error Responses

```python
try:
    result = process_json_data(json_str)
    return safe_json_dumps(result)

except NewscastAuditError as e:
    # Return structured error
    error_response = {
        "success": False,
        "error": e.to_dict()
    }
    return safe_json_dumps(error_response)

except Exception as e:
    # Handle unexpected errors
    error_response = {
        "success": False,
        "error": create_error_response(e)
    }
    return safe_json_dumps(error_response)
```

## Usage in JavaScript

### Enhanced Error Display

```javascript
// Initialize error UI
const errorUI = new ErrorUI();

try {
    const result = await processData();

    if (!result.success) {
        // Show structured error
        errorUI.showError(result);
    } else {
        // Show data quality warnings
        if (result.quality && result.quality.warnings.length > 0) {
            errorUI.showWarnings(result.quality);
        }
        renderResults(result);
    }

} catch (error) {
    // Show JavaScript error
    errorUI.showError(error.message);
}
```

### Error Response Format

```javascript
// Success with warnings
{
    "success": true,
    "summary": { ... },
    "tables": { ... },
    "charts": { ... },
    "quality": {
        "warnings": [
            {
                "level": "warning",
                "message": "Found 5 unknown newscast formats",
                "count": 5,
                "examples": ["xyz", "test"]
            }
        ],
        "info": [
            {
                "level": "info",
                "message": "10 responses have no newscast specified",
                "count": 10
            }
        ]
    }
}

// Error response
{
    "success": false,
    "error": {
        "error_type": "DataValidationError",
        "message": "Excel file is missing required columns.",
        "details": {
            "missing_columns": ["Which newscast are you auditing?"],
            "found_columns": ["col1", "col2", ...]
        },
        "user_action": "Ensure you're uploading the correct file..."
    }
}
```

## Data Quality Tracking

The `DataQualityTracker` class tracks non-fatal issues:

```python
class DataQualityTracker:
    def __init__(self):
        self.warnings = []
        self.info = []

    def add_warning(self, message, count=0, examples=None):
        """Add a data quality warning."""
        self.warnings.append({
            "level": "warning",
            "message": message,
            "count": count,
            "examples": (examples or [])[:5]
        })

    def add_info(self, message, details=None):
        """Add informational message."""
        self.info.append({
            "level": "info",
            "message": message,
            **details
        })
```

### Common Quality Issues Tracked

1. **Unknown newscast formats** - Formats that don't match patterns
2. **Invalid dates** - Dates that can't be parsed
3. **Missing newscasts** - Responses without newscast specified
4. **Dropped rows** - Rows with all metrics NA
5. **Failed calculations** - Optional metrics that fail to calculate

## User Experience

### Error UI Features

1. **Clear Error Type** - Shows specific error category
2. **User-Friendly Message** - Explains what went wrong
3. **Actionable Guidance** - Tells user exactly what to do
4. **Technical Details** - Expandable section for debugging
5. **Examples** - Shows specific problematic values
6. **Visual Hierarchy** - Icons, colors, and layout guide attention

### Error Display

```
┌─────────────────────────────────────────┐
│ ⚠ DataValidationError                   │
│                                         │
│ Excel file is missing required columns.│
│                                         │
│ What to do: Ensure you're uploading    │
│ the correct file. The file should      │
│ contain these columns: Which newscast  │
│ are you auditing?, Date of newscast:   │
│                                         │
│ [Show technical details ▼]             │
└─────────────────────────────────────────┘
```

### Warning Display

```
┌─────────────────────────────────────────┐
│ ⚠ Data Quality Warnings                 │
│                                         │
│ The data was processed successfully,   │
│ but some quality issues were detected: │
│                                         │
│ • Found 5 unknown newscast formats     │
│   [Show examples (5) ▼]                │
│                                         │
│ • Dropped 10 rows (5%) with no data    │
└─────────────────────────────────────────┘
```

## Best Practices

### When to Raise Errors

1. **Critical validation failures** - Missing columns, empty file
2. **Unrecoverable data issues** - >50% of data dropped
3. **Configuration problems** - Missing required config
4. **Unexpected exceptions** - Wrap and re-raise with context

### When to Use Warnings

1. **Recoverable data issues** - Invalid dates (can be NaT)
2. **Quality concerns** - Unknown formats, missing values
3. **Optional features failing** - Weekly trends can't be calculated
4. **Information** - Row counts, processing stats

### Error Message Guidelines

1. **Be specific** - "Missing column: X" not "Invalid data"
2. **Be actionable** - Tell user what to do, not just what's wrong
3. **Provide context** - Show examples of problematic data
4. **Use plain language** - Avoid jargon and technical terms
5. **Offer help** - Include link to docs or support contact

## Testing Error Handling

### Test Exception Raising

```python
def test_empty_data_raises_error():
    """Should raise EmptyDataError for empty DataFrame."""
    df = pd.DataFrame()
    with pytest.raises(EmptyDataError):
        validate_input_data(df)

def test_missing_columns_raises_error():
    """Should raise DataValidationError with column details."""
    df = pd.DataFrame({'wrong_column': [1, 2, 3]})
    with pytest.raises(DataValidationError) as exc_info:
        validate_input_data(df)

    error = exc_info.value
    assert 'Which newscast are you auditing?' in error.missing_columns
    assert error.found_columns == ['wrong_column']
```

### Test Error Responses

```python
def test_error_response_structure():
    """Should return structured error response."""
    result = process_json_data_with_errors('{}')
    data = json.loads(result)

    assert data['success'] == False
    assert 'error' in data
    assert 'error_type' in data['error']
    assert 'message' in data['error']
    assert 'user_action' in data['error']
```

### Test Quality Tracking

```python
def test_tracks_unknown_newscasts():
    """Should track unknown newscast formats as warnings."""
    df = pd.DataFrame({
        'newscast': ['xyz', '5-7am', 'unknown'],
        'metric1': [1, 1, 1]
    })

    quality_tracker = DataQualityTracker()
    # ... process data ...

    assert quality_tracker.has_warnings()
    assert any('unknown' in w['message'].lower()
               for w in quality_tracker.warnings)
```

## Integration Checklist

To enable enhanced error handling:

- [ ] Import error UI JavaScript in index.html
- [ ] Import error UI CSS in index.html
- [ ] Update processing.py to use processing_with_errors.py
- [ ] Update app.js to use errorUI.showError() and errorUI.showWarnings()
- [ ] Test error scenarios (empty file, missing columns, bad data)
- [ ] Test warning display (unknown formats, invalid dates)
- [ ] Verify mobile responsiveness of error UI
- [ ] Add error logging/monitoring if desired

## Future Enhancements

1. **Error Logging** - Send errors to monitoring service
2. **User Feedback** - Allow users to report issues directly
3. **Auto-Recovery** - Suggest fixes for common issues
4. **Context-Aware Help** - Link to specific docs based on error
5. **Error Analytics** - Track most common errors to improve UX
