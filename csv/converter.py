import pandas as pd  
import json

# making dataframe
df = pd.read_csv("dataset/dataset.csv")
json_file_path = "submission.json"


# Convert the DataFrame directly to a list of dictionaries and assign to 'submission'
submission = df.to_dict(orient="records")

# Write the 'submission' list to a JSON file
with open(json_file_path, "w") as file:
    json.dump(submission, file, indent=4)
# output the dataframe
print(df)
