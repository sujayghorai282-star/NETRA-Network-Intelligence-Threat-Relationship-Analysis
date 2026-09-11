import os
import pandas as pd

PROFILE_FILE = "output/entity_profiles.csv"
EVIDENCE_FILE = "output/evidence_index.csv"
TRACE_FILE = "output/evidence_traceability.csv"
RISK_FILE = "output/risk_analysis.csv"

OUTPUT_FILE = "output/investigation_context.csv"


print("\n==========================================")
print(" INVESTIGATION CONTEXT BUILDER")
print("==========================================\n")


def load_file(path, required=True):

    if not os.path.exists(path):

        if required:
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

        return None

    return pd.read_csv(path)


def find_column(df, possible_names):

    for name in possible_names:

        if name in df.columns:
            return name

    return None


def build_context():

    print("Loading investigation intelligence...")

    profiles = load_file(PROFILE_FILE)
    evidence = load_file(EVIDENCE_FILE)
    traceability = load_file(TRACE_FILE)

    # Risk analysis is optional for this layer.
    risk = load_file(
        RISK_FILE,
        required=False
    )

    print("Entity profiles:", len(profiles))
    print("Evidence index:", len(evidence))
    print("Traceability records:", len(traceability))

    if risk is not None:
        print("Risk records:", len(risk))
    else:
        print("Risk analysis: not available")

    # --------------------------------------------------
    # STANDARDIZE ENTITY COLUMN
    # --------------------------------------------------

    profile_entity_col = find_column(
        profiles,
        ["entity", "entity_name"]
    )

    evidence_entity_col = find_column(
        evidence,
        ["entity", "entity_name"]
    )

    if profile_entity_col is None:
        raise ValueError(
            "Entity column missing from entity profiles."
        )

    if evidence_entity_col is None:
        raise ValueError(
            "Entity column missing from evidence index."
        )

    # --------------------------------------------------
    # PREPARE PROFILE DATA
    # --------------------------------------------------

    profile_columns = [
        "entity",
        "entity_type",
        "evidence_count",
        "relationship_count",
        "connected_entity_count"
    ]

    available_profile_columns = [
        column
        for column in profile_columns
        if column in profiles.columns
    ]

    profile_data = profiles[
        available_profile_columns
    ].copy()

    # --------------------------------------------------
    # PREPARE EVIDENCE DATA
    # --------------------------------------------------

    evidence_columns = [
        "entity",
        "evidence_count",
        "evidence_records",
        "relationship_types",
        "connected_entity_count",
        "connected_entities"
    ]

    available_evidence_columns = [
        column
        for column in evidence_columns
        if column in evidence.columns
    ]

    evidence_data = evidence[
        available_evidence_columns
    ].copy()

    # Avoid duplicate column names after merge.
    evidence_data = evidence_data.rename(
        columns={
            "evidence_count": "indexed_evidence_count",
            "connected_entity_count":
                "indexed_connected_entity_count"
        }
    )

    # --------------------------------------------------
    # MERGE PROFILE + EVIDENCE
    # --------------------------------------------------

    print("\n==========================================")
    print(" MERGING INVESTIGATION DATA")
    print("==========================================")

    context = profile_data.merge(
        evidence_data,
        on="entity",
        how="left"
    )

    # --------------------------------------------------
    # ADD RISK INTELLIGENCE
    # --------------------------------------------------

    if risk is not None:

        risk_entity_col = find_column(
            risk,
            ["entity", "entity_name"]
        )

        if risk_entity_col is not None:

            risk_columns = [
                risk_entity_col,
                "risk_score",
                "risk_level",
                "connections",
                "fir_count",
                "direct_complainants",
                "investigative_connections"
            ]

            available_risk_columns = [
                column
                for column in risk_columns
                if column in risk.columns
            ]

            risk_data = risk[
                available_risk_columns
            ].copy()

            if risk_entity_col != "entity":

                risk_data = risk_data.rename(
                    columns={
                        risk_entity_col: "entity"
                    }
                )

            context = context.merge(
                risk_data,
                on="entity",
                how="left"
            )

    # --------------------------------------------------
    # TRACEABILITY STATISTICS
    # --------------------------------------------------

    print("\n==========================================")
    print(" BUILDING TRACEABILITY SUMMARY")
    print("==========================================")

    trace_entity_data = []

    if not traceability.empty:

        source_col = find_column(
            traceability,
            ["source", "entity_a"]
        )

        target_col = find_column(
            traceability,
            ["target", "entity_b"]
        )

        record_col = find_column(
            traceability,
            ["record_id", "evidence_record"]
        )

        if source_col and target_col and record_col:

            source_trace = traceability[
                [source_col, record_col]
            ].copy()

            source_trace.columns = [
                "entity",
                "trace_record_id"
            ]

            target_trace = traceability[
                [target_col, record_col]
            ].copy()

            target_trace.columns = [
                "entity",
                "trace_record_id"
            ]

            combined_trace = pd.concat(
                [
                    source_trace,
                    target_trace
                ],
                ignore_index=True
            )

            trace_summary = (
                combined_trace
                .groupby("entity")["trace_record_id"]
                .nunique()
                .reset_index()
            )

            trace_summary = trace_summary.rename(
                columns={
                    "trace_record_id":
                        "traceable_evidence_count"
                }
            )

            context = context.merge(
                trace_summary,
                on="entity",
                how="left"
            )

    # --------------------------------------------------
    # CLEAN NUMERIC VALUES
    # --------------------------------------------------

    numeric_columns = [
        "evidence_count",
        "relationship_count",
        "connected_entity_count",
        "indexed_evidence_count",
        "indexed_connected_entity_count",
        "risk_score",
        "connections",
        "fir_count",
        "direct_complainants",
        "investigative_connections",
        "traceable_evidence_count"
    ]

    for column in numeric_columns:

        if column in context.columns:

            context[column] = pd.to_numeric(
                context[column],
                errors="coerce"
            ).fillna(0)

    # --------------------------------------------------
    # QUALITY CHECK
    # --------------------------------------------------

    print("\n==========================================")
    print(" CONTEXT QUALITY CHECK")
    print("==========================================")

    print(
        "Investigation entities:",
        len(context)
    )

    print(
        "Missing entity names:",
        context["entity"].isna().sum()
    )

    if "entity_type" in context.columns:

        print(
            "Missing entity types:",
            context["entity_type"].isna().sum()
        )

    if "traceable_evidence_count" in context.columns:

        print(
            "Entities with traceability:",
            (
                context["traceable_evidence_count"] > 0
            ).sum()
        )

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    print("\n==========================================")
    print(" SAVING INVESTIGATION CONTEXT")
    print("==========================================")

    os.makedirs("output", exist_ok=True)

    context.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nOutput:")
    print(OUTPUT_FILE)

    return context


