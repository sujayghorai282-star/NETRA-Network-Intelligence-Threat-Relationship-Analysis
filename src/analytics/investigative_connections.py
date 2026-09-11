import pandas as pd
import os
from itertools import combinations

print("\n==========================================")
print(" INVESTIGATIVE CONNECTION ANALYSIS")
print("==========================================\n")


# ==========================================
# LOAD RELATIONSHIP DATA
# ==========================================

input_file = "output/extracted_relationships.csv"

if not os.path.exists(input_file):
    print(f"ERROR: File not found: {input_file}")
    exit()

df = pd.read_csv(input_file)

required_columns = {"source", "target", "relationship"}

if not required_columns.issubset(df.columns):
    print("ERROR: Relationship file has invalid structure.")
    print("Required columns:", required_columns)
    print("Available columns:", list(df.columns))
    exit()


# ==========================================
# DETECT DATA MODE
# ==========================================

reported_df = df[
    df["relationship"] == "REPORTED_AGAINST"
].copy()

identified_df = df[
    df["relationship"] == "IDENTIFIED_AS"
].copy()

linked_case_df = df[
    df["relationship"] == "LINKED_TO_CASE"
].copy()


traditional_mode = not reported_df.empty

universal_mode = (
    reported_df.empty
    and not identified_df.empty
)


if traditional_mode:

    print("DATA MODE: TRADITIONAL FIR")

elif universal_mode:

    print("DATA MODE: UNIVERSAL / PERSON-CASE DATASET")

else:

    print("WARNING: No supported human relationship structure found.")


# ==========================================
# TRADITIONAL FIR MODE
# ==========================================

if traditional_mode:

    print(
        "Total FIR-based human relationships:",
        len(reported_df)
    )


    # ======================================
    # ACCUSED -> COMPLAINANT EVIDENCE MAP
    # ======================================

    accused_complainants = (
        reported_df
        .groupby("target")
        .apply(
            lambda group: list(
                zip(
                    group["source"],
                    group["report_id"]
                )
            )
        )
        .to_dict()
    )


    # ======================================
    # COMPLAINANT -> ACCUSED MAP
    # ======================================

    complainant_accused = (
        reported_df
        .groupby("source")
        .apply(
            lambda group: list(
                zip(
                    group["target"],
                    group["report_id"]
                )
            )
        )
        .to_dict()
    )


    # ======================================
    # BUILD ACCUSED-TO-ACCUSED CONNECTIONS
    # ======================================

    connections = []


    for complainant, records in complainant_accused.items():

        unique_records = list(
            dict.fromkeys(records)
        )

        accused_list = sorted(
            set(
                accused
                for accused, _ in unique_records
            )
        )


        if len(accused_list) < 2:
            continue


        for entity_a, entity_b in combinations(
            accused_list,
            2
        ):

            fir_a = next(
                fir
                for accused, fir in unique_records
                if accused == entity_a
            )

            fir_b = next(
                fir
                for accused, fir in unique_records
                if accused == entity_b
            )


            connections.append({
                "entity_a": entity_a,
                "entity_b": entity_b,
                "shared_complainant": complainant,
                "fir_a": fir_a,
                "fir_b": fir_b,
                "shared_complainants": 1,
                "connection_type": "SHARED_COMPLAINANT"
            })


    # ======================================
    # ENTITY SUMMARY
    # ======================================

    connection_counts = {}

    for row in connections:

        entity_a = row["entity_a"]
        entity_b = row["entity_b"]

        connection_counts[entity_a] = (
            connection_counts.get(entity_a, 0) + 1
        )

        connection_counts[entity_b] = (
            connection_counts.get(entity_b, 0) + 1
        )


    entity_summary = []


    for entity, evidence in accused_complainants.items():

        complainants = set(
            complainant
            for complainant, _ in evidence
        )

        entity_summary.append({
            "entity": entity,
            "fir_count": len(evidence),
            "direct_complainants": len(complainants),
            "investigative_connections":
                connection_counts.get(entity, 0)
        })


    connections_df = pd.DataFrame(connections)

    entity_summary_df = pd.DataFrame(
        entity_summary
    )


# ==========================================
# UNIVERSAL DATA MODE
# ==========================================

