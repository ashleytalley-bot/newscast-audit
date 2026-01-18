import pandas as pd
df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
df.to_excel('test_survey.xlsx', index=False)
