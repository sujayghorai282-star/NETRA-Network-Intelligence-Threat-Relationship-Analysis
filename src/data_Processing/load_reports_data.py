import pandas as pd

file_path = "data/reports/intelligence_reports.csv"

df = pd.read_csv(file_path)

print("\n===== INTELLIGENCE REPORTS LOADED SUCCESSFULLY =====\n")

print("Total Reports:", len(df))

print("\nDataset Preview:\n")
print(df[["report_id", "date", "location"]].head())

print("\nSample Intelligence Report:\n")
print(df.iloc[0]["report_text"])