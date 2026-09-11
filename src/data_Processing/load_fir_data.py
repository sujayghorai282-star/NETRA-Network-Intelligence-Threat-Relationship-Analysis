import pandas as pd
import os
import sys
import re

# ============================================================
# FIR DATA LOADER
# ============================================================

print("\n==========================================")
print(" FIR DATA LOADER")
print("==========================================\n")


# ============================================================
# INPUT FILE
# ============================================================

# If a file path is supplied, use it.
# Otherwise use the existing 30,000 FIR dataset.

if len(sys.argv) > 1:

    file_path = sys.argv[1]

else:

    file_path = "data/fir/indian_fir_30k_synthetic.csv"


print("Input FIR file:")
print(file_path)


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(file_path):

    print(
        f"\nERROR: FIR file not found:\n{file_path}"
    )

    sys.exit(1)


# ============================================================
# LOAD DATASET
# ============================================================

try:

    df = pd.read_csv(
        file_path
    )

except Exception as e:

    print(
        f"\nERROR: Unable to read FIR dataset:\n{e}"
    )

    sys.exit(1)

# ============================================================
# UNIVERSAL FIR COLUMN NORMALIZATION
# ============================================================

def normalize_column_name(column_name):

    name = str(column_name).strip().lower()

    name = re.sub(r"[\s\-/]+", "_", name)

    name = re.sub(r"[^a-z0-9_]", "", name)

    name = re.sub(r"_+", "_", name)

    return name.strip("_")


FIR_COLUMN_ALIASES = {

    "FIR_No": [
        "fir_no",
        "fir_number",
        "fir_num",
        "fir_id",
        "firid",
        "case_no",
        "case_number",
        "case_id",
        "crime_no",
        "crime_number",
        "complaint_no",
        "complaint_number",
        "fir"
    ],

    "Date_Filed": [
        "date_filed",
        "fir_date",
        "date_of_fir",
        "registration_date",
        "registered_on",
        "date_registered",
        "filing_date",
        "date"
    ],

    "State": [
        "state",
        "state_name",
        "province",
        "region"
    ],

    "District": [
        "district",
        "district_name"
    ],

    "Police_Station": [
        "police_station",
        "police_station_name",
        "ps_name",
        "ps",
        "station",
        "station_name",
        "police_post"
    ],

    "Complainant_Name": [
        "complainant_name",
        "complainant",
        "informant",
        "informant_name",
        "victim",
        "victim_name",
        "reporter",
        "reporting_person",
        "applicant"
    ],

    "Accused_Name": [
        "accused_name",
        "accused",
        "suspect",
        "suspect_name",
        "offender",
        "offender_name",
        "defendant",
        "defendant_name",
        "criminal_name"
    ],

    "Legal_Section": [
        "legal_section",
        "section",
        "sections",
        "ipc_section",
        "ipc_sections",
        "law_section",
        "act_section",
        "offence_section",
        "offense_section",
        "legal_provision"
    ],

    "Crime_Category": [
        "crime_category",
        "crime_type",
        "crime",
        "offence",
        "offense",
        "offence_type",
        "offense_type",
        "category",
        "crime_classification"
    ],

    "Incident_Description": [
        "incident_description",
        "description",
        "incident_details",
        "incident",
        "narrative",
        "case_description",
        "complaint_details",
        "details",
        "remarks"
    ],

    "Case_Status": [
        "case_status",
        "status",
        "investigation_status",
        "case_state",
        "disposal_status",
        "current_status"
    ]
}


# ============================================================
# BUILD ALIAS LOOKUP
# ============================================================

alias_lookup = {}

for canonical_name, aliases in FIR_COLUMN_ALIASES.items():

    alias_lookup[
        normalize_column_name(canonical_name)
    ] = canonical_name

    for alias in aliases:

        alias_lookup[
            normalize_column_name(alias)
        ] = canonical_name


# ============================================================
# MAP UPLOADED COLUMNS
# ============================================================

column_mapping = {}

for original_column in df.columns:

    normalized_column = normalize_column_name(
        original_column
    )

    canonical_name = alias_lookup.get(
        normalized_column
    )

    if canonical_name is None:
        continue

    if canonical_name in df.columns:
        continue

    if canonical_name in column_mapping:
        continue

    df[canonical_name] = df[original_column]

    column_mapping[canonical_name] = original_column


# ============================================================
# DISPLAY NORMALIZATION RESULT
# ============================================================

print("\n===== COLUMN NORMALIZATION =====")

if column_mapping:

    for canonical_name, original_column in column_mapping.items():

        print(
            f" {original_column}  -->  {canonical_name}"
        )

else:

    print(
        " No alternate column names detected."
    )

# ============================================================
# UNIVERSAL DATASET VALIDATION
# ============================================================

