import os
import pandas as pd
import networkx as nx


# ============================================================
# NORMALIZED EVIDENCE NETWORK BUILDER
# ============================================================

INPUT_FILE = "output/normalized_relationships.csv"
OUTPUT_FILE = "output/normalized_evidence_network.graphml"


print("\n==========================================")
print(" NORMALIZED EVIDENCE NETWORK BUILDER")
print("==========================================\n")


# ============================================================
# CHECK INPUT
# ============================================================

if not os.path.exists(INPUT_FILE):

    print("ERROR: Normalized relationship file not found.")

    print("\nExpected:")
    print(INPUT_FILE)

    print("\nRun the evidence normalizer first.")

    raise SystemExit


# ============================================================
# LOAD RELATIONSHIPS
# ============================================================

try:

    df = pd.read_csv(INPUT_FILE)

except Exception as e:

    print("ERROR: Unable to load normalized relationships.")
    print(e)

    raise SystemExit


print("Input file:")
print(INPUT_FILE)

print("\nRelationships loaded:")
print(len(df))


# ============================================================
# VALIDATE COLUMNS
# ============================================================

required_columns = [
    "source",
    "source_type",
    "target",
    "target_type",
    "relationship",
    "record_id"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    print("\nERROR: Missing required columns:")

    for column in missing_columns:
        print(" -", column)

    raise SystemExit


# ============================================================
# CREATE GRAPH
# ============================================================

G = nx.MultiDiGraph()


# ============================================================
# ADD RELATIONSHIPS
# ============================================================

for _, row in df.iterrows():

    source = str(row["source"]).strip()
    target = str(row["target"]).strip()

    source_type = str(
        row["source_type"]
    ).strip()

    target_type = str(
        row["target_type"]
    ).strip()

    relationship = str(
        row["relationship"]
    ).strip()

    record_id = str(
        row["record_id"]
    ).strip()


    if not source or not target:
        continue


    # --------------------------------------------------------
    # Add source node
    # --------------------------------------------------------

    G.add_node(
        source,
        entity_type=source_type
    )


    # --------------------------------------------------------
    # Add target node
    # --------------------------------------------------------

    G.add_node(
        target,
        entity_type=target_type
    )


    # --------------------------------------------------------
    # Add relationship
    # --------------------------------------------------------

    G.add_edge(
        source,
        target,
        relationship=relationship,
        record_id=record_id
    )


# ============================================================
# SAVE GRAPH
# ============================================================

os.makedirs(
    "output",
    exist_ok=True
)


nx.write_graphml(
    G,
    OUTPUT_FILE
)


# ============================================================
# STATISTICS
# ============================================================

print("\n==========================================")
print(" NETWORK CONSTRUCTION COMPLETE")
print("==========================================")

print("\nNodes:")
print(G.number_of_nodes())

print("\nRelationships:")
print(G.number_of_edges())

print("\nEntity types:")

entity_types = {}

for _, data in G.nodes(data=True):

    entity_type = data.get(
        "entity_type",
        "UNKNOWN"
    )

    entity_types[entity_type] = (
        entity_types.get(entity_type, 0) + 1
    )


for entity_type, count in sorted(
    entity_types.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"  {entity_type}: {count}"
    )


print("\nRelationship types:")

relationship_counts = (
    df["relationship"]
    .value_counts()
)


for relationship, count in relationship_counts.items():

    print(
        f"  {relationship}: {count}"
    )


print("\nOutput:")
print(OUTPUT_FILE)

print("\n==========================================\n")