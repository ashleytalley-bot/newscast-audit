# Error Handling Improvements - Implementation Recommendations

This document provides actionable recommendations for making error handling more robust and user-friendly.

## What Was Created

### 1. Custom Exception Hierarchy (`lib/exceptions.py`)

A complete set of structured exceptions:

- **`NewscastAuditError`** - Base exception with `.to_dict()` for JSON serialization
- **`DataValidationError`** - Missing columns, wrong format
- **`EmptyDataError`** - No data in file
- **`InsufficientDataError`** - Too many rows dropped
- **`DataQualityWarning`** - Non-fatal issues
- **`ProcessingError`** - Unexpected processing failures
- **`ConfigurationError`** - Setup/config issues

**Key feature:** Each exception includes `user_action` field with specific guidance.

### 2. Enhanced Processing Module (`docs/py/processing_with_errors.py`)

- **`DataQualityTracker`** class to track warnings
- **`validate_and_clean_data()`** with quality tracking
- **`process_json_data_with_errors()`** with comprehensive error handling
- Returns structured responses with `success`, `error`, and `quality` fields

### 3. Error UI Components (`docs/js/error-ui.js`)

- **`ErrorUI`** class for rich error display
- Shows structured errors with expandable details
- Displays data quality warnings separately
- User-friendly messages with actionable guidance
- XSS-safe HTML rendering

### 4. Error UI Styles (`docs/css/error-ui.css`)

- Beautiful error cards with icons
- Warning cards with collapsible examples
- Dark mode support
- Mobile responsive design

### 5. Comprehensive Documentation (`ERROR_HANDLING.md`)

- Complete guide to exception hierarchy
- Usage examples for Python and JavaScript
- Error response format specifications
- Best practices and testing guidelines

## Implementation Roadmap

### Phase 1: Backend Integration (High Priority)

**What:** Replace basic `ValueError` with structured exceptions

**How:**
1. Update `lib/cleaners.py` to use custom exceptions (partially done)
2. Update `docs/py/processing.py` to import from `processing_with_errors.py`
3. Test with various error scenarios

**Files to modify:**
```python
# docs/py/processing.py
# Change this line:
from lib import clean_data, validate_input_data
# To import enhanced versions:
from processing_with_errors import process_json_data

# Or simply rename processing_with_errors.py to processing.py
```

**Benefits:**
- Detailed error messages
- Structured error responses
- Data quality tracking

### Phase 2: Frontend Integration (High Priority)

**What:** Use enhanced error UI instead of basic error messages

**How:**
1. Add error-ui.js and error-ui.css to index.html
2. Update app.js to use `errorUI.showError()` and `errorUI.showWarnings()`
3. Handle both success responses with warnings and error responses

**Files to modify:**

```html
<!-- docs/index.html -->
<head>
    <!-- Existing styles -->
    <link rel="stylesheet" href="css/style.css">
    <!-- Add error UI styles -->
    <link rel="stylesheet" href="css/error-ui.css">
</head>
<body>
    <!-- Existing content -->

    <!-- Add before app.js -->
    <script src="js/error-ui.js"></script>
    <script src="js/app.js"></script>
</body>
```

```javascript
// docs/js/app.js - Update error handling
async processFile(file) {
    try {
        // ... existing code ...

        const result = JSON.parse(resultJson);

        if (!result.success) {
            // Show structured error
            errorUI.showError(result);
            return;
        }

        // Show data quality warnings
        if (result.quality && result.quality.warnings.length > 0) {
            errorUI.showWarnings(result.quality);
        }

        this.processedData = result;
        this.renderResults();
        this.showResults();

    } catch (error) {
        errorUI.showError(error);
    }
}
```

**Benefits:**
- User-friendly error messages
- Actionable guidance
- Visual distinction between errors and warnings

### Phase 3: Testing (Medium Priority)

**What:** Add tests for error handling

**How:**
1. Create `tests/test_exceptions.py`
2. Test each exception type
3. Test error response formatting
4. Test quality tracker

**Example tests:**

```python
# tests/test_exceptions.py
def test_data_validation_error():
    """Should create structured error response."""
    error = DataValidationError(
        message="Missing columns",
        missing_columns=['col1', 'col2']
    )

    response = error.to_dict()
    assert response['error_type'] == 'DataValidationError'
    assert 'col1' in response['details']['missing_columns']
    assert 'user_action' in response

def test_quality_tracker():
    """Should track warnings and info."""
    tracker = DataQualityTracker()
    tracker.add_warning("Test warning", count=5)
    tracker.add_info("Test info")

    assert tracker.has_warnings()
    data = tracker.to_dict()
    assert len(data['warnings']) == 1
    assert len(data['info']) == 1
```

**Benefits:**
- Prevent regressions
- Document expected behavior
- Verify error messages are helpful

### Phase 4: Error Logging (Optional, Low Priority)

**What:** Track errors for monitoring and improvement

**How:**
1. Add logging to `process_json_data_with_errors()`
2. Log errors to console or external service
3. Track error frequency and types

**Example:**

```python
import logging

logger = logging.getLogger(__name__)

def process_json_data_with_errors(json_str: str) -> str:
    try:
        # ... processing ...
        return success_response

    except NewscastAuditError as e:
        # Log structured error
        logger.error(
            "Processing failed",
            extra={
                "error_type": e.__class__.__name__,
                "message": e.message,
                "details": e.details
            }
        )
        return error_response
```

