import pytest
import json
import pandas as pd
import sys
import os

# Add docs/py to path to import processing_with_errors
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../docs/py')))

from processing_with_errors import process_json_data

# Valid sample data using correct MS Forms column names
VALID_DATA = [
    {
        "Which newscast are you auditing?": "5-7am",
        "Date of newscast:": "2024-01-15",
        "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ": "Yes",
        "Is a tease to streaming in at least every 30 minutes with specific content push for each show?": "No",
         "Did we use streaming content and/or mobile shorts in this show?": "N/A",
        "Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?": "Yes",
        "Is there a clearly defined weather story, supported by graphics or video?": "Yes",
        "Does each weather hit focus on new/now/next?": "Yes",
        "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "No",
        "Are anchors shown three times per show on tight shots with name supers?": "Yes",
        "Did we specifically reference every piece of file or non-descript video?": "No",
        "Do anchors add local context to two or more stories and include one community-celebration story per hour?": "Yes"
    },
    {
        "Which newscast are you auditing?": "6pm",
        "Date of newscast:": "2024-01-15",
       "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ": "No",
        "Is a tease to streaming in at least every 30 minutes with specific content push for each show?": "Yes",
         "Did we use streaming content and/or mobile shorts in this show?": "Yes",
        "Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?": "Yes",
        "Is there a clearly defined weather story, supported by graphics or video?": "No",
        "Does each weather hit focus on new/now/next?": "No",
        "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "Yes",
        "Are anchors shown three times per show on tight shots with name supers?": "Yes",
        "Did we specifically reference every piece of file or non-descript video?": "Yes",
        "Do anchors add local context to two or more stories and include one community-celebration story per hour?": "No"
    }
]

def test_process_success():
    """Test successful processing with valid data."""
    json_str = json.dumps(VALID_DATA)
    result_str = process_json_data(json_str)
    result = json.loads(result_str)

    if not result["success"]:
        pytest.fail(f"Processing failed with error: {result.get('error')}")

    assert result["success"] is True
    assert "summary" in result
    assert result["summary"]["record_count"] == 2
    assert "tables" in result
    assert "charts" in result
    assert "quality" in result

def test_process_empty_file():
    """Test processing an empty list."""
    json_str = json.dumps([])
    result_str = process_json_data(json_str)
    result = json.loads(result_str)

    assert result["success"] is False
    assert result["error"]["error_type"] == "EmptyDataError"
    assert "0 rows" in result["error"]["message"]

def test_process_missing_columns():
    """Test processing data with missing required columns."""
    bad_data = [{"Wrong Column": "Value"}]
    json_str = json.dumps(bad_data)
    result_str = process_json_data(json_str)
    result = json.loads(result_str)

    assert result["success"] is False
    assert result["error"]["error_type"] == "DataValidationError"
    assert "missing_columns" in result["error"]["details"]

def test_process_quality_warnings():
    """Test success with quality warnings for unknown newscasts."""
    data_with_unknown = [
        {
            "Which newscast are you auditing?": "Unknown News",
            "Date of newscast:": "2024-01-15",
             "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ": "Yes",
            "Is a tease to streaming in at least every 30 minutes with specific content push for each show?": "No",
             "Did we use streaming content and/or mobile shorts in this show?": "N/A",
            "Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?": "Yes",
            "Is there a clearly defined weather story, supported by graphics or video?": "Yes",
            "Does each weather hit focus on new/now/next?": "Yes",
            "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": "No",
            "Are anchors shown three times per show on tight shots with name supers?": "Yes",
            "Did we specifically reference every piece of file or non-descript video?": "No",
            "Do anchors add local context to two or more stories and include one community-celebration story per hour?": "Yes"
        }
    ]
    json_str = json.dumps(data_with_unknown)
    result_str = process_json_data(json_str)
    result = json.loads(result_str)

    if not result["success"]:
         pytest.fail(f"Processing failed with error: {result.get('error')}")

    assert result["success"] is True
    assert result["quality"]["warnings"]
    warning = result["quality"]["warnings"][0]
    assert "unrecognized newscast formats" in warning["message"]
    assert "Unknown News" in warning["examples"]
