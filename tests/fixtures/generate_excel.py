
import pandas as pd
import os

def generate_fixture(output_path):
    # exact headers from survey.yaml
    data = {
        "Id": [1, 2],
        "Start time": ["2024-01-01 10:00:00", "2024-01-02 10:00:00"],
        "Completion time": ["2024-01-01 10:05:00", "2024-01-02 10:05:00"],
        "Email": ["tester@example.com", "tester@example.com"],
        "Name": ["Tester", "Tester"],
        "Date of newscast:": ["2024-01-01", "2024-01-02"],
        "Which newscast are you auditing?": ["5 pm", "6 pm"],
        # Metrics - minimal set, mixing Yes/No
        "Does each story create urgency with time relevance and active writing explaining why stories are being told right now? ": ["Yes", "No"],
        "Is a tease to streaming in at least every 30 minutes with specific content push for each show?": ["Yes", "Yes"],
        "Did we use streaming content and/or mobile shorts in this show?": ["No", "Yes"],
        "Are maps, timelines and supporting graphics used within 30 minutes for events and included as useful context in newscasts?": ["Yes", "No"],
        "Is there a clearly defined weather story, supported by graphics or video?": ["Yes", "Yes"],
        "Does each weather hit focus on new/now/next?": ["No", "No"],
        "Does the story address the audience as \"you,\" end with \"Here's what you can do today\"?": ["Yes", "No"],
        "Are anchors shown three times per show on tight shots with name supers?": ["Yes", "Yes"],
        "Did we specifically reference every piece of file or non-descript video?": ["No", "Yes"],
        "Do anchors add local context to two or more stories and include one community-celebration story per hour?": ["Yes", "No"],
        "Additional comments below:": ["Test comment 1", "Test comment 2"]
    }

    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to Excel
    df.to_excel(output_path, index=False)
    print(f"Generated fixture at {output_path}")

if __name__ == "__main__":
    generate_fixture("tests/fixtures/test_upload.xlsx")