def main():

    context = build_context()

    # --------------------------------------------------
    # TEST WITH KNOWN ENTITY
    # --------------------------------------------------

    test_entity = "Ganga Dyal"

    print("\n==========================================")
    print(" CONTEXT TEST")
    print("==========================================")

    result = context[
        context["entity"].astype(str).str.lower()
        == test_entity.lower()
    ]

    if result.empty:

        print(
            f"Entity not found: {test_entity}"
        )

    else:

        row = result.iloc[0]

        print("\nEntity:", row["entity"])

        if "entity_type" in row:
            print(
                "Entity Type:",
                row["entity_type"]
            )

        if "evidence_count" in row:
            print(
                "Evidence Count:",
                row["evidence_count"]
            )

        if "relationship_count" in row:
            print(
                "Relationship Count:",
                row["relationship_count"]
            )

        if "connected_entity_count" in row:
            print(
                "Connected Entities:",
                row["connected_entity_count"]
            )

        if "risk_score" in row:
            print(
                "Risk Score:",
                row["risk_score"]
            )

        if "risk_level" in row:
            print(
                "Risk Level:",
                row["risk_level"]
            )

        if "traceable_evidence_count" in row:
            print(
                "Traceable Evidence:",
                row["traceable_evidence_count"]
            )

    print("\n==========================================")
    print(" INVESTIGATION CONTEXT BUILD COMPLETE")
    print("==========================================")


if __name__ == "__main__":
    main()