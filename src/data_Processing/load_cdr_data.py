import pandas as pd

file_path = "data/cdr/cdr_records.csv"

df = pd.read_csv(file_path)

print("\n===== CDR DATASET LOADED SUCCESSFULLY =====\n")

print("Total Call Records:", len(df))

print("\nDataset Preview:\n")
print(df.head())

print("\nColumns:")
print(df.columns.tolist())

print("\nUnique People Involved:")
people = set(df["caller"]).union(set(df["receiver"]))

for person in people:
    print("-", person)