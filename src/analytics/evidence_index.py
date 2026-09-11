import os
import pandas as pd

INPUT_FILE = "output/normalized_relationships.csv"
OUTPUT_FILE = "output/evidence_index.csv"

print("\n==========================================")
print(" INVESTIGATION EVIDENCE INDEX")
print("==========================================\n")

print("Loading normalized relationships...")

if not os.path.exists(INPUT_FILE):
    print(f"ERROR: Input file not found: {INPUT_FILE}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_FILE)

required_columns = [
    "source",
    "target",
    "relationship",
    "record_id"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    print("ERROR: Missing required columns:")
    for col in missing:
        print(f" - {col}")
    raise SystemExit(1)

print("Relationships loaded:", len(df))

# --------------------------------------------------
# BUILD ENTITY -> EVIDENCE INDEX
# --------------------------------------------------

print("\n==========================================")
print(" BUILDING EVIDENCE INDEX")
print("==========================================")

entity_index = {}

for row in df.itertuples(index=False):

    source = str(row.source)
    target = str(row.target)
    relationship = str(row.relationship)
    record_id = str(row.record_id)

    # Source entity
    if source not in entity_index:
        entity_index[source] = {
            "evidence_records": set(),
            "relationships": set(),
            "connected_entities": set()
        }

    entity_index[source]["evidence_records"].add(record_id)
    entity_index[source]["relationships"].add(relationship)
    entity_index[source]["connected_entities"].add(target)

    # Target entity
    if target not in entity_index:
        entity_index[target] = {
            "evidence_records": set(),
            "relationships": set(),
            "connected_entities": set()
        }

    entity_index[target]["evidence_records"].add(record_id)
    entity_index[target]["relationships"].add(relationship)
    entity_index[target]["connected_entities"].add(source)

print("Unique entities indexed:", len(entity_index))

# --------------------------------------------------
# CREATE OUTPUT RECORDS
# --------------------------------------------------

print("\n==========================================")
print(" GENERATING EVIDENCE INDEX RECORDS")
print("==========================================")

records = []

for entity, data in entity_index.items():

    evidence_records = sorted(data["evidence_records"])
    relationships = sorted(data["relationships"])
    connected_entities = sorted(data["connected_entities"])

    records.append({
        "entity": entity,
        "evidence_count": len(evidence_records),
        "evidence_records": " | ".join(evidence_records),
        "relationship_count": len(relationships),
        "relationship_types": " | ".join(relationships),
        "connected_entity_count": len(connected_entities),
        "connected_entities": " | ".join(connected_entities)
    })

index_df = pd.DataFrame(records)

# --------------------------------------------------
# SORT BY EVIDENCE COUNT
# --------------------------------------------------

index_df = index_df.sort_values(
    by="evidence_count",
    ascending=False
).reset_index(drop=True)

# --------------------------------------------------
# QUALITY CHECK
# --------------------------------------------------

print("\n==========================================")
print(" EVIDENCE INDEX QUALITY CHECK")
print("==========================================")

print("Total indexed entities:", len(index_df))

missing_entities = index_df["entity"].isna().sum()
missing_evidence = index_df["evidence_records"].eq("").sum()

print("Missing entity names:", missing_entities)
print("Entities without evidence:", missing_evidence)

# --------------------------------------------------
# SAVE
# --------------------------------------------------

print("\n==========================================")
print(" SAVING EVIDENCE INDEX")
print("==========================================")

os.makedirs("output", exist_ok=True)

index_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nOutput:")
print(OUTPUT_FILE)

print("\n==========================================")
print(" EVIDENCE INDEX BUILD COMPLETE")
print("==========================================")