import os
import sys
import pandas as pd


# ==========================================
# TRANSACTION NORMALIZER
# ==========================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

OUTPUT_FOLDER = os.path.join(
    PROJECT_ROOT,
    "output"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "normalized_transaction_data.csv"
)


# ==========================================
# COLUMN ALIASES
# ==========================================

COLUMN_ALIASES = {

    "transaction_id": [
        "transaction_id",
        "transactionid",
        "txn_id",
        "txnid",
        "record_id",
        "transaction_no",
        "transaction_number",
        "id"
    ],

    "sender": [
        "sender",
        "sender_id",
        "sender_account",
        "from",
        "from_account",
        "source",
        "source_account",
        "payer",
        "payer_id"
    ],

    "receiver": [
        "receiver",
        "receiver_id",
        "receiver_account",
        "to",
        "to_account",
        "target",
        "target_account",
        "payee",
        "payee_id"
    ],

    "amount": [
        "amount",
        "transaction_amount",
        "txn_amount",
        "value",
        "transaction_value",
        "money"
    ],

    "date": [
        "date",
        "transaction_date",
        "txn_date",
        "timestamp",
        "datetime",
        "time",
        "transaction_time"
    ],

    "account": [
        "account",
        "account_id",
        "account_number",
        "bank_account",
        "bank_account_id"
    ]
}


# ==========================================
# FIND COLUMN
# ==========================================

def find_column(columns, aliases):

    normalized_columns = {
        str(column).strip().lower(): column
        for column in columns
    }

    for alias in aliases:

        alias_lower = alias.lower()

        if alias_lower in normalized_columns:

            return normalized_columns[
                alias_lower
            ]

    return None


# ==========================================
# NORMALIZE TRANSACTIONS
# ==========================================

def normalize_transactions(file_path):

    if not file_path:

        raise ValueError(
            "Transaction file path was not provided."
        )

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Transaction file not found: {file_path}"
        )

    # --------------------------------------
    # LOAD CSV
    # --------------------------------------

    df = pd.read_csv(
        file_path
    )

    if df.empty:

        raise ValueError(
            "Uploaded transaction CSV "
            "contains no records."
        )

    # --------------------------------------
    # DETECT COLUMNS
    # --------------------------------------

    rename_map = {}

    for canonical_name, aliases in COLUMN_ALIASES.items():

        original_column = find_column(
            df.columns,
            aliases
        )

        if original_column is not None:

            rename_map[
                original_column
            ] = canonical_name

    df = df.rename(
        columns=rename_map
    )

    # --------------------------------------
    # TRANSACTION ID
    # --------------------------------------

    if "transaction_id" not in df.columns:

        df["transaction_id"] = [
            f"TXN_{index + 1:06d}"
            for index in range(len(df))
        ]

    # --------------------------------------
    # SENDER
    # --------------------------------------

    if "sender" not in df.columns:

        df["sender"] = ""

    # --------------------------------------
    # RECEIVER
    # --------------------------------------

    if "receiver" not in df.columns:

        df["receiver"] = ""

    # --------------------------------------
    # ACCOUNT
    # --------------------------------------

    if "account" not in df.columns:

        df["account"] = ""

    # --------------------------------------
    # AMOUNT
    # --------------------------------------

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0.0)

    else:

        df["amount"] = 0.0

    # --------------------------------------
    # DATE
    # --------------------------------------

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    else:

        df["date"] = pd.NaT

    # --------------------------------------
    # CLEAN TEXT FIELDS
    # --------------------------------------

    text_columns = [
        "transaction_id",
        "sender",
        "receiver",
        "account"
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # --------------------------------------
    # REMOVE EMPTY RECORDS
    # --------------------------------------

    df = df[
        ~(
            (df["sender"] == "")
            &
            (df["receiver"] == "")
            &
            (df["account"] == "")
            &
            (df["amount"] == 0)
        )
    ].copy()

    # --------------------------------------
    # TRANSACTION TYPE
    # --------------------------------------

    def classify_transaction(row):

        sender = str(
            row["sender"]
        ).strip()

        receiver = str(
            row["receiver"]
        ).strip()

        if sender and receiver:

            return "TRANSFER"

        if sender:

            return "OUTGOING"

        if receiver:

            return "INCOMING"

        if row["account"]:

            return "ACCOUNT_ACTIVITY"

        return "UNSPECIFIED"

    df["transaction_type"] = df.apply(
        classify_transaction,
        axis=1
    )

    # --------------------------------------
    # EVIDENCE TYPE
    # --------------------------------------

    df["evidence_type"] = (
        "TRANSACTION"
    )

    # --------------------------------------
    # SOURCE FILE
    # --------------------------------------

    df["source_file"] = os.path.basename(
        file_path
    )

    # --------------------------------------
    # RECORD TEXT
    # --------------------------------------

    def create_record_text(row):

        parts = []

        if row["transaction_id"]:

            parts.append(
                f"Transaction ID: "
                f"{row['transaction_id']}"
            )

        if row["sender"]:

            parts.append(
                f"Sender: "
                f"{row['sender']}"
            )

        if row["receiver"]:

            parts.append(
                f"Receiver: "
                f"{row['receiver']}"
            )

        if row["account"]:

            parts.append(
                f"Account: "
                f"{row['account']}"
            )

        if row["amount"] != 0:

            parts.append(
                f"Amount: "
                f"{row['amount']}"
            )

        if pd.notna(row["date"]):

            parts.append(
                f"Date: "
                f"{row['date']}"
            )

        parts.append(
            f"Transaction Type: "
            f"{row['transaction_type']}"
        )

        return " | ".join(parts)

    df["record_text"] = df.apply(
        create_record_text,
        axis=1
    )

    # --------------------------------------
    # SAVE OUTPUT
    # --------------------------------------

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    return df


# ==========================================
# COMMAND-LINE ENTRY POINT
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "TRANSACTION NORMALIZATION FAILED"
        )

        print(
            "ERROR: Transaction CSV path "
            "was not provided."
        )

        sys.exit(1)

    input_file = sys.argv[1]

    try:

        normalized_df = normalize_transactions(
            input_file
        )

        print(
            "TRANSACTION NORMALIZATION COMPLETE"
        )

        print(
            f"Transaction Records: "
            f"{len(normalized_df)}"
        )

        print(
            f"Output: {OUTPUT_FILE}"
        )

        print(
            "Columns:"
        )

        print(
            list(normalized_df.columns)
        )

    except Exception as error:

        print(
            "TRANSACTION NORMALIZATION FAILED"
        )

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)