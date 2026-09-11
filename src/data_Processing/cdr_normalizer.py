import os
import sys
import pandas as pd


print("\n==========================================")
print(" CDR EVIDENCE NORMALIZER")
print("==========================================\n")


# ------------------------------------------------------------
# INPUT FILE
# ------------------------------------------------------------

if len(sys.argv) > 1:
    input_file = sys.argv[1]
else:
    input_file = "data/cdr/synthetic_cdr_20000_all_india.csv"


print("CDR input file:")
print(input_file)


if not os.path.exists(input_file):

    print("\nERROR: CDR file not found.")
    print("Expected location:")
    print(input_file)

    sys.exit(1)


# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

try:

    df = pd.read_csv(input_file)

except Exception as error:

    print("\nERROR: Unable to read CDR dataset.")
    print(error)

    sys.exit(1)


print("\n===== CDR DATASET LOADED SUCCESSFULLY =====\n")

print("Total CDR Records:", len(df))

print("\nOriginal Columns:")
print(df.columns.tolist())


# ------------------------------------------------------------
# REQUIRED COLUMNS
# ------------------------------------------------------------

required_columns = [
    "cdr_id",
    "caller_id",
    "receiver_id",
    "timestamp",
    "call_type",
    "duration_seconds",
    "cell_tower_id",
    "latitude",
    "longitude",
    "imei",
    "imsi",
    "sms_count",
    "data_usage_mb",
    "country",
    "location_type"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    print("\nERROR: Invalid CDR dataset.")

    print("\nMissing columns:")

    for column in missing_columns:
        print(" -", column)

    sys.exit(1)


# ------------------------------------------------------------
# NORMALIZE CDR
# ------------------------------------------------------------

normalized = df.rename(
    columns={
        "cdr_id": "record_id",
        "caller_id": "caller",
        "receiver_id": "receiver",
        "timestamp": "timestamp",
        "call_type": "call_type",
        "duration_seconds": "duration_seconds",
        "cell_tower_id": "cell_tower_id",
        "latitude": "latitude",
        "longitude": "longitude",
        "imei": "imei",
        "imsi": "imsi",
        "sms_count": "sms_count",
        "data_usage_mb": "data_usage_mb",
        "country": "country",
        "location_type": "location_type"
    }
).copy()


# ------------------------------------------------------------
# CLEAN ENTITY VALUES
# ------------------------------------------------------------

for column in [
    "record_id",
    "caller",
    "receiver",
    "call_type",
    "cell_tower_id",
    "imei",
    "imsi",
    "country",
    "location_type"
]:

    normalized[column] = (
        normalized[column]
        .astype(str)
        .str.strip()
    )


# ------------------------------------------------------------
# STANDARDIZE TIMESTAMP
# ------------------------------------------------------------

normalized["timestamp"] = pd.to_datetime(
    normalized["timestamp"],
    errors="coerce"
)


# ------------------------------------------------------------
# STANDARDIZE NUMERIC FIELDS
# ------------------------------------------------------------

numeric_columns = [
    "duration_seconds",
    "latitude",
    "longitude",
    "sms_count",
    "data_usage_mb"
]


for column in numeric_columns:

    normalized[column] = pd.to_numeric(
        normalized[column],
        errors="coerce"
    )


# ------------------------------------------------------------
# REMOVE INVALID CALL RECORDS
# ------------------------------------------------------------

normalized = normalized[
    normalized["caller"].notna()
    & normalized["receiver"].notna()
].copy()


normalized = normalized[
    normalized["caller"].astype(str).str.lower() != "nan"
]

normalized = normalized[
    normalized["receiver"].astype(str).str.lower() != "nan"
]


# ------------------------------------------------------------
# CREATE CDR RELATIONSHIPS
# ------------------------------------------------------------

relationships = normalized[
    [
        "record_id",
        "caller",
        "receiver"
    ]
].copy()


relationships = relationships.rename(
    columns={
        "caller": "source",
        "receiver": "target"
    }
)


relationships["relationship"] = "CALLED"

relationships["evidence_type"] = "CDR"


# ------------------------------------------------------------
# CREATE LOCATION RELATIONSHIPS
# ------------------------------------------------------------

location_relationships = normalized[
    [
        "record_id",
        "caller",
        "cell_tower_id"
    ]
].copy()


location_relationships = location_relationships[
    location_relationships["cell_tower_id"].notna()
]


location_relationships = location_relationships.rename(
    columns={
        "caller": "source",
        "cell_tower_id": "target"
    }
)


location_relationships["relationship"] = (
    "CONNECTED_TO_CELL_TOWER"
)

location_relationships["evidence_type"] = "CDR"


# ------------------------------------------------------------
# COMBINE RELATIONSHIPS
# ------------------------------------------------------------

relationships = pd.concat(
    [
        relationships[
            [
                "source",
                "target",
                "relationship",
                "record_id",
                "evidence_type"
            ]
        ],

        location_relationships[
            [
                "source",
                "target",
                "relationship",
                "record_id",
                "evidence_type"
            ]
        ]
    ],
    ignore_index=True
)


# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------

os.makedirs(
    "output",
    exist_ok=True
)


normalized_output = (
    "output/normalized_cdr_data.csv"
)


relationship_output = (
    "output/normalized_cdr_relationships.csv"
)


normalized.to_csv(
    normalized_output,
    index=False
)


relationships.to_csv(
    relationship_output,
    index=False
)


# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("\n==========================================")
print(" CDR NORMALIZATION COMPLETE")
print("==========================================\n")

print(
    "Input CDR records:",
    len(df)
)

print(
    "Valid CDR records:",
    len(normalized)
)

print(
    "Unique callers:",
    normalized["caller"].nunique()
)

print(
    "Unique receivers:",
    normalized["receiver"].nunique()
)

print(
    "Unique cell towers:",
    normalized["cell_tower_id"].nunique()
)

print(
    "Total CDR relationships:",
    len(relationships)
)

print("\nRelationship types:")

print(
    relationships["relationship"]
    .value_counts()
    .to_string()
)

print("\nNormalized CDR:")
print(normalized_output)

print("\nCDR relationships:")
print(relationship_output)

print("\n==========================================\n")