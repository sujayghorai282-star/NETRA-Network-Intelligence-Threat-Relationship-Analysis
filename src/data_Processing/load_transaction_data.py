import pandas as pd

file_path = "data/transactions/transaction_records.csv"

df = pd.read_csv(file_path)

print("\n===== TRANSACTION DATASET LOADED SUCCESSFULLY =====\n")

print("Total Transactions:", len(df))

print("\nDataset Preview:\n")
print(df.head())

print("\nTotal Transaction Amount:")
print("Rs", df["amount"].sum())

print("\nHighest Transaction:")
highest = df.loc[df["amount"].idxmax()]

print(highest)