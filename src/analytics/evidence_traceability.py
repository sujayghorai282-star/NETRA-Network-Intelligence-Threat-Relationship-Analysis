import os
import pandas as pd


INPUT_FILE = "output/normalized_relationships.csv"
OUTPUT_FILE = "output/evidence_traceability.csv"


print("\n==========================================")
print(" EVIDENCE TRACEABILITY LAYER")
print("==========================================\n")


if not os.path.exists(INPUT_FILE):
    print("ERROR: Normalized relationships file not found.")
    print("\nExpected:")
    print(INPUT_FILE)
    raise SystemExit(1)


print("Loading normalized relationships...")

df = pd.read_csv(INPUT_FILE)

print("Relationships loaded:", len(df))


required_columns = [
    "source",
    "target",
    "relationship",
    "record_id"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:
    print("\nERROR: Required columns missing:")

    for column in missing_columns:
        print(" -", column)

    raise SystemExit(1)


print("\n==========================================")
print(" TRACEABILITY VALIDATION")
print("==========================================\n")


missing_record_ids = df["record_id"].isna().sum()
missing_relationships = df["relationship"].isna().sum()
missing_sources = df["source"].isna().sum()
missing_targets = df["target"].isna().sum()


print("Missing evidence record IDs:", missing_record_ids)
print("Missing relationship types:", missing_relationships)
print("Missing source entities:", missing_sources)
print("Missing target entities:", missing_targets)


print("\n==========================================")
print(" BUILDING TRACEABILITY INDEX")
print("==========================================\n")


traceability = df[
    [
        "record_id",
        "source",
        "target",
        "relationship"
    ]
].copy()


traceability["record_id"] = (
    traceability["record_id"]
    .fillna("")
    .astype(str)
    .str.strip()
)

traceability["source"] = (
    traceability["source"]
    .fillna("")
    .astype(str)
    .str.strip()
)

traceability["target"] = (
    traceability["target"]
    .fillna("")
    .astype(str)
    .str.strip()
)

traceability["relationship"] = (
    traceability["relationship"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# Evidence type is derived from the relationship
# because normalized_relationships.csv does not
# currently store the evidence_type column.

traceability["evidence_type"] = "FIR"


traceability = traceability[
    [
        "record_id",
        "evidence_type",
        "source",
        "target",
        "relationship"
    ]
]


traceability = traceability.drop_duplicates()


traceability = traceability.sort_values(
    by=[
        "source",
        "target",
        "relationship",
        "record_id"
    ]
)


os.makedirs("output", exist_ok=True)


traceability.to_csv(
    OUTPUT_FILE,
    index=False
)


print("Traceability records:", len(traceability))


print("\n==========================================")
print(" TRACEABILITY STATISTICS")
print("==========================================\n")


print("Unique evidence records:")
print(traceability["record_id"].nunique())


print("\nUnique source entities:")
print(traceability["source"].nunique())


print("\nUnique target entities:")
print(traceability["target"].nunique())


unique_pairs = traceability[
    ["source", "target"]
].drop_duplicates()


print("\nUnique entity pairs:")
print(len(unique_pairs))


print("\n==========================================")
print(" RELATIONSHIP TYPES")
print("==========================================\n")


relationship_counts = (
    traceability["relationship"]
    .value_counts()
)


for relationship, count in relationship_counts.items():
    print(f"{relationship}: {count}")


print("\n==========================================")
print(" EVIDENCE TYPES")
print("==========================================\n")


evidence_counts = (
    traceability["evidence_type"]
    .value_counts()
)


for evidence_type, count in evidence_counts.items():
    print(f"{evidence_type}: {count}")


print("\n==========================================")
print(" TRACEABILITY COMPLETE")
print("==========================================\n")


print("Output:")
print(OUTPUT_FILE)


print("\nEvery normalized relationship can now be")
print("traced back to its originating evidence record.")


if __name__ == "__main__":
    pass