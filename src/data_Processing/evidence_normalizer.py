import os
import re
import pandas as pd


# ============================================================
# EVIDENCE NORMALIZATION LAYER
# ============================================================

print("\n==========================================")
print(" EVIDENCE NORMALIZATION LAYER")
print("==========================================\n")


# ============================================================
# FILE PATH
# ============================================================

DEFAULT_FILE = "data/fir/indian_fir_30k_synthetic.csv"

if os.path.exists(DEFAULT_FILE):
    input_file = DEFAULT_FILE
else:
    input_file = None


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {

    "record_id": [
        "FIR_No",
        "FIR Number",
        "FIR_Number",
        "Record_ID",
        "Record_ID",
        "Case_ID",
        "ID"
    ],

    "date": [
        "Date_Filed",
        "Date",
        "Incident_Date",
        "Date_Of_Incident"
    ],

    "state": [
        "State",
        "State_Name"
    ],

    "district": [
        "District",
        "District_Name"
    ],

    "police_station": [
        "Police_Station",
        "Police Station",
        "Station"
    ],

    "complainant": [
        "Complainant_Name",
        "Complainant",
        "Victim_Name",
        "Victim"
    ],

    "accused": [
        "Accused_Name",
        "Accused",
        "Suspect_Name",
        "Suspect"
    ],

    "phone": [
        "Phone",
        "Phone_Number",
        "Mobile",
        "Mobile_Number",
        "Phone_Number",
        "Caller_Number"
    ],

    "location": [
        "Location",
        "Incident_Location",
        "Address"
    ],

    "vehicle": [
        "Vehicle",
        "Vehicle_Number",
        "Vehicle_No",
        "Registration_Number"
    ],

    "organization": [
        "Organization",
        "Organisation",
        "Company",
        "Organization_Name"
    ],

    "bank_account": [
        "Bank_Account",
        "Account_Number",
        "Bank_Account_Number"
    ],

    "crime_category": [
        "Crime_Category",
        "Crime_Type",
        "Crime"
    ],

    "legal_section": [
        "Legal_Section",
        "Section",
        "Law_Section"
    ],

    "description": [
        "Incident_Description",
        "Description",
        "Incident",
        "Details"
    ],

    "case_status": [
        "Case_Status",
        "Status"
    ],

    "amount": [
        "Amount",
        "Transaction_Amount",
        "Value"
    ]
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return ""

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    return value


def find_column(df, aliases):

    for column in aliases:

        if column in df.columns:
            return column

    return None


# ============================================================
# DETECT COLUMN MAPPING
# ============================================================

def detect_column_mapping(df):

    mapping = {}

    for normalized_field, aliases in COLUMN_ALIASES.items():

        column = find_column(df, aliases)

        if column:
            mapping[normalized_field] = column

    return mapping


# ============================================================
# DETECT EVIDENCE TYPE
# ============================================================

def detect_evidence_type(mapping):

    fields = set(mapping.keys())

    if "accused" in fields and "complainant" in fields:
        return "FIR"

    if "phone" in fields:
        return "CDR"

    if "bank_account" in fields or "amount" in fields:
        return "FINANCIAL"

    if "vehicle" in fields:
        return "VEHICLE"

    if "organization" in fields:
        return "ORGANIZATION"

    return "GENERAL"


# ============================================================
# ENTITY TYPE CLASSIFICATION
# ============================================================

def classify_entity_type(field):

    entity_types = {

        "record_id": "RECORD",

        "person": "PERSON",

        "accused": "ACCUSED",

        "complainant": "COMPLAINANT",

        "phone": "PHONE",

        "location": "LOCATION",

        "state": "STATE",

        "district": "DISTRICT",

        "police_station": "POLICE_STATION",

        "vehicle": "VEHICLE",

        "organization": "ORGANIZATION",

        "bank_account": "BANK_ACCOUNT",

        "crime_category": "CRIME_CATEGORY",

        "legal_section": "LEGAL_SECTION",

        "date": "DATE",

        "description": "DESCRIPTION",

        "case_status": "CASE_STATUS",

        "amount": "AMOUNT"
    }

    return entity_types.get(field, "ENTITY")


# ============================================================
# NORMALIZE DATAFRAME
# ============================================================

def normalize_dataframe(df, mapping):

    normalized = pd.DataFrame(index=df.index)

    # --------------------------------------------------------
    # Preserve original data
    # --------------------------------------------------------

    for column in df.columns:
        normalized[column] = df[column]

    # --------------------------------------------------------
    # Create normalized fields
    # --------------------------------------------------------

    normalized_fields = [
        "record_id",
        "date",
        "person",
        "accused",
        "complainant",
        "phone",
        "location",
        "state",
        "district",
        "police_station",
        "vehicle",
        "organization",
        "bank_account",
        "crime_category",
        "legal_section",
        "description",
        "case_status",
        "amount"
    ]

    for field in normalized_fields:

        if field in mapping:

            source_column = mapping[field]

            normalized[field] = (
                df[source_column]
                .apply(clean_value)
            )

        else:

            normalized[field] = ""

    # --------------------------------------------------------
    # Person field
    # --------------------------------------------------------

    if "accused" in mapping:

        normalized["person"] = normalized["accused"]

    elif "complainant" in mapping:

        normalized["person"] = normalized["complainant"]

    # --------------------------------------------------------
    # Evidence type
    # --------------------------------------------------------

    evidence_type = detect_evidence_type(mapping)

    normalized["evidence_type"] = evidence_type

    # --------------------------------------------------------
    # Original row number
    # --------------------------------------------------------

    normalized["original_row"] = range(
        1,
        len(normalized) + 1
    )

    # --------------------------------------------------------
    # Entity type columns
    # --------------------------------------------------------

    for field in normalized_fields:

        normalized[f"{field}_type"] = classify_entity_type(field)

    return normalized


# ============================================================
# RELATIONSHIP HELPER
# ============================================================

def add_relationship(
    relationships,
    source,
    source_type,
    target,
    target_type,
    relationship,
    record_id
):

    source = clean_value(source)
    target = clean_value(target)

    if not source or not target:
        return

    if source.lower() in ["unknown", "unidentified", "n/a", "none"]:
        return

    if target.lower() in ["unknown", "unidentified", "n/a", "none"]:
        return

    relationships.append({

        "source": source,
        "source_type": source_type,

        "target": target,
        "target_type": target_type,

        "relationship": relationship,

        "record_id": record_id
    })


# ============================================================
# GENERATE RELATIONSHIPS
# ============================================================

def generate_relationships(normalized_df, evidence_type):

    relationships = []

    for _, row in normalized_df.iterrows():

        record_id = row.get("record_id", "")

        # ====================================================
        # FIR RELATIONSHIPS
        # ====================================================

        if evidence_type == "FIR":

            complainant = row.get("complainant", "")
            accused = row.get("accused", "")

            state = row.get("state", "")
            district = row.get("district", "")
            police_station = row.get("police_station", "")

            crime_category = row.get(
                "crime_category",
                ""
            )

            legal_section = row.get(
                "legal_section",
                ""
            )

            # Complainant -> Accused

            add_relationship(
                relationships,
                complainant,
                "COMPLAINANT",
                accused,
                "ACCUSED",
                "REPORTED_AGAINST",
                record_id
            )

            # Accused -> State

            add_relationship(
                relationships,
                accused,
                "ACCUSED",
                state,
                "STATE",
                "LOCATED_IN_STATE",
                record_id
            )

            # Accused -> District

            add_relationship(
                relationships,
                accused,
                "ACCUSED",
                district,
                "DISTRICT",
                "LOCATED_IN_DISTRICT",
                record_id
            )

            # Accused -> Police Station

            add_relationship(
                relationships,
                accused,
                "ACCUSED",
                police_station,
                "POLICE_STATION",
                "CASE_REGISTERED_AT",
                record_id
            )

            # Accused -> Crime Category

            add_relationship(
                relationships,
                accused,
                "ACCUSED",
                crime_category,
                "CRIME_CATEGORY",
                "INVOLVED_IN_CRIME",
                record_id
            )

            # Accused -> Legal Section

            add_relationship(
                relationships,
                accused,
                "ACCUSED",
                legal_section,
                "LEGAL_SECTION",
                "CHARGED_UNDER",
                record_id
            )

        # ====================================================
        # CDR RELATIONSHIPS
        # ====================================================

        elif evidence_type == "CDR":

            phone = row.get("phone", "")
            person = row.get("person", "")
            location = row.get("location", "")

            add_relationship(
                relationships,
                phone,
                "PHONE",
                person,
                "PERSON",
                "ASSOCIATED_WITH",
                record_id
            )

            add_relationship(
                relationships,
                phone,
                "PHONE",
                location,
                "LOCATION",
                "USED_AT",
                record_id
            )

        # ====================================================
        # FINANCIAL RELATIONSHIPS
        # ====================================================

        elif evidence_type == "FINANCIAL":

            account = row.get(
                "bank_account",
                ""
            )

            person = row.get(
                "person",
                ""
            )

            organization = row.get(
                "organization",
                ""
            )

            amount = row.get(
                "amount",
                ""
            )

            add_relationship(
                relationships,
                person,
                "PERSON",
                account,
                "BANK_ACCOUNT",
                "LINKED_TO_ACCOUNT",
                record_id
            )

            add_relationship(
                relationships,
                organization,
                "ORGANIZATION",
                account,
                "BANK_ACCOUNT",
                "LINKED_TO_ACCOUNT",
                record_id
            )

            if amount:

                add_relationship(
                    relationships,
                    account,
                    "BANK_ACCOUNT",
                    str(amount),
                    "AMOUNT",
                    "TRANSACTION_VALUE",
                    record_id
                )

        # ====================================================
        # VEHICLE RELATIONSHIPS
        # ====================================================

        elif evidence_type == "VEHICLE":

            vehicle = row.get(
                "vehicle",
                ""
            )

            person = row.get(
                "person",
                ""
            )

            location = row.get(
                "location",
                ""
            )

            add_relationship(
                relationships,
                person,
                "PERSON",
                vehicle,
                "VEHICLE",
                "ASSOCIATED_WITH",
                record_id
            )

            add_relationship(
                relationships,
                vehicle,
                "VEHICLE",
                location,
                "LOCATION",
                "OBSERVED_AT",
                record_id
            )

        # ====================================================
        # ORGANIZATION RELATIONSHIPS
        # ====================================================

        elif evidence_type == "ORGANIZATION":

            person = row.get(
                "person",
                ""
            )

            organization = row.get(
                "organization",
                ""
            )

            location = row.get(
                "location",
                ""
            )

            add_relationship(
                relationships,
                person,
                "PERSON",
                organization,
                "ORGANIZATION",
                "ASSOCIATED_WITH",
                record_id
            )

            add_relationship(
                relationships,
                organization,
                "ORGANIZATION",
                location,
                "LOCATION",
                "LOCATED_AT",
                record_id
            )

        # ====================================================
        # GENERAL EVIDENCE
        # ====================================================

        else:

            person = row.get(
                "person",
                ""
            )

            location = row.get(
                "location",
                ""
            )

            organization = row.get(
                "organization",
                ""
            )

            vehicle = row.get(
                "vehicle",
                ""
            )

            add_relationship(
                relationships,
                person,
                "PERSON",
                location,
                "LOCATION",
                "ASSOCIATED_WITH",
                record_id
            )

            add_relationship(
                relationships,
                person,
                "PERSON",
                organization,
                "ORGANIZATION",
                "ASSOCIATED_WITH",
                record_id
            )

            add_relationship(
                relationships,
                person,
                "PERSON",
                vehicle,
                "VEHICLE",
                "ASSOCIATED_WITH",
                record_id
            )

    return pd.DataFrame(
        relationships,
        columns=[
            "source",
            "source_type",
            "target",
            "target_type",
            "relationship",
            "record_id"
        ]
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    global input_file

    print("Evidence file:")

    if input_file is None:

        print("ERROR: FIR dataset not found.")

        print(
            "\nExpected file:"
        )

        print(
            DEFAULT_FILE
        )

        return

    print(input_file)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            input_file
        )

    except Exception as e:

        print(
            "\nERROR: Unable to read evidence file:"
        )

        print(e)

        return

    # --------------------------------------------------------
    # Detect columns
    # --------------------------------------------------------

    mapping = detect_column_mapping(df)

    evidence_type = detect_evidence_type(
        mapping
    )

    print(
        "\nDetected evidence type:"
    )

    print(evidence_type)

    print(
        "\nDetected column mapping:"
    )

    for normalized_field, source_column in mapping.items():

        print(
            f"  {source_column} -> {normalized_field}"
        )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    normalized_df = normalize_dataframe(
        df,
        mapping
    )

    # --------------------------------------------------------
    # Generate relationships
    # --------------------------------------------------------

    relationships_df = generate_relationships(
        normalized_df,
        evidence_type
    )

    # --------------------------------------------------------
    # Create output folder
    # --------------------------------------------------------

    os.makedirs(
        "output",
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save normalized evidence
    # --------------------------------------------------------

    normalized_file = (
        "output/normalized_evidence.csv"
    )

    normalized_df.to_csv(
        normalized_file,
        index=False
    )

    # --------------------------------------------------------
    # Save normalized relationships
    # --------------------------------------------------------

    relationships_file = (
        "output/normalized_relationships.csv"
    )

    relationships_df.to_csv(
        relationships_file,
        index=False
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print(
        "\nRecords:"
    )

    print(
        len(normalized_df)
    )

    print(
        "\nNormalized fields:"
    )

    print(
        normalized_df.columns.tolist()
    )

    print(
        "\nRelationships generated:"
    )

    print(
        len(relationships_df)
    )

    print(
        "\n=========================================="
    )

    print(
        " NORMALIZATION COMPLETE"
    )

    print(
        "=========================================="
    )

    print(
        "\nNormalized evidence:"
    )

    print(
        normalized_file
    )

    print(
        "\nNormalized relationships:"
    )

    print(
        relationships_file
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()