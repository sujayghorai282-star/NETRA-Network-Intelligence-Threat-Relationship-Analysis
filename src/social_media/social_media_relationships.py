import pandas as pd
import os
import re


def split_values(value):
    """
    Split comma/semicolon/pipe separated values into clean items.
    """

    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value:
        return []

    parts = re.split(r"[,;|]", value)

    return [
        item.strip()
        for item in parts
        if item.strip()
    ]


def extract_social_media_relationships(df):
    """
    Extract evidence-supported relationships from normalized
    social media records.

    Relationship schema:
        source
        relationship
        target
    """

    relationships = []

    for _, row in df.iterrows():

        user_id = str(row.get("user_id", "")).strip()
        username = str(row.get("username", "")).strip()
        post_id = str(row.get("post_id", "")).strip()
        location = str(row.get("location", "")).strip()

        # Prefer username as the visible investigation entity.
        # Fall back to user_id if username is unavailable.
        user = username if username else user_id

        if not user:
            continue

        # --------------------------------------------------------
        # USER -> POST
        # --------------------------------------------------------

        if post_id:
            relationships.append({
                "source": user,
                "relationship": "POSTS",
                "target": post_id
            })

        # --------------------------------------------------------
        # USER -> LOCATION
        # --------------------------------------------------------

        if location and location.lower() not in {
            "nan",
            "unknown",
            "none",
            "null"
        }:
            relationships.append({
                "source": user,
                "relationship": "LOCATED_IN",
                "target": location
            })

        # --------------------------------------------------------
        # USER -> MENTIONED USER
        # --------------------------------------------------------

        mentions = split_values(
            row.get("mentions", "")
        )

        for mentioned_user in mentions:

            mentioned_user = mentioned_user.lstrip("@").strip()

            if not mentioned_user:
                continue

            if mentioned_user == user:
                continue

            relationships.append({
                "source": user,
                "relationship": "MENTIONS",
                "target": mentioned_user
            })

        # --------------------------------------------------------
        # USER -> HASHTAG
        # --------------------------------------------------------

        hashtags = split_values(
            row.get("hashtags", "")
        )

        for hashtag in hashtags:

            hashtag = hashtag.strip()

            if not hashtag:
                continue

            if not hashtag.startswith("#"):
                hashtag = "#" + hashtag

            relationships.append({
                "source": user,
                "relationship": "USES_HASHTAG",
                "target": hashtag
            })

        # --------------------------------------------------------
        # USER -> ORGANIZATION
        # --------------------------------------------------------

        organizations = split_values(
            row.get("organizations", "")
        )

        for organization in organizations:

            organization = organization.strip()

            if not organization:
                continue

            relationships.append({
                "source": user,
                "relationship": "REFERENCES",
                "target": organization
            })

    return relationships


def save_social_media_relationships(
    relationships,
    output_file="output/social_media_relationships.csv"
):
    """
    Save social media relationships using the same
    relationship structure used by the existing FIR pipeline.
    """

    os.makedirs(
        os.path.dirname(output_file),
        exist_ok=True
    )

    relationships_df = pd.DataFrame(
        relationships,
        columns=[
            "source",
            "relationship",
            "target"
        ]
    )

    relationships_df.to_csv(
        output_file,
        index=False
    )

    return relationships_df


if __name__ == "__main__":

    input_file = "output/normalized_social_media.csv"

    try:

        df = pd.read_csv(input_file)

        relationships = extract_social_media_relationships(df)

        relationships_df = save_social_media_relationships(
            relationships
        )

        print("\n========================================")
        print("SOCIAL MEDIA RELATIONSHIP EXTRACTION")
        print("========================================")

        print(
            "\nRecords Processed:",
            len(df)
        )

        print(
            "Relationships Extracted:",
            len(relationships_df)
        )

        print("\nExtracted Relationships:\n")

        if not relationships_df.empty:
            print(
                relationships_df.head(20)
            )
        else:
            print(
                "No relationships found."
            )

        print("\n========================================")
        print("SOCIAL MEDIA RELATIONSHIPS SAVED")
        print("========================================")

        print(
            "Output File:",
            "output/social_media_relationships.csv"
        )

    except Exception as e:

        print(
            "\nSOCIAL MEDIA RELATIONSHIP EXTRACTION FAILED"
        )

        print(
            "Error:",
            e
        )