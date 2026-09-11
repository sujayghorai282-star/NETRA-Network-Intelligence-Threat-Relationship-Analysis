import networkx as nx
import pandas as pd
import os


# Load criminal network
input_file = "output/criminal_network.graphml"

G = nx.read_graphml(input_file)


print("\n==========================================")
print(" CRIMINAL NETWORK INTELLIGENCE ANALYSIS")
print("==========================================")

print(f"\nTotal Nodes: {G.number_of_nodes()}")
print(f"Total Relationships: {G.number_of_edges()}")


# ------------------------------------------
# 1. DEGREE CENTRALITY
# ------------------------------------------

degree_centrality = nx.degree_centrality(G)


# ------------------------------------------
# 2. BETWEENNESS CENTRALITY
# ------------------------------------------

betweenness_centrality = nx.betweenness_centrality(
    G,
    k=min(50, G.number_of_nodes()),
    seed=42
)


# ------------------------------------------
# 3. PAGERANK
# ------------------------------------------

pagerank = nx.pagerank(G)


# ------------------------------------------
# CREATE ANALYSIS DATA
# ------------------------------------------

relationship_file = "output/extracted_relationships.csv"

if os.path.exists(relationship_file):
    relationships_df = pd.read_csv(relationship_file)
else:
    relationships_df = pd.DataFrame(
        columns=["source", "target", "relationship"]
    )

# Identify actual person entities.
# Traditional FIR data → REPORTED_AGAINST target
# Universal/person-based data → IDENTIFIED_AS source
person_entities = set()

if not relationships_df.empty:

    accused = relationships_df.loc[
        relationships_df["relationship"] == "REPORTED_AGAINST",
        "target"
    ]

    identified_people = relationships_df.loc[
        relationships_df["relationship"] == "IDENTIFIED_AS",
        "source"
    ]

    person_entities.update(
        accused.dropna().astype(str).str.strip()
    )

    person_entities.update(
        identified_people.dropna().astype(str).str.strip()
    )
print("DEBUG person_entities:", len(person_entities))
print("DEBUG sample person_entities:", list(person_entities)[:10])

graph_people = [
    str(node).strip()
    for node in G.nodes()
    if str(node).strip() in person_entities
]

print("DEBUG matched graph people:", len(graph_people))
print("DEBUG matched people sample:", graph_people[:10])

analysis_data = []

for node in G.nodes():

    node_str = str(node).strip()

    # Keep only actual people in investigator-facing analysis.
    # Crime types, cities, states, years, severity values, etc.
    # remain in the full graph but are not ranked as persons.
    if person_entities and node_str not in person_entities:
        continue

    analysis_data.append({
        "entity": node_str,
        "connections": int(G.degree(node)),
        "degree_centrality": round(
            degree_centrality.get(node, 0), 4
    ),
       "betweenness_centrality": round(
        betweenness_centrality.get(node, 0), 4
    ),
       "pagerank": round(
        pagerank.get(node, 0), 4
    )
})


# Convert to DataFrame
df = pd.DataFrame(analysis_data)


# Create combined influence score
df["influence_score"] = (
    df["degree_centrality"] * 0.4
    + df["betweenness_centrality"] * 0.3
    + df["pagerank"] * 0.3
)


# Sort by influence
df = df.sort_values(
    by="influence_score",
    ascending=False
)


# Create output folder
os.makedirs("output", exist_ok=True)


# Save results
output_file = "output/network_analysis.csv"

df.to_csv(output_file, index=False)


# Display Top 10
print("\nTOP 10 MOST INFLUENTIAL ENTITIES\n")

print(
    df[
        [
            "entity",
            "degree_centrality",
            "betweenness_centrality",
            "pagerank",
            "influence_score"
        ]
    ].head(10).to_string(index=False)
)


print("\n==========================================")
print(" NETWORK ANALYSIS COMPLETED SUCCESSFULLY")
print("==========================================")

print("Output file:", output_file)