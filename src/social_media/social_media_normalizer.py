import pandas as pd
import os
import csv
import sys
def read_social_media_csv(input_file):
    """
    Read Social Media CSV safely.

    Repairs rows where post_text contains unquoted commas.
    The expected structure is 9 columns, so:
    - first 3 fields = post_id, user_id, username
    - last 5 fields = timestamp, location, mentions, hashtags, organizations
    - everything between them = post_text
    """

    expected_columns = [
        "post_id",
        "user_id",
        "username",
        "post_text",
        "timestamp",
        "location",
        "mentions",
        "hashtags",
        "organizations"
    ]

    rows = []

    with open(
        input_file,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.reader(f)

        header = next(reader)

        for line_number, row in enumerate(reader, start=2):

            if len(row) == 9:
                rows.append(row)

            elif len(row) > 9:
                # Recover commas accidentally left unquoted
                # inside post_text.
                repaired_row = (
                    row[:3]
                    + [",".join(row[3:-5])]
                    + row[-5:]
                )

                if len(repaired_row) == 9:
                    rows.append(repaired_row)
                else:
                    print(
                        f"WARNING: Could not repair line {line_number}"
                    )

            else:
                print(
                    f"WARNING: Skipping incomplete line {line_number}"
                )

    return pd.DataFrame(
        rows,
        columns=expected_columns
    )

REQUIRED_COLUMNS = [
    "post_id",
    "user_id",
    "username",
    "post_text",
    "timestamp",
    "location"
]


def normalize_social_media(input_file):
    """
    Normalize social media CSV data into a consistent structure.

    Expected input columns:
        post_id
        user_id
        username
        post_text
        timestamp
        location
        mentions
        hashtags
        organizations

    Returns:
        pandas DataFrame containing normalized social media records.
    """

    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"Social media input file not found: {input_file}"
        )

    df = read_social_media_csv(input_file)

    # ------------------------------------------------------------
    # Validate required columns
    # ------------------------------------------------------------
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required social media columns: "
            + ", ".join(missing_columns)
        )

    # ------------------------------------------------------------
    # Add optional columns if they do not exist
    # ------------------------------------------------------------

    optional_columns = [
        "mentions",
        "hashtags",
        "organizations"
    ]

    for column in optional_columns:
        if column not in df.columns:
            df[column] = ""

    # ------------------------------------------------------------
    # Clean text fields
    # ------------------------------------------------------------

    text_columns = [
        "post_id",
        "user_id",
        "username",
        "post_text",
        "timestamp",
        "location",
        "mentions",
        "hashtags",
        "organizations"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # ------------------------------------------------------------
    # Remove completely empty posts
    # ------------------------------------------------------------

    df = df[
        (df["post_id"] != "") &
        (df["user_id"] != "")
    ].copy()

    # ------------------------------------------------------------
    # Remove duplicate posts
    # ------------------------------------------------------------

    df = df.drop_duplicates(
        subset=["post_id"],
        keep="first"
    )

    # ------------------------------------------------------------
    # Normalize timestamp
    # ------------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # ------------------------------------------------------------
    # Normalize location
    # ------------------------------------------------------------

    df["location"] = (
        df["location"]
        .replace("", pd.NA)
    )

    # ------------------------------------------------------------
    # Reset index
    # ------------------------------------------------------------

    df = df.reset_index(drop=True)

    return df


if __name__ == "__main__":

    input_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "data/social_media/social_media.csv"
    )

    output_file = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "output/normalized_social_media.csv"
    )

    try:

        normalized_df = normalize_social_media(input_file)

        os.makedirs("output", exist_ok=True)

        normalized_df.to_csv(
            output_file,
            index=False
        )

        print("\n========================================")
        print("SOCIAL MEDIA NORMALIZATION COMPLETE")
        print("========================================")

        print(
            "\nRecords Processed:",
            len(normalized_df)
        )

        print(
            "\nOutput File:",
            output_file
        )

        print("\nNormalized Data:\n")

        print(
            normalized_df.head(10)
        )

    except Exception as e:

        print("\nSOCIAL MEDIA NORMALIZATION FAILED")
        print("Error:", e)