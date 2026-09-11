import os
import pandas as pd


INPUT_FILE = "output/normalized_cdr_data.csv"
RELATIONSHIP_FILE = "output/normalized_cdr_relationships.csv"

OUTPUT_FILE = "output/cdr_intelligence.csv"


def build_cdr_intelligence():

    print("\n==========================================")
    print(" CDR INTELLIGENCE ANALYSIS")
    print("==========================================\n")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"CDR file not found: {INPUT_FILE}"
        )

    if not os.path.exists(RELATIONSHIP_FILE):
        raise FileNotFoundError(
            f"CDR relationship file not found: "
            f"{RELATIONSHIP_FILE}"
        )

    cdr = pd.read_csv(INPUT_FILE)

    relationships = pd.read_csv(
        RELATIONSHIP_FILE
    )

    print(
        "CDR records:",
        len(cdr)
    )

    print(
        "CDR relationships:",
        len(relationships)
    )


    # --------------------------------------------------------
    # CALL STATISTICS
    # --------------------------------------------------------

    call_relationships = relationships[
        relationships["relationship"] == "CALLED"
    ].copy()


    # --------------------------------------------------------
    # OUTGOING CALL COUNT
    # --------------------------------------------------------

    outgoing = (
        call_relationships
        .groupby("source")
        .size()
        .reset_index(
            name="outgoing_calls"
        )
    )

    outgoing = outgoing.rename(
        columns={
            "source": "entity"
        }
    )


    # --------------------------------------------------------
    # INCOMING CALL COUNT
    # --------------------------------------------------------

    incoming = (
        call_relationships
        .groupby("target")
        .size()
        .reset_index(
            name="incoming_calls"
        )
    )

    incoming = incoming.rename(
        columns={
            "target": "entity"
        }
    )


    # --------------------------------------------------------
    # UNIQUE CONTACTS
    # --------------------------------------------------------

    outgoing_contacts = (
        call_relationships
        .groupby("source")["target"]
        .nunique()
        .reset_index(
            name="unique_outgoing_contacts"
        )
    )

    outgoing_contacts = outgoing_contacts.rename(
        columns={
            "source": "entity"
        }
    )


    incoming_contacts = (
        call_relationships
        .groupby("target")["source"]
        .nunique()
        .reset_index(
            name="unique_incoming_contacts"
        )
    )

    incoming_contacts = incoming_contacts.rename(
        columns={
            "target": "entity"
        }
    )


    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    intelligence = pd.merge(
        outgoing,
        incoming,
        on="entity",
        how="outer"
    )

    intelligence = pd.merge(
        intelligence,
        outgoing_contacts,
        on="entity",
        how="outer"
    )

    intelligence = pd.merge(
        intelligence,
        incoming_contacts,
        on="entity",
        how="outer"
    )


    # --------------------------------------------------------
    # CLEAN COUNTS
    # --------------------------------------------------------

    count_columns = [
        "outgoing_calls",
        "incoming_calls",
        "unique_outgoing_contacts",
        "unique_incoming_contacts"
    ]

    for column in count_columns:

        intelligence[column] = (
            intelligence[column]
            .fillna(0)
            .astype(int)
        )


    # --------------------------------------------------------
    # TOTAL CALLS
    # --------------------------------------------------------

    intelligence["total_calls"] = (
        intelligence["outgoing_calls"]
        + intelligence["incoming_calls"]
    )


    # --------------------------------------------------------
    # UNIQUE CONTACTS
    # --------------------------------------------------------

    intelligence["unique_contacts"] = (
        intelligence["unique_outgoing_contacts"]
        + intelligence["unique_incoming_contacts"]
    )


    # --------------------------------------------------------
    # CDR ACTIVITY SCORE
    # --------------------------------------------------------

    intelligence["cdr_activity_score"] = (
        intelligence["total_calls"] * 0.6
        + intelligence["unique_contacts"] * 0.4
    ).round(2)


    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    intelligence = intelligence.sort_values(
        by="cdr_activity_score",
        ascending=False
    )


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    os.makedirs(
        "output",
        exist_ok=True
    )

    intelligence.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(
        "\nUnique CDR entities:",
        len(intelligence)
    )

    print(
        "Total calls analysed:",
        len(call_relationships)
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print("\nTop CDR activity:")

    print(
        intelligence.head(10).to_string(
            index=False
        )
    )

    print(
        "\n==========================================\n"
    )

    return OUTPUT_FILE


if __name__ == "__main__":

    build_cdr_intelligence()