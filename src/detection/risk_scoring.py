import pandas as pd
import os
# Load standardized criminal dataset for universal recurrence analysis
standardized_file = "output/standardized_fir_data.csv"

if os.path.exists(standardized_file):
    standardized_df = pd.read_csv(standardized_file)
else:
    standardized_df = pd.DataFrame()
print("\n========================================")
print("       RISK SCORING STARTED")
print("========================================\n")

os.makedirs("output", exist_ok=True)

input_file = "output/network_analysis.csv"

if not os.path.exists(input_file):
    print(f"ERROR: File not found: {input_file}")
    print("Run network_analysis.py first.")
    exit()

df = pd.read_csv(input_file)

# ==========================================
# LOAD RELATIONSHIP DATA
# ==========================================

relationship_file = "output/extracted_relationships.csv"

if not os.path.exists(relationship_file):
    print(f"ERROR: File not found: {relationship_file}")
    exit()

relationships_df = pd.read_csv(relationship_file)


# ==========================================
# IDENTIFY ACCUSED ENTITIES
# ==========================================

# Select investigative entities
# Traditional FIR datasets may contain REPORTED_AGAINST,
# while universal datasets may contain people through
# IDENTIFIED_AS / INVOLVED_IN_CRIME relationships.

accused_entities = set(
    relationships_df.loc[
        relationships_df["relationship"] == "REPORTED_AGAINST",
        "target"
    ]
)

if accused_entities:
    df = df[df["entity"].isin(accused_entities)].copy()
else:
    # Universal dataset fallback:
    # keep person entities identified by the relationship extractor.
    person_entities = set(
        relationships_df.loc[
            relationships_df["relationship"] == "IDENTIFIED_AS",
            "source"
        ]
    )

    if person_entities:
        df = df[df["entity"].isin(person_entities)].copy()
    else:
        print("WARNING: No person entities identified for risk scoring.")
        df = df.iloc[0:0].copy()


# ==========================================
# CONNECTIONS
# ==========================================

df["connections"] = (
    pd.to_numeric(df["connections"], errors="coerce")
    .fillna(0)
    .astype(int)
)


# ==========================================
# NETWORK SCORES
# ==========================================

df["centrality_score"] = df["degree_centrality"]

df["bridge_score"] = df["betweenness_centrality"]

df["pagerank_score"] = df["pagerank"]

df["influence_score"] = df["influence_score"]


# ==========================================
# NORMALIZATION FUNCTION
# ==========================================

def normalize(series):

    min_value = series.min()
    max_value = series.max()

    if max_value > min_value:
        return ((series - min_value) / (max_value - min_value)) * 100

    return series * 0


# ==========================================
# NORMALIZE NETWORK METRICS
# ==========================================

df["connection_risk"] = normalize(df["connections"])

df["bridge_risk"] = normalize(df["bridge_score"])

df["pagerank_risk"] = normalize(df["pagerank_score"])

df["influence_risk"] = normalize(df["influence_score"])


# ==========================================
# FIR RECURRENCE
# ==========================================

# Calculate recurrence / previous-case involvement
#
# Traditional FIR datasets:
#   REPORTED_AGAINST relationships represent repeated FIR involvement.
#
# Universal criminal datasets:
#   prior_cases represents previously recorded cases for a person.

fir_counts = (
    relationships_df[
        relationships_df["relationship"] == "REPORTED_AGAINST"
    ]
    .groupby("target")
    .size()
)

df["fir_count"] = (
    df["entity"]
    .map(fir_counts)
    .fillna(0)
    .astype(int)
)



# The relationship count above only tells us that prior-case
# information exists, so extract the actual numeric value from
# the standardized report text when available.
# Get previous-case counts from the standardized source dataset.
# Match using the person's name because the network analysis
# currently stores the person name as the entity.

df["prior_cases"] = 0

if not standardized_df.empty and "name" in standardized_df.columns:

    source_prior_cases = pd.to_numeric(
        standardized_df.get("prior_cases", 0),
        errors="coerce"
    ).fillna(0)

    source_names = (
        standardized_df["name"]
        .astype(str)
        .str.strip()
    )

    prior_case_map = (
        pd.DataFrame({
            "name": source_names,
            "prior_cases": source_prior_cases
        })
        .groupby("name")["prior_cases"]
        .max()
    )

    df["prior_cases"] = (
        df["entity"]
        .astype(str)
        .str.strip()
        .map(prior_case_map)
        .fillna(0)
        .astype(int)
    )

