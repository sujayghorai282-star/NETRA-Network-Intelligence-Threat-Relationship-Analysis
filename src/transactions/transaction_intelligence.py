import os
import pandas as pd


# ==========================================
# TRANSACTION INTELLIGENCE
# ==========================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

INPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "output",
    "normalized_transaction_data.csv"
)

OUTPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "output",
    "transaction_intelligence.csv"
)


# ==========================================
# GENERATE TRANSACTION INTELLIGENCE
# ==========================================

def generate_transaction_intelligence():

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            "Normalized transaction data was not found."
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    if df.empty:

        raise ValueError(
            "Normalized transaction dataset is empty."
        )

    # --------------------------------------
    # CLEAN NUMERIC DATA
    # --------------------------------------

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0.0)

    # --------------------------------------
    # ENTITY COLLECTION
    # --------------------------------------

    entities = set()

    if "sender" in df.columns:

        entities.update(
            df["sender"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[
                lambda x: x != ""
            ]
            .tolist()
        )

    if "receiver" in df.columns:

        entities.update(
            df["receiver"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[
                lambda x: x != ""
            ]
            .tolist()
        )

    if "account" in df.columns:

        entities.update(
            df["account"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[
                lambda x: x != ""
            ]
            .tolist()
        )

    # --------------------------------------
    # ENTITY-LEVEL ANALYSIS
    # --------------------------------------

    intelligence_records = []

    for entity in sorted(entities):

        outgoing = df[
            df["sender"].astype(str).str.strip()
            == entity
        ]

        incoming = df[
            df["receiver"].astype(str).str.strip()
            == entity
        ]

        outgoing_amount = float(
            outgoing["amount"].sum()
        )

        incoming_amount = float(
            incoming["amount"].sum()
        )

        total_activity = (
            outgoing_amount
            + incoming_amount
        )

        transaction_count = (
            len(outgoing)
            + len(incoming)
        )

        contacts = set()

        for target in outgoing["receiver"]:

            target = str(target).strip()

            if target and target != entity:

                contacts.add(target)

        for source in incoming["sender"]:

            source = str(source).strip()

            if source and source != entity:

                contacts.add(source)

        unique_contacts = len(
            contacts
        )

        # ----------------------------------
        # ACTIVITY SCORE
        # ----------------------------------

        activity_score = min(
            100.0,
            (
                transaction_count * 2
                + unique_contacts * 3
                + min(
                    total_activity / 100000,
                    50
                )
            )
        )

        intelligence_records.append(
            {
                "entity": entity,
                "transaction_count": transaction_count,
                "unique_contacts": unique_contacts,
                "outgoing_transactions": len(
                    outgoing
                ),
                "incoming_transactions": len(
                    incoming
                ),
                "outgoing_amount": round(
                    outgoing_amount,
                    2
                ),
                "incoming_amount": round(
                    incoming_amount,
                    2
                ),
                "total_transaction_value": round(
                    total_activity,
                    2
                ),
                "transaction_activity_score": round(
                    activity_score,
                    2
                )
            }
        )

    # --------------------------------------
    # SAVE INTELLIGENCE
    # --------------------------------------

    intelligence_df = pd.DataFrame(
        intelligence_records
    )

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    intelligence_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    return intelligence_df


# ==========================================
# COMMAND-LINE ENTRY POINT
# ==========================================

if __name__ == "__main__":

    try:

        result = (
            generate_transaction_intelligence()
        )

        print(
            "TRANSACTION INTELLIGENCE COMPLETE"
        )

        print(
            f"Entities analyzed: {len(result)}"
        )

        print(
            f"Output: {OUTPUT_FILE}"
        )

    except Exception as error:

        print(
            "TRANSACTION INTELLIGENCE FAILED"
        )

        print(
            f"ERROR: {error}"
        )

        raise