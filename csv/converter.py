import pandas as pd  
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.output_helpers import get_output_base_dir

# making dataframe
df = pd.read_csv("dataset/dataset.csv")
json_file_path = os.path.join(get_output_base_dir(), "submission.json")


# Convert the DataFrame directly to a list of dictionaries and assign to 'submission'
submission = df.to_dict(orient="records")

# Write the 'submission' list to a JSON file
with open(json_file_path, "w") as file:
    json.dump(submission, file, indent=4)
# output the dataframe
print(df)
