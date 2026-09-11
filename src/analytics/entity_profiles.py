import os
import pandas as pd


RELATIONSHIP_FILE = "output/normalized_relationships.csv"
TRACEABILITY_FILE = "output/evidence_traceability.csv"
OUTPUT_FILE = "output/entity_profiles.csv"


print("\n==========================================")
print(" INVESTIGATOR ENTITY PROFILE BUILDER")
print("==========================================\n")


if not os.path.exists(RELATIONSHIP_FILE):
    print("ERROR: Normalized relationships file not found.")
    print("\nExpected:")
    print(RELATIONSHIP_FILE)
    raise SystemExit(1)


print("Loading normalized relationships...")

df = pd.read_csv(RELATIONSHIP_FILE)

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
print(" BUILDING ENTITY INDEX")
print("==========================================\n")


source_entities = df[
    ["source"]
].rename(columns={"source": "entity"})

target_entities = df[
    ["target"]
].rename(columns={"target": "entity"})


all_entities = pd.concat(
    [source_entities, target_entities],
    ignore_index=True
)


all_entities = (
    all_entities["entity"]
    .dropna()
    .astype(str)
    .str.strip()
)


all_entities = sorted(
    all_entities[all_entities != ""].unique()
)


print("Unique entities:", len(all_entities))


print("\n==========================================")
print(" BUILDING ENTITY PROFILES")
print("==========================================\n")


profiles = []


for entity in all_entities:

    source_rows = df[df["source"] == entity]
    target_rows = df[df["target"] == entity]

    relationships = pd.concat(
        [source_rows, target_rows],
        ignore_index=True
    )

    evidence_ids = sorted(
        relationships["record_id"]
        .dropna()
        .astype(str)
        .unique()
    )

    relationship_types = sorted(
        relationships["relationship"]
        .dropna()
        .astype(str)
        .unique()
    )

    connected_entities = set()

    for _, row in source_rows.iterrows():
        connected_entities.add(str(row["target"]))

    for _, row in target_rows.iterrows():
        connected_entities.add(str(row["source"]))

    connected_entities.discard(entity)

    entity_type = "UNKNOWN"

    source_relationships = set(
        source_rows["relationship"]
        .dropna()
        .astype(str)
    )

    target_relationships = set(
        target_rows["relationship"]
        .dropna()
        .astype(str)
    )


    # Determine entity type from its graph role.

    if "REPORTED_AGAINST" in target_relationships:
        entity_type = "ACCUSED"

    elif "REPORTED_AGAINST" in source_relationships:
        entity_type = "COMPLAINANT"

    elif "LOCATED_IN_STATE" in target_relationships:
        entity_type = "STATE"

    elif "LOCATED_IN_DISTRICT" in target_relationships:
        entity_type = "DISTRICT"

    elif "CASE_REGISTERED_AT" in target_relationships:
        entity_type = "POLICE_STATION"

    elif "INVOLVED_IN_CRIME" in target_relationships:
        entity_type = "CRIME_CATEGORY"

    elif "CHARGED_UNDER" in target_relationships:
        entity_type = "LEGAL_SECTION"


    profiles.append({
        "entity": entity,
        "entity_type": entity_type,
        "evidence_count": len(evidence_ids),
        "connection_count": len(connected_entities),
        "relationship_count": len(relationships),
        "relationship_types": " | ".join(relationship_types),
        "evidence_records": " | ".join(evidence_ids),
        "connected_entities": " | ".join(
            sorted(connected_entities)
        )
    })


profiles_df = pd.DataFrame(profiles)


print("Profiles generated:", len(profiles_df))


print("\n==========================================")
print(" ENTITY TYPE SUMMARY")
print("==========================================\n")


type_counts = (
    profiles_df["entity_type"]
    .value_counts()
)


for entity_type, count in type_counts.items():
    print(f"{entity_type}: {count}")


print("\n==========================================")
print(" PROFILE QUALITY CHECK")
print("==========================================\n")


missing_entities = profiles_df["entity"].isna().sum()
missing_types = (
    profiles_df["entity_type"]
    .isna()
    .sum()
)


print("Missing entity names:", missing_entities)
print("Missing entity types:", missing_types)


print("\n==========================================")
print(" SAVING ENTITY PROFILES")
print("==========================================\n")


os.makedirs("output", exist_ok=True)


profiles_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("Output:")
print(OUTPUT_FILE)


print("\n==========================================")
print(" ENTITY PROFILE BUILD COMPLETE")
print("==========================================\n")


if __name__ == "__main__":
    pass