# Combine observed FIR involvement with known previous cases.
df["recurrence_count"] = (
    df["fir_count"] + df["prior_cases"]
)

df["recurrence_risk"] = normalize(
    df["recurrence_count"]
)

# ==========================================
# RISK SCORE
# ==========================================

# ==========================================
# INVESTIGATIVE CONNECTION SIGNAL
# ==========================================

connection_file = "output/investigative_entity_connections.csv"

if os.path.exists(connection_file):

    connection_df = pd.read_csv(connection_file)

    df = df.merge(
        connection_df[
            [
                "entity",
                "direct_complainants",
                "investigative_connections"
            ]
        ],
        on="entity",
        how="left"
    )

    df["direct_complainants"] = (
        df["direct_complainants"]
        .fillna(0)
        .astype(int)
    )

    df["investigative_connections"] = (
        df["investigative_connections"]
        .fillna(0)
        .astype(int)
    )

else:

    print("WARNING: Investigative connection file not found.")

    df["direct_complainants"] = 0
    df["investigative_connections"] = 0


# ==========================================
# NORMALIZE INVESTIGATIVE SIGNALS
# ==========================================

df["complainant_risk"] = normalize(
    df["direct_complainants"]
)

df["investigative_connection_risk"] = normalize(
    df["investigative_connections"]
)


# ==========================================
# INVESTIGATIVE PRIORITY SCORE
# ==========================================

# Determine whether complainant evidence is actually available.
# Never penalize a dataset simply because that field does not exist.

has_complainant_evidence = (
    df["direct_complainants"].fillna(0).sum() > 0
)

if has_complainant_evidence:

    # Traditional FIR-style data
    # All investigative signals are available.

    df["risk_score"] = (
        df["recurrence_risk"] * 0.30
        + df["complainant_risk"] * 0.20
        + df["investigative_connection_risk"] * 0.20
        + df["connection_risk"] * 0.10
        + df["bridge_risk"] * 0.10
        + df["influence_risk"] * 0.10
    )

else:

    # Universal person/case datasets
    # No complainant information is available.
    #
    # Redistribute the unused 20% proportionally across
    # the available investigative signals.

    df["risk_score"] = (
        df["recurrence_risk"] * 0.375
        + df["investigative_connection_risk"] * 0.25
        + df["connection_risk"] * 0.125
        + df["bridge_risk"] * 0.125
        + df["influence_risk"] * 0.125
    )

df["risk_score"] = df["risk_score"].round(2)


# ==========================================
# RISK LEVEL
# ==========================================

def get_risk_level(score):

    if score >= 70:
        return "HIGH"

    elif score >= 40:
        return "MEDIUM"

    else:
        return "LOW"


df["risk_level"] = df["risk_score"].apply(
    get_risk_level
)


# ==========================================
# SORT RESULTS
# ==========================================

df = df.sort_values(
    by="risk_score",
    ascending=False
)


# ==========================================
# PREPARE OUTPUT
# ==========================================

# ==========================================
# PREPARE OUTPUT
# ==========================================

output_df = df[
    [
        "entity",
        "connections",
        "fir_count",
        "prior_cases",
        "recurrence_count",
        "direct_complainants",
        "investigative_connections",
        "risk_score",
        "risk_level"
    ]
]


# ==========================================
# SAVE OUTPUT
# ==========================================

output_file = "output/risk_analysis.csv"

output_df.to_csv(
    output_file,
    index=False
)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n========================================")
print("       RISK ANALYSIS COMPLETED")
print("========================================\n")

print("Total Accused Entities:", len(output_df))

print("\nRISK LEVEL DISTRIBUTION:\n")

print(
    output_df["risk_level"].value_counts()
)

print("\nTOP 15 HIGH-PRIORITY ENTITIES:\n")

print(
    output_df.head(15).to_string(index=False)
)

print("\n========================================")
print("Output file:", output_file)
print("========================================\n")