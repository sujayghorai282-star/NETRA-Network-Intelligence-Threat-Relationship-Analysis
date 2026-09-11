import os
import networkx as nx


# ============================================================
# NORMALIZED NETWORK VALIDATION
# ============================================================

GRAPH_FILE = "output/normalized_evidence_network.graphml"


print("\n==========================================")
print(" NORMALIZED NETWORK VALIDATION")
print("==========================================\n")


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(GRAPH_FILE):

    print("ERROR: Normalized graph not found.")

    print("\nExpected:")
    print(GRAPH_FILE)

    raise SystemExit


# ============================================================
# LOAD GRAPH
# ============================================================

print("Loading graph...")

G = nx.read_graphml(GRAPH_FILE)


print("Graph loaded successfully.")


# ============================================================
# BASIC STATISTICS
# ============================================================

print("\n==========================================")
print(" BASIC GRAPH STATISTICS")
print("==========================================")

print("\nNodes:")
print(G.number_of_nodes())

print("\nRelationships:")
print(G.number_of_edges())


# ============================================================
# NODE TYPE VALIDATION
# ============================================================

print("\n==========================================")
print(" NODE TYPE VALIDATION")
print("==========================================")

node_types = {}

for node, data in G.nodes(data=True):

    entity_type = data.get(
        "entity_type",
        "UNKNOWN"
    )

    node_types[entity_type] = (
        node_types.get(entity_type, 0) + 1
    )


for entity_type, count in sorted(
    node_types.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"{entity_type}: {count}"
    )


# ============================================================
# RELATIONSHIP TYPE VALIDATION
# ============================================================

print("\n==========================================")
print(" RELATIONSHIP VALIDATION")
print("==========================================")

relationship_types = {}

for source, target, data in G.edges(data=True):

    relationship = data.get(
        "relationship",
        "UNKNOWN"
    )

    relationship_types[relationship] = (
        relationship_types.get(
            relationship,
            0
        ) + 1
    )


for relationship, count in sorted(
    relationship_types.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"{relationship}: {count}"
    )


# ============================================================
# MISSING NODE TYPES
# ============================================================

print("\n==========================================")
print(" DATA QUALITY CHECK")
print("==========================================")

missing_types = 0

for node, data in G.nodes(data=True):

    entity_type = data.get(
        "entity_type"
    )

    if not entity_type or entity_type == "UNKNOWN":

        missing_types += 1


print(
    "\nNodes without entity type:",
    missing_types
)


# ============================================================
# MISSING RELATIONSHIP TYPES
# ============================================================

missing_relationships = 0

for source, target, data in G.edges(data=True):

    relationship = data.get(
        "relationship"
    )

    if not relationship or relationship == "UNKNOWN":

        missing_relationships += 1


print(
    "Relationships without type:",
    missing_relationships
)


# ============================================================
# MISSING RECORD IDS
# ============================================================

missing_record_ids = 0

for source, target, data in G.edges(data=True):

    record_id = data.get(
        "record_id"
    )

    if not record_id:

        missing_record_ids += 1


print(
    "Relationships without evidence record ID:",
    missing_record_ids
)


# ============================================================
# FINAL RESULT
# ============================================================

print("\n==========================================")
print(" VALIDATION RESULT")
print("==========================================")

if (
    missing_types == 0
    and missing_relationships == 0
    and missing_record_ids == 0
):

    print(
        "\nPASS: Normalized investigation graph is valid."
    )

else:

    print(
        "\nWARNING: Data quality issues detected."
    )

    print(
        "Review the values reported above."
    )


print("\n==========================================\n")