# A dataset does not need to contain every traditional FIR field.
# It only needs enough meaningful information to create an
# investigator-usable intelligence record.

available_fields = [
    column
    for column in [
        "FIR_No",
        "Date_Filed",
        "State",
        "District",
        "Police_Station",
        "Complainant_Name",
        "Accused_Name",
        "Legal_Section",
        "Crime_Category",
        "Incident_Description",
        "Case_Status"
    ]
    if column in df.columns
]


if not available_fields:

    print("\nERROR: No recognizable FIR/intelligence fields found.")

    print("\nDataset columns:")

    print(df.columns.tolist())

    print(
        "\nThe dataset must contain at least one recognizable "
        "investigative field."
    )

    sys.exit(1)


# ============================================================
# REMOVE COMPLETELY EMPTY RECORDS
# ============================================================

df = df.dropna(how="all")


if df.empty:

    print(
        "\nERROR: Dataset contains no usable records."
    )

    sys.exit(1)


print("\n===== UNIVERSAL DATASET ACCEPTED =====")

print(
    "Recognized FIR fields:",
    len(available_fields)
)

print(
    "Fields:",
    available_fields
)


# ============================================================
# REMOVE COMPLETELY EMPTY RECORDS
# ============================================================

df = df.dropna(
    how="all"
)


if df.empty:

    print(
        "\nERROR: FIR dataset contains no usable records."
    )

    sys.exit(1)

# ============================================================
# SUCCESS MESSAGE
# ============================================================

print(
    "\n===== FIR DATASET LOADED SUCCESSFULLY =====\n"
)

print(
    "Total FIR Records:",
    len(df)
)

print(
    "\nOriginal Columns:"
)

print(
    df.columns.tolist()
)


# ============================================================
# CREATE UNIVERSAL STANDARDIZED FIELDS
# ============================================================

def get_field(row, field_name, default="Unknown"):

    if field_name not in row.index:
        return default

    value = row[field_name]

    if pd.isna(value):
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


# ============================================================
# CREATE UNIVERSAL REPORT ID
# ============================================================

if "FIR_No" in df.columns:

    df["report_id"] = df["FIR_No"].astype(str)

elif "case_id" in df.columns:

    df["report_id"] = df["case_id"].astype(str)

elif "person_id" in df.columns:

    df["report_id"] = df["person_id"].astype(str)

else:

    df["report_id"] = (
        "REPORT_" +
        df.index.astype(str)
    )


# ============================================================
# CREATE UNIVERSAL REPORT TEXT
# ============================================================

def build_report_text(row):

    parts = []

    # Traditional FIR fields
    field_labels = {
        "FIR_No": "FIR",
        "Date_Filed": "Filed on",
        "State": "State",
        "District": "District",
        "Police_Station": "Police Station",
        "Complainant_Name": "Complainant",
        "Accused_Name": "Accused",
        "Legal_Section": "Legal Section",
        "Crime_Category": "Crime Category",
        "Incident_Description": "Incident Description",
        "Case_Status": "Case Status",

        # Universal intelligence fields
        "person_id": "Person ID",
        "name": "Person Name",
        "age": "Age",
        "gender": "Gender",
        "city": "City",
        "crime_type": "Crime Type",
        "incident_year": "Incident Year",
        "severity": "Severity",
        "prior_cases": "Prior Cases",
        "case_id": "Case ID"
    }

    for field_name, label in field_labels.items():

        if field_name not in row.index:
            continue

        value = row[field_name]

        if pd.isna(value):
            continue

        value = str(value).strip()

        if not value:
            continue

        parts.append(
            f"{label}: {value}"
        )

    # Preserve any additional dataset information
    # that wasn't explicitly mapped above.
    known_fields = set(field_labels.keys()) | {
        "report_id",
        "report_text"
    }

    for field_name in row.index:

        if field_name in known_fields:
            continue

        value = row[field_name]

        if pd.isna(value):
            continue

        value = str(value).strip()

        if not value:
            continue

        parts.append(
            f"{field_name}: {value}"
        )

    return ". ".join(parts)


df["report_text"] = df.apply(
    build_report_text,
    axis=1
)


# ============================================================
# SAVE STANDARDIZED DATA
# ============================================================

os.makedirs(
    "output",
    exist_ok=True
)


output_file = (
    "output/standardized_fir_data.csv"
)


df.to_csv(
    output_file,
    index=False
)


# ============================================================
# FINAL STATUS
# ============================================================

print(
    "\n===== FIR STANDARDIZATION COMPLETE =====\n"
)

print(
    "Records processed:",
    len(df)
)

print(
    "Output file:",
    output_file
)

print(
    "\nFIR is ready for relationship extraction."
)