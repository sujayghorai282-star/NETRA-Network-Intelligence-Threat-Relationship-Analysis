import os
import pandas as pd

print("\n==========================================")
print(" FIR + CDR CORRELATION ENGINE")
print("==========================================\n")

MAPPING_FILE = "data/mappings/fir_cdr_identity_mapping.csv"
FIR_CONTEXT_FILE = "output/investigation_context.csv"
CDR_INTELLIGENCE_FILE = "output/cdr_intelligence.csv"

OUTPUT_FILE = "output/fir_cdr_correlation.csv"


# ==========================================
# CHECK INPUT FILES
# ==========================================

required_files = [
    MAPPING_FILE,
    FIR_CONTEXT_FILE,
    CDR_INTELLIGENCE_FILE
]

for file_path in required_files:

    if not os.path.exists(file_path):

        print("ERROR: Required file not found:")
        print(file_path)

        raise SystemExit(1)


# ==========================================
# LOAD DATA
# ==========================================

mapping = pd.read_csv(MAPPING_FILE)
fir_context = pd.read_csv(FIR_CONTEXT_FILE)
cdr_intelligence = pd.read_csv(CDR_INTELLIGENCE_FILE)


# ==========================================
# VALIDATE MAPPING
# ==========================================

required_mapping_columns = {
    "entity",
    "subscriber_id",
    "mapping_status",
    "mapping_source"
}

if not required_mapping_columns.issubset(mapping.columns):

    print("ERROR: Invalid identity mapping file.")

    print("\nRequired columns:")
    print(sorted(required_mapping_columns))

    raise SystemExit(1)


# ==========================================
# NORMALIZE IDENTIFIERS
# ==========================================

mapping["entity"] = (
    mapping["entity"]
    .astype(str)
    .str.strip()
)

mapping["subscriber_id"] = (
    mapping["subscriber_id"]
    .astype(str)
    .str.strip()
)

mapping["mapping_status"] = (
    mapping["mapping_status"]
    .astype(str)
    .str.strip()
)

mapping["mapping_source"] = (
    mapping["mapping_source"]
    .astype(str)
    .str.strip()
)


fir_context["entity"] = (
    fir_context["entity"]
    .astype(str)
    .str.strip()
)

cdr_intelligence["entity"] = (
    cdr_intelligence["entity"]
    .astype(str)
    .str.strip()
)


# ==========================================
# BUILD CDR LOOKUP
# ==========================================

cdr_lookup = cdr_intelligence.set_index("entity")


correlation_records = []


# ==========================================
# CORRELATE IDENTITIES
# ==========================================

for _, mapping_row in mapping.iterrows():

    fir_entity = mapping_row["entity"]

    subscriber_id = mapping_row["subscriber_id"]

    mapping_status = mapping_row["mapping_status"]

    mapping_source = mapping_row["mapping_source"]


    # --------------------------------------
    # FIR ENTITY
    # --------------------------------------

    fir_matches = fir_context[
        fir_context["entity"].str.lower()
        ==
        fir_entity.lower()
    ]


    if fir_matches.empty:

        print(
            f"WARNING: FIR entity not found: "
            f"{fir_entity}"
        )

        continue


    fir_record = fir_matches.iloc[0]


    # --------------------------------------
    # CDR ENTITY
    # --------------------------------------

    if subscriber_id not in cdr_lookup.index:

        print(
            f"WARNING: CDR subscriber not found: "
            f"{subscriber_id}"
        )

        continue


    cdr_record = cdr_lookup.loc[subscriber_id]


    # --------------------------------------
    # CREATE CORRELATION RECORD
    # --------------------------------------

    correlation_records.append({

        "fir_entity":
            fir_entity,

        "subscriber_id":
            subscriber_id,

        "mapping_status":
            mapping_status,

        "mapping_source":
            mapping_source,

        "fir_entity_type":
            fir_record.get(
                "entity_type",
                ""
            ),

        "fir_evidence_count":
            fir_record.get(
                "evidence_count",
                0
            ),

        "fir_relationship_count":
            fir_record.get(
                "relationship_count",
                0
            ),

        "fir_risk_score":
            fir_record.get(
                "risk_score",
                0
            ),

        "fir_risk_level":
            fir_record.get(
                "risk_level",
                "UNKNOWN"
            ),

        "traceable_evidence_count":
            fir_record.get(
                "traceable_evidence_count",
                0
            ),

        "cdr_total_calls":
            cdr_record.get(
                "total_calls",
                0
            ),

        "cdr_unique_contacts":
            cdr_record.get(
                "unique_contacts",
                0
            ),

        "cdr_outgoing_calls":
            cdr_record.get(
                "outgoing_calls",
                0
            ),

        "cdr_incoming_calls":
            cdr_record.get(
                "incoming_calls",
                0
            ),

        "cdr_activity_score":
            cdr_record.get(
                "cdr_activity_score",
                0
            )

    })


# ==========================================
# CREATE OUTPUT
# ==========================================

correlation_df = pd.DataFrame(
    correlation_records
)


os.makedirs(
    "output",
    exist_ok=True
)


correlation_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# SUMMARY
# ==========================================

print("\n===== CORRELATION COMPLETE =====\n")

print(
    "Identity mappings processed:",
    len(mapping)
)

print(
    "FIR + CDR correlations:",
    len(correlation_df)
)

print(
    "Output file:",
    OUTPUT_FILE
)


if not correlation_df.empty:

    print("\nCorrelation Records:\n")

    print(
        correlation_df.to_string(
            index=False
        )
    )

else:

    print(
        "\nNo valid FIR + CDR correlations "
        "were generated."
    )


print("\n==========================================")
print(" CORRELATION ENGINE FINISHED")
print("==========================================\n")