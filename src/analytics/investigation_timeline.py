import os
import pandas as pd


EVIDENCE_FILE = "output/standardized_fir_data.csv"
OUTPUT_FILE = "output/investigation_timeline.csv"


def build_investigation_timeline():

    print("\n==========================================")
    print(" INVESTIGATION TIMELINE")
    print("==========================================\n")

    if not os.path.exists(EVIDENCE_FILE):
        raise FileNotFoundError(
            f"Evidence file not found: {EVIDENCE_FILE}"
        )

    df = pd.read_csv(EVIDENCE_FILE)

    required_columns = [
        "FIR_No",
        "Date_Filed",
        "State",
        "District",
        "Police_Station",
        "Complainant_Name",
        "Accused_Name",
        "Legal_Section",
        "Crime_Category",
        "Incident_Description",
        "Case_Status"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    timeline = df[
        [
            "FIR_No",
            "Date_Filed",
            "State",
            "District",
            "Police_Station",
            "Complainant_Name",
            "Accused_Name",
            "Legal_Section",
            "Crime_Category",
            "Case_Status"
        ]
    ].copy()

    timeline["Date_Filed"] = pd.to_datetime(
        timeline["Date_Filed"],
        errors="coerce"
    )

    timeline = timeline.dropna(
        subset=["Date_Filed"]
    )

    timeline = timeline.sort_values(
        by="Date_Filed"
    )

        # Create timeline events for both complainant and accused.
    accused_timeline = timeline.copy()
    accused_timeline["entity"] = accused_timeline["Accused_Name"]
    accused_timeline["event_type"] = "FIR_REGISTERED_AS_ACCUSED"

    complainant_timeline = timeline.copy()
    complainant_timeline["entity"] = complainant_timeline["Complainant_Name"]
    complainant_timeline["event_type"] = "FIR_REGISTERED_AS_COMPLAINANT"

    timeline = pd.concat(
        [
            accused_timeline,
            complainant_timeline
        ],
        ignore_index=True
    )

    timeline["event_description"] = (
        "FIR "
        + timeline["FIR_No"].astype(str)
        + " registered under "
        + timeline["Legal_Section"].astype(str)
        + " for "
        + timeline["Crime_Category"].astype(str)
    )

    timeline = timeline[
        [
            "entity",
            "FIR_No",
            "Date_Filed",
            "event_type",
            "event_description",
            "State",
            "District",
            "Police_Station",
            "Complainant_Name",
            "Legal_Section",
            "Crime_Category",
            "Case_Status"
        ]
    ]

    timeline = timeline.rename(
        columns={
            "Date_Filed": "event_date",
            "Complainant_Name": "complainant"
        }
    )

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    timeline.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("===== TIMELINE GENERATION COMPLETE =====\n")

    print(
        "Timeline records:",
        len(timeline)
    )

    print(
        "Unique entities:",
        timeline["entity"].nunique()
    )

    print(
        "Date range:",
        timeline["event_date"].min(),
        "to",
        timeline["event_date"].max()
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print("\n==========================================\n")

    return OUTPUT_FILE


if __name__ == "__main__":
    build_investigation_timeline()