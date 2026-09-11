import os
import pandas as pd
import networkx as nx


# ==========================================
# LOAD RELATIONSHIPS
# ==========================================

fir_file = "output/extracted_relationships.csv"
social_media_file = "output/social_media_relationships.csv"

fir_df = pd.read_csv(fir_file)

# Social Media is optional so the existing FIR pipeline
# continues to work even when no social media evidence exists.
if os.path.exists(social_media_file):
    social_media_df = pd.read_csv(social_media_file)
else:
    social_media_df = pd.DataFrame(
        columns=["source", "relationship", "target"]
    )


# ==========================================
# ALLOWED RELATIONSHIPS
# ==========================================

# Existing FIR relationships
FIR_ALLOWED_RELATIONSHIPS = {
    "REPORTED_AGAINST",
    "INVOLVED_IN_CRIME",
    "LOCATED_IN_STATE",
    "LOCATED_IN_DISTRICT",
    "CASE_REGISTERED_AT",
    "CHARGED_UNDER"
}

# Explicit Social Media relationships
SOCIAL_MEDIA_ALLOWED_RELATIONSHIPS = {
    "MENTIONS",
    "REFERENCES",
    "POSTS",
    "USES_HASHTAG"
}


# ==========================================
# CREATE GRAPH
# ==========================================

G = nx.Graph()


# ==========================================
# ADD FIR RELATIONSHIPS
# ==========================================

for _, row in fir_df.iterrows():

    source = row["source"]
    target = row["target"]
    relationship = row["relationship"]

    if relationship not in FIR_ALLOWED_RELATIONSHIPS:
        continue

    if pd.isna(source) or pd.isna(target):
        continue

    source = str(source).strip()
    target = str(target).strip()

    if not source or not target:
        continue

   # Determine entity types from the relationship evidence.
    if relationship == "REPORTED_AGAINST":

        G.add_node(
            source,
            entity_type="COMPLAINANT"
        )

        G.add_node(
            target,
            entity_type="ACCUSED"
        )

    else:

        G.add_node(
            source,
            entity_type="PERSON"
        )

        target_type_map = {
            "LOCATED_IN_STATE": "STATE",
            "LOCATED_IN_DISTRICT": "DISTRICT",
            "CASE_REGISTERED_AT": "POLICE_STATION",
            "INVOLVED_IN_CRIME": "CRIME_CATEGORY",
            "CHARGED_UNDER": "LEGAL_SECTION"
        }

        G.add_node(
            target,
            entity_type=target_type_map.get(
                relationship,
                "ENTITY"
            )
        )

    G.add_edge(
        source,
        target,
        relationship=relationship,
        evidence_source="FIR"
    )


# ==========================================
# ADD SOCIAL MEDIA RELATIONSHIPS
# ==========================================

for _, row in social_media_df.iterrows():

    source = row["source"]
    target = row["target"]
    relationship = row["relationship"]

    if relationship not in SOCIAL_MEDIA_ALLOWED_RELATIONSHIPS:
        continue

    if pd.isna(source) or pd.isna(target):
        continue

    source = str(source).strip()
    target = str(target).strip()

    if not source or not target:
        continue

    G.add_node(source)
    G.add_node(target)

    G.add_edge(
        source,
        target,
        relationship=relationship,
        evidence_source="SOCIAL_MEDIA"
    )


# ==========================================
# GRAPH INFORMATION
# ==========================================

print("\n========================================")
print("CRIMINAL NETWORK GRAPH CREATED")
print("========================================")

print("\nTotal Nodes:", G.number_of_nodes())
print("Total Relationships:", G.number_of_edges())


print("\n===== NETWORK CONNECTIONS =====\n")

for source, target, data in G.edges(data=True):

    print(
        f"{source} "
        f"--- {data['relationship']} ---> "
        f"{target} "
        f"[{data.get('evidence_source', 'UNKNOWN')}]"
    )


# ==========================================
# SAVE GRAPH
# ==========================================

os.makedirs("output", exist_ok=True)

output_file = "output/criminal_network.graphml"

nx.write_graphml(G, output_file)


print("\n========================================")
print("NETWORK SAVED SUCCESSFULLY")
print("========================================")

print("Output file:", output_file)