**Benefits:**
- Identify common errors
- Improve documentation based on real issues
- Monitor application health

## Quick Wins (Can Implement Immediately)

### 1. Add Error UI to HTML (5 minutes)

```html
<!-- Add to docs/index.html -->
<link rel="stylesheet" href="css/error-ui.css">
<script src="js/error-ui.js"></script>
```

### 2. Use Enhanced Error Display (10 minutes)

```javascript
// Replace in docs/js/app.js
// Old:
showError(message) {
    this.dom.errorMessage.textContent = message;
    this.dom.errorMessage.classList.remove('hidden');
}

// New:
showError(error) {
    errorUI.showError(error);
}
```

### 3. Switch to Enhanced Processing (2 minutes)

```bash
# Rename files
mv docs/py/processing.py docs/py/processing_basic.py
mv docs/py/processing_with_errors.py docs/py/processing.py
```

## Testing Recommendations

### Test Scenarios to Validate

1. **Empty file** - Should show EmptyDataError with clear guidance
2. **Missing columns** - Should list missing and found columns
3. **Unknown newscast formats** - Should show warnings with examples
4. **Invalid dates** - Should show warnings, continue processing
5. **All rows dropped** - Should show InsufficientDataError
6. **Successful processing** - Should show warnings if any
7. **JSON parse error** - Should show ProcessingError

### How to Test

```bash
# 1. Upload empty Excel file
# Expected: EmptyDataError with "file contains 0 rows"

# 2. Upload Excel with wrong columns
# Expected: DataValidationError listing missing columns

# 3. Upload file with weird newscast names
# Expected: Success + warnings showing unknown formats

# 4. Upload file with invalid dates
# Expected: Success + warnings showing date parse failures
```

## Maintenance Guidelines

### Adding New Error Types

1. Create exception class inheriting from `NewscastAuditError`
2. Implement `get_user_action()` with specific guidance
3. Add to `lib/__init__.py` exports
4. Document in `ERROR_HANDLING.md`
5. Write tests

**Example:**

```python
class NetworkError(NewscastAuditError):
    """Raised when network operations fail."""

    def __init__(self, message: str, url: str):
        super().__init__(message, {"url": url})
        self.url = url

    def get_user_action(self) -> str:
        return (
            f"Network request to {self.url} failed. "
            "Check your internet connection and try again."
        )
```

### Improving Error Messages

**Guidelines:**
1. Be specific about what went wrong
2. Explain why it's a problem
3. Tell user exactly what to do
4. Provide examples where helpful
5. Use plain language, avoid jargon

**Bad:**
```
Error: Invalid data
```

**Good:**
```
Excel file is missing required columns: "Which newscast are you auditing?", "Date of newscast:"

What to do: Ensure you're uploading the newscast audit survey export from Microsoft Forms.
The file should be exported directly from the survey without modifications.

Columns found in your file:
• Question1
• Question2
• Timestamp
```

## Performance Considerations

### Error Response Size

- Limit examples to 5 items
- Limit affected rows to 10
- Don't include full DataFrames in error details
- Use pagination for large error lists

### Error UI Performance

- Use CSS for styling, not JavaScript manipulation
- Lazy-load error details (expandable sections)
- Debounce error display if multiple errors
- Clear previous errors before showing new ones

## Security Considerations

### XSS Prevention

The `ErrorUI.escapeHtml()` method prevents XSS:

```javascript
escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;  // This escapes HTML
    return div.innerHTML;
}
```

**Never** use unescaped user input in HTML:

```javascript
// BAD - XSS vulnerable
container.innerHTML = `<div>${errorMessage}</div>`;

// GOOD - XSS safe
container.innerHTML = `<div>${this.escapeHtml(errorMessage)}</div>`;
```

### Sensitive Data

Don't include in error messages:
- Passwords or API keys
- Personal identifiable information (PII)
- Full file contents
- Complete database queries

## Migration Checklist

- [ ] Review exception hierarchy
- [ ] Add error-ui.css to index.html
- [ ] Add error-ui.js to index.html
- [ ] Update app.js to use errorUI
- [ ] Switch to processing_with_errors.py
- [ ] Test empty file scenario
- [ ] Test missing columns scenario
- [ ] Test unknown newscast formats
- [ ] Test invalid dates
- [ ] Verify warnings display correctly
- [ ] Test on mobile devices
- [ ] Test dark mode
- [ ] Add error handling tests
- [ ] Update user documentation
- [ ] Deploy to staging
- [ ] Monitor for errors
- [ ] Deploy to production

## Summary

The enhanced error handling system provides:

✅ **Structured exceptions** with actionable guidance
✅ **Data quality tracking** for non-fatal issues
✅ **Rich error UI** with expandable details
✅ **User-friendly messages** in plain language
✅ **Developer-friendly** debugging information
✅ **Production-ready** with XSS protection and performance optimizations

The implementation is **backwards compatible** - you can adopt it incrementally:

1. Start with just the error UI (5 min)
2. Add quality tracking (10 min)
3. Write tests (ongoing)
4. Add logging (optional)

All files are ready to use - just follow the Phase 1 and Phase 2 steps above!
