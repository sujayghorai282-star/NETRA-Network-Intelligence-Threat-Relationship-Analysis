import os
import pandas as pd

PROFILE_FILE = "output/entity_profiles.csv"
EVIDENCE_FILE = "output/evidence_index.csv"

print("\n==========================================")
print(" INVESTIGATION QUERY ENGINE")
print("==========================================\n")


def load_data():
    """Load investigator intelligence indexes."""

    if not os.path.exists(PROFILE_FILE):
        raise FileNotFoundError(
            f"Entity profile file not found: {PROFILE_FILE}"
        )

    if not os.path.exists(EVIDENCE_FILE):
        raise FileNotFoundError(
            f"Evidence index file not found: {EVIDENCE_FILE}"
        )

    profiles = pd.read_csv(PROFILE_FILE)
    evidence = pd.read_csv(EVIDENCE_FILE)

    return profiles, evidence


def query_entity(entity_name):
    """
    Search for an entity and return its investigation context.
    """

    profiles, evidence = load_data()

    entity_name = str(entity_name).strip()

    # Case-insensitive exact search
    profile_match = profiles[
        profiles["entity"].astype(str).str.lower()
        == entity_name.lower()
    ]

    evidence_match = evidence[
        evidence["entity"].astype(str).str.lower()
        == entity_name.lower()
    ]

    if profile_match.empty and evidence_match.empty:
        return None

    result = {
        "entity": entity_name,
        "profile": {},
        "evidence": {}
    }

    if not profile_match.empty:
        row = profile_match.iloc[0]

        result["profile"] = {
            "entity": row.get("entity", ""),
            "entity_type": row.get("entity_type", ""),
            "evidence_count": row.get("evidence_count", 0),
            "relationship_count": row.get("relationship_count", 0),
            "relationship_types": row.get("relationship_types", ""),
            "connected_entity_count": row.get(
                "connected_entity_count", 0
            )
        }

    if not evidence_match.empty:
        row = evidence_match.iloc[0]

        result["evidence"] = {
            "evidence_count": row.get("evidence_count", 0),
            "evidence_records": row.get("evidence_records", ""),
            "relationship_types": row.get(
                "relationship_types", ""
            ),
            "connected_entity_count": row.get(
                "connected_entity_count", 0
            ),
            "connected_entities": row.get(
                "connected_entities", ""
            )
        }

    return result


def print_entity_result(result):

    if result is None:
        print("\nENTITY NOT FOUND")
        return

    print("\n==========================================")
    print(" ENTITY INVESTIGATION RESULT")
    print("==========================================")

    profile = result["profile"]
    evidence = result["evidence"]

    print("\nEntity:")
    print(result["entity"])

    print("\nEntity Type:")
    print(profile.get("entity_type", "UNKNOWN"))

    print("\nEvidence Records:")
    print(evidence.get("evidence_count", 0))

    print("\nRelationship Count:")
    print(profile.get("relationship_count", 0))

    print("\nConnected Entities:")
    print(evidence.get("connected_entity_count", 0))

    print("\nRelationship Types:")
    print(evidence.get("relationship_types", "None"))

    print("\nEvidence Record IDs:")

    records = evidence.get("evidence_records", "")

    if records:
        record_list = records.split(" | ")

        for record in record_list[:10]:
            print(" -", record)

        if len(record_list) > 10:
            print(
                f" ... and {len(record_list) - 10} more"
            )

    print("\nConnected Entities:")

    connected = evidence.get("connected_entities", "")

    if connected:
        connected_list = connected.split(" | ")

        for entity in connected_list[:10]:
            print(" -", entity)

        if len(connected_list) > 10:
            print(
                f" ... and {len(connected_list) - 10} more"
            )


def main():

    print("Loading investigation indexes...")

    profiles, evidence = load_data()

    print("Entity profiles loaded:", len(profiles))
    print("Evidence index records:", len(evidence))

    print("\n==========================================")
    print(" QUERY ENGINE READY")
    print("==========================================")

    # Test using a known entity from the dataset.
    test_entity = "Ganga Dyal"

    print("\nTesting entity search:")
    print(test_entity)

    result = query_entity(test_entity)

    print_entity_result(result)

    print("\n==========================================")
    print(" QUERY ENGINE TEST COMPLETE")
    print("==========================================")


if __name__ == "__main__":
    main()