elif universal_mode:

    print(
        "Identified person relationships:",
        len(identified_df)
    )

    print(
        "Person-case relationships:",
        len(linked_case_df)
    )


    # ======================================
    # IDENTIFY ACTUAL PERSON ENTITIES
    # ======================================

    person_entities = set(
        identified_df["source"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    person_entities = {
        person
        for person in person_entities
        if person
    }


    # ======================================
    # BUILD PERSON -> CASE MAP
    # ======================================

    person_case_records = {}

    if not linked_case_df.empty:

        for _, row in linked_case_df.iterrows():

            person = str(row["source"]).strip()
            case_id = str(row["target"]).strip()

            if not person or not case_id:
                continue

            if person not in person_case_records:
                person_case_records[person] = []

            person_case_records[person].append(
                case_id
            )


    # ======================================
    # BUILD CASE -> PEOPLE MAP
    # ======================================

    case_people = {}

    for person, cases in person_case_records.items():

        for case_id in set(cases):

            if case_id not in case_people:
                case_people[case_id] = set()

            case_people[case_id].add(person)


    # ======================================
    # BUILD PERSON-TO-PERSON CONNECTIONS
    # USING SHARED CASE ONLY
    # ======================================

    connections = []

    for case_id, people in case_people.items():

        people = sorted(people)

        if len(people) < 2:
            continue


        for entity_a, entity_b in combinations(
            people,
            2
        ):

            connections.append({
                "entity_a": entity_a,
                "entity_b": entity_b,
                "shared_complainant": "",
                "fir_a": "",
                "fir_b": "",
                "shared_complainants": 0,
                "connection_type": "SHARED_CASE",
                "shared_case": case_id
            })


    # ======================================
    # CONNECTION COUNTS
    # ======================================

    connection_counts = {}

    for row in connections:

        entity_a = row["entity_a"]
        entity_b = row["entity_b"]

        connection_counts[entity_a] = (
            connection_counts.get(entity_a, 0) + 1
        )

        connection_counts[entity_b] = (
            connection_counts.get(entity_b, 0) + 1
        )


    # ======================================
    # CREATE UNIVERSAL ENTITY SUMMARY
    # ======================================

    entity_summary = []


    for entity in sorted(person_entities):

        # IMPORTANT:
        # There is NO complainant information
        # in the universal dataset.
        #
        # Therefore direct_complainants MUST
        # remain zero rather than being inferred.

        entity_summary.append({
            "entity": entity,
            "fir_count": 0,
            "direct_complainants": 0,
            "investigative_connections":
                connection_counts.get(entity, 0)
        })


    connections_df = pd.DataFrame(connections)

    entity_summary_df = pd.DataFrame(
        entity_summary
    )


# ==========================================
# NO SUPPORTED MODE
# ==========================================

else:

    print(
        "WARNING: Dataset does not contain "
        "supported person relationship semantics."
    )

    connections_df = pd.DataFrame(
        columns=[
            "entity_a",
            "entity_b",
            "shared_complainant",
            "fir_a",
            "fir_b",
            "shared_complainants",
            "connection_type"
        ]
    )

    entity_summary_df = pd.DataFrame(
        columns=[
            "entity",
            "fir_count",
            "direct_complainants",
            "investigative_connections"
        ]
    )


# ==========================================
# SAVE INVESTIGATIVE CONNECTIONS
# ==========================================

os.makedirs("output", exist_ok=True)


connections_file = (
    "output/investigative_connections.csv"
)


connections_df.to_csv(
    connections_file,
    index=False
)


# ==========================================
# SAVE ENTITY SUMMARY
# ==========================================

summary_file = (
    "output/investigative_entity_connections.csv"
)


entity_summary_df.to_csv(
    summary_file,
    index=False
)


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n==========================================")
print(" INVESTIGATIVE CONNECTION ANALYSIS COMPLETE")
print("==========================================\n")


print(
    "Unique person entities:",
    len(entity_summary_df)
)


print(
    "Person-to-person connections:",
    len(connections_df)
)


print(
    "Entities with investigative connections:",
    sum(
        1
        for value in connection_counts.values()
        if value > 0
    )
    if "connection_counts" in locals()
    else 0
)


# ==========================================
# CONNECTION RESULTS
# ==========================================

print("\nTOP INVESTIGATIVE CONNECTIONS:\n")


if not connections_df.empty:

    display_columns = [
        column
        for column in [
            "entity_a",
            "entity_b",
            "shared_complainant",
            "shared_case",
            "fir_a",
            "fir_b",
            "connection_type"
        ]
        if column in connections_df.columns
    ]

    print(
        connections_df[
            display_columns
        ]
        .head(20)
        .to_string(index=False)
    )

else:

    print(
        "No evidence-based person-to-person "
        "connections found."
    )


# ==========================================
# ENTITY RESULTS
# ==========================================

print("\nTOP CONNECTED ENTITIES:\n")


if not entity_summary_df.empty:

    print(
        entity_summary_df
        .sort_values(
            by="investigative_connections",
            ascending=False
        )
        .head(20)
        .to_string(index=False)
    )

else:

    print("No person entities available.")


# ==========================================
# OUTPUT FILES
# ==========================================

print("\n==========================================")
print("OUTPUT FILES")
print("==========================================")

print(
    "Connections:",
    connections_file
)

print(
    "Entity Summary:",
    summary_file
)

print("==========================================\n")