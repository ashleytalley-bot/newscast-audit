import json
import pytest
import pandas as pd
from docs.py.processing import process_json_data as legacy_process
from docs.py.pipeline.orchestrator import ProcessingPipeline

@pytest.fixture
def sample_data():
    first_metric_q = "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? "
    second_metric_q = "Is a tease to streaming in at least every 30 minutes with specific content push for each show?"

    return [
        {
            "Id": 1,
            "Start time": "2023-10-23 09:00:00",
            "Completion time": "2023-10-23 09:05:00",
            "Email": "test@example.com",
            "Name": "Test User",
            "Date of newscast:": "10/23/2023",
            "Which newscast are you auditing?": "5 pm",
            first_metric_q: "Yes",
            second_metric_q: "No"
        },
        {
            "Id": 2,
            "Start time": "2023-10-23 09:10:00",
            "Completion time": "2023-10-23 09:15:00",
            "Email": "test2@example.com",
            "Name": "Test User 2",
            "Date of newscast:": "10/24/2023",
            "Which newscast are you auditing?": "6 pm",
            first_metric_q: "No",
            second_metric_q: "No"
        }
    ]

def test_pipeline_parity(sample_data):
    """
    Verify that the new Pipeline architecture produces identical output 
    to the legacy monolithic script.
    """
    json_str = json.dumps(sample_data)
    
    # Run Legacy
    legacy_output_str = legacy_process(json_str)
    legacy_result = json.loads(legacy_output_str)
    
    # Run New Pipeline
    pipeline = ProcessingPipeline()
    new_output_str = pipeline.execute(json_str)
    new_result = json.loads(new_output_str)
    
    # Compare correctness
    if not legacy_result['success']:
        pytest.fail(f"Legacy processing failed: {legacy_result.get('error')}")
    if not new_result['success']:
        pytest.fail(f"New pipeline processing failed: {new_result.get('error')}")

    assert legacy_result['success'] is True
    assert new_result['success'] is True
    
    # Compare Summary
    assert legacy_result['summary'] == new_result['summary']
    
    # Compare Config (should be identical)
    assert legacy_result['config'] == new_result['config']
    
    # Compare Tables (ignore order if needed, but they should be deterministic)
    assert len(legacy_result['tables']['overall']) == len(new_result['tables']['overall'])
    pd.testing.assert_frame_equal(
        pd.DataFrame(legacy_result['tables']['overall']),
        pd.DataFrame(new_result['tables']['overall'])
    )
    
    # Compare Charts data
    # Overall chart
    assert legacy_result['charts']['overall']['values'] == new_result['charts']['overall']['values']
    assert legacy_result['charts']['overall']['labels'] == new_result['charts']['overall']['labels']
    
    # Compare Quality Warnings
    assert legacy_result['quality']['warnings'] == new_result['quality']['warnings']

