import os
import re
from difflib import SequenceMatcher

import pandas as pd


# ================================================================
# CONFIGURATION
# ================================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "output"
)

CONTEXT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "investigation_context.csv"
)

EVIDENCE_FILE = os.path.join(
    OUTPUT_FOLDER,
    "standardized_fir_data.csv"
)

CONNECTION_FILE = os.path.join(
    OUTPUT_FOLDER,
    "investigative_entity_connections.csv"
)

RISK_FILE = os.path.join(
    OUTPUT_FOLDER,
    "risk_analysis.csv"
)

RELATIONSHIP_FILE = os.path.join(
    OUTPUT_FOLDER,
    "extracted_relationships.csv"
)
SOCIAL_MEDIA_RELATIONSHIP_FILE = os.path.join(
    OUTPUT_FOLDER,
    "social_media_relationships.csv"
)


class InvestigationAssistant:
    """
    Investigation-focused query engine.

    Responsibilities:
    - Resolve entities using exact and fuzzy matching.
    - Retrieve investigation context.
    - Retrieve standardized evidence/FIR records.
    - Retrieve investigative connections.
    - Use relationship graph as a fallback.
    - Answer common natural-language investigation questions.
    - Search other CSV datasets when a specialized answer is unavailable.

    Important:
    Risk scores are analytical prioritization indicators only.
    They are not determinations of guilt.
    """

    # ------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------

    def __init__(self):

        self.context_df = self._load_file(
            CONTEXT_FILE
        )

        self.evidence_df = self._load_file(
            EVIDENCE_FILE
        )

        self.connection_df = self._load_file(
            CONNECTION_FILE
        )

        self.risk_df = self._load_file(
            RISK_FILE
        )

        self.relationship_df = self._load_file(
    RELATIONSHIP_FILE
)

# ------------------------------------------------------------
# LOAD ALL OUTPUT DATASETS
# ------------------------------------------------------------

        self.output_data = {}

        if os.path.exists(OUTPUT_FOLDER):

            for filename in os.listdir(OUTPUT_FOLDER):

                if not filename.lower().endswith(".csv"):
                    continue

                filepath = os.path.join(
                    OUTPUT_FOLDER,
                    filename
                )

                dataframe = self._load_file(
                    filepath
                )

                if not dataframe.empty:
                    self.output_data[
                        filename
                    ] = dataframe

        self.dataset_cache = {}

        self.entity_names = (
            self._collect_entity_names()
        )

    # ------------------------------------------------------------
    # FILE LOADING
    # ------------------------------------------------------------

    def _load_file(
        self,
        filepath
    ):

        try:

            if not os.path.exists(
                filepath
            ):
                return pd.DataFrame()

            df = pd.read_csv(
                filepath,
                low_memory=False
            )

            df.columns = [
                str(column).strip()
                for column in df.columns
            ]

            return df

        except Exception:

            return pd.DataFrame()

    # ------------------------------------------------------------
    # NORMALIZATION
    # ------------------------------------------------------------

    def _normalize_text(
        self,
        value
    ):

        if value is None:
            return ""

        try:

            if pd.isna(value):
                return ""

        except Exception:
            pass

        text = str(
            value
        ).strip().lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # ------------------------------------------------------------
    # ENTITY NAME COLLECTION
    # ------------------------------------------------------------

    def _collect_entity_names(
        self
    ):

        names = set()

        dataframes = [
            self.context_df,
            self.evidence_df,
            self.connection_df,
            self.risk_df,
            self.relationship_df
        ]

        preferred_columns = [
            "entity",
            "Entity",
            "entity_name",
            "Entity_Name",
            "name",
            "Name",
            "person",
            "Person",
            "person_name",
            "Person_Name",
            "source",
            "target"
        ]

        for df in dataframes:

            if df.empty:
                continue

            for column in preferred_columns:

                if column not in df.columns:
                    continue

                values = (
                    df[column]
                    .dropna()
                    .astype(str)
                    .str.strip()
                )

                for value in values:

                    if not value:
                        continue

                    normalized = (
                        self._normalize_text(
                            value
                        )
                    )

                    if (
                        normalized
                        and len(normalized) > 1
                    ):
                        names.add(
                            value
                        )

        return sorted(
            names
        )

    # ------------------------------------------------------------
    # ENTITY RESOLUTION
    # ------------------------------------------------------------

    def resolve_entity(
        self,
        entity_name
    ):

        if entity_name is None:
            return ""

        original = str(
            entity_name
        ).strip()

        if not original:
            return ""

        normalized = (
            self._normalize_text(
                original
            )
        )

        if not normalized:
            return original
        # Use the current candidate pool so newly integrated
        # evidence sources such as Social Media are included.
        candidates = self._candidate_entities()

        # Exact normalized match
        for candidate in candidates:

            if (
                self._normalize_text(
                    candidate
                )
                == normalized
            ):
                return candidate

        # Token based match
        normalized_tokens = set(
            normalized.split()
        )

        if normalized_tokens:

            for candidate in self.entity_names:

                candidate_normalized = (
                    self._normalize_text(
                        candidate
                    )
                )

                candidate_tokens = set(
                    candidate_normalized.split()
                )

                if (
                    normalized_tokens
                    and candidate_tokens
                    and normalized_tokens
                    == candidate_tokens
                ):
                    return candidate

        # Fuzzy matching
        best_candidate = None
        best_score = 0.0

        for candidate in self.entity_names:

            candidate_normalized = (
                self._normalize_text(
                    candidate
                )
            )

            if not candidate_normalized:
                continue

            score = SequenceMatcher(
                None,
                normalized,
                candidate_normalized
            ).ratio()

            if score > best_score:

                best_score = score
                best_candidate = candidate

        if (
            best_candidate is not None
            and best_score >= 0.78
        ):
            return best_candidate

        return original

    # ------------------------------------------------------------
    # DATAFRAME ENTITY MATCHING
    # ------------------------------------------------------------

    def _entity_matches_dataframe(
        self,
        df,
        entity_name
    ):

        if df.empty:
            return pd.DataFrame()

        normalized_entity = (
            self._normalize_text(
                entity_name
            )
        )

        if not normalized_entity:
            return pd.DataFrame()

        possible_columns = [
            "entity",
            "Entity",
            "entity_name",
            "Entity_Name",
            "name",
            "Name",
            "person",
            "Person",
            "person_name",
            "Person_Name",
            "source",
            "target",
            "complainant",
            "Complainant",
            "Complainant_Name",
            "accused",
            "Accused",
            "Accused_Name",
            "victim",
            "Victim"
                    ]

        available_columns = [
            column
            for column in possible_columns
            if column in df.columns
        ]

        if not available_columns:
            return pd.DataFrame()

        mask = pd.Series(
            False,
            index=df.index
        )

        for column in available_columns:

            column_values = (
                df[column]
                .fillna("")
                .astype(str)
                .map(
                    self._normalize_text
                )
            )

            exact_mask = (
                column_values
                == normalized_entity
            )

            contains_mask = (
                column_values
                .str.contains(
                    re.escape(
                        normalized_entity
                    ),
                    regex=True,
                    na=False
                )
            )

            mask = (
                mask
                | exact_mask
                | contains_mask
            )

        return df.loc[
            mask
        ].copy()

    # ------------------------------------------------------------
    # INVESTIGATION SUMMARY
    # ------------------------------------------------------------

    def get_investigation_summary(
        self,
        entity_name
    ):

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        if not resolved_entity:

            return {
                "found": False,
                "entity": "",
                "risk_score": 0.0,
                "risk_level": "UNKNOWN",
                "evidence_count": 0,
                "relationship_count": 0,
                "summary": (
                    "No entity was provided."
                )
            }

        context_matches = (
            self._entity_matches_dataframe(
                self.context_df,
                resolved_entity
            )
        )

        evidence_matches = (
            self._entity_matches_dataframe(
                self.evidence_df,
                resolved_entity
            )
        )

        connection_matches = (
            self._entity_matches_dataframe(
                self.connection_df,
                resolved_entity
            )
        )

        risk_matches = (
            self._entity_matches_dataframe(
                self.risk_df,
                resolved_entity
            )
        )

        relationship_matches = (
            self._entity_matches_dataframe(
                self.relationship_df,
                resolved_entity
            )
        )

        found = any(
            not df.empty
            for df in [
                context_matches,
                evidence_matches,
                connection_matches,
                risk_matches,
                relationship_matches
            ]
        )

        risk_score = self._extract_risk_score(
            risk_matches,
            context_matches
        )

        risk_level = self._extract_risk_level(
            risk_matches,
            context_matches,
            risk_score
        )

        evidence_count = (
            self._count_evidence_records(
                evidence_matches,
                context_matches
            )
        )

        relationship_count = (
            self._count_relationships(
                relationship_matches,
                connection_matches
            )
        )

        summary = (
            f"{resolved_entity} is recorded "
            f"as an investigation entity with "
            f"{evidence_count} linked evidence "
            f"record(s). The investigation context "
            f"contains {relationship_count} "
            f"relationship(s). The calculated risk "
            f"score is {risk_score:.2f}, classified "
            f"as {risk_level}."
        )

        return {
            "found": found,
            "entity": resolved_entity,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "evidence_count": evidence_count,
            "relationship_count": relationship_count,
            "summary": summary
        }

    # ------------------------------------------------------------
    # RISK SCORE EXTRACTION
    # ------------------------------------------------------------

    def _extract_risk_score(
        self,
        risk_df,
        context_df
    ):

        candidate_columns = [
            "risk_score",
            "Risk_Score",
            "risk",
            "Risk",
            "score",
            "Score",
            "calculated_risk_score",
            "Calculated_Risk_Score"
        ]

        for df in [
            risk_df,
            context_df
        ]:

            if df.empty:
                continue

            for column in candidate_columns:

                if column not in df.columns:
                    continue

                values = (
                    pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )
                    .dropna()
                )

                if not values.empty:

                    return float(
                        values.iloc[0]
                    )

        return 0.0

    # ------------------------------------------------------------
    # RISK LEVEL EXTRACTION
    # ------------------------------------------------------------

    def _extract_risk_level(
        self,
        risk_df,
        context_df,
        risk_score
    ):

        candidate_columns = [
            "risk_level",
            "Risk_Level",
            "risk_category",
            "Risk_Category",
            "severity",
            "Severity",
            "classification",
            "Classification"
        ]

        for df in [
            risk_df,
            context_df
        ]:

            if df.empty:
                continue

            for column in candidate_columns:

                if column not in df.columns:
                    continue

                values = (
                    df[column]
                    .dropna()
                    .astype(str)
                    .str.strip()
                )

                if not values.empty:

                    value = values.iloc[0]

                    if value:
                        return value.upper()

        # Conservative fallback
        if risk_score >= 70:
            return "HIGH"

        if risk_score >= 40:
            return "MEDIUM"

        if risk_score > 0:
            return "LOW"

        return "UNKNOWN"

    # ------------------------------------------------------------
    # EVIDENCE COUNT
    # ------------------------------------------------------------

    def _count_evidence_records(
        self,
        evidence_df,
        context_df
    ):

        if not evidence_df.empty:

            if "FIR_No" in evidence_df.columns:

                values = (
                    evidence_df[
                        "FIR_No"
                    ]
                    .dropna()
                    .astype(str)
                    .str.strip()
                )

                values = values[
                    values != ""
                ]

                if not values.empty:

                    return int(
                        values.nunique()
                    )

            return int(
                len(evidence_df)
            )

        if not context_df.empty:

            for column in [
                "evidence_count",
                "Evidence_Count",
                "fir_count",
                "FIR_Count",
                "case_count",
                "Case_Count"
            ]:

                if column in context_df.columns:

                    values = (
                        pd.to_numeric(
                            context_df[column],
                            errors="coerce"
                        )
                        .dropna()
                    )

                    if not values.empty:

                        return int(
                            values.iloc[0]
                        )

        return 0

    # ------------------------------------------------------------
    # RELATIONSHIP COUNT
    # ------------------------------------------------------------

    def _count_relationships(
        self,
        relationship_df,
        connection_df
    ):

        if not relationship_df.empty:
            return int(
                len(
                    relationship_df
                )
            )

        if not connection_df.empty:

            for column in [
                "investigative_connections",
                "Investigative_Connections",
                "relationship_count",
                "Relationship_Count",
                "connection_count",
                "Connection_Count"
            ]:

                if column in connection_df.columns:

                    values = (
                        pd.to_numeric(
                            connection_df[column],
                            errors="coerce"
                        )
                        .dropna()
                    )

                    if not values.empty:

                        return int(
                            values.iloc[0]
                        )

            return int(
                len(connection_df)
            )

        return 0
    # ------------------------------------------------------------
    # RELATIONSHIP GRAPH
    # ------------------------------------------------------------

    def _get_relationships(
        self,
        entity_name
    ):
        fir_relationships = pd.DataFrame()

        if not self.relationship_df.empty:

            source_column = (
                "source"
                if "source" in self.relationship_df.columns
                else "Source"
                if "Source" in self.relationship_df.columns
                else None
            )

            target_column = (
                "target"
                if "target" in self.relationship_df.columns
                else "Target"
                if "Target" in self.relationship_df.columns
                else None
            )

            if source_column and target_column:

                resolved_entity = (
                    self.resolve_entity(
                        entity_name
                    )
                )

                normalized = (
                    self._normalize_text(
                        resolved_entity
                    )
                )

                source_values = (
                    self.relationship_df[
                        source_column
                    ]
                    .astype(str)
                    .map(
                        self._normalize_text
                    )
                )

                target_values = (
                    self.relationship_df[
                        target_column
                    ]
                    .astype(str)
                    .map(
                        self._normalize_text
                    )
                )

                mask = (
                    source_values.eq(normalized)
                    |
                    target_values.eq(normalized)
                )

                fir_relationships = (
                    self.relationship_df[
                        mask
                    ].copy()
                )

        # --------------------------------------------------------
        # SOCIAL MEDIA RELATIONSHIPS
        # --------------------------------------------------------

        social_relationships = pd.DataFrame()

        social_df = self.output_data.get(
            "social_media_relationships.csv",
            pd.DataFrame()
        )

        if (
            not social_df.empty
            and "source" in social_df.columns
            and "target" in social_df.columns
            and "relationship" in social_df.columns
        ):

            # Only explicit user-to-user mentions are treated
            # as direct Social Media connections.
            social_mentions = social_df[
                social_df["relationship"]
                .astype(str)
                .str.strip()
                .str.upper()
                == "MENTIONS"
            ].copy()

            if not social_mentions.empty:

                resolved_entity = (
                    self.resolve_entity(
                        entity_name
                    )
                )

                normalized = (
                    self._normalize_text(
                        resolved_entity
                    )
                )

                social_source_values = (
                    social_mentions["source"]
                    .astype(str)
                    .map(
                        self._normalize_text
                    )
                )

                social_target_values = (
                    social_mentions["target"]
                    .astype(str)
                    .map(
                        self._normalize_text
                    )
                )

                social_mask = (
                    social_source_values.eq(normalized)
                    |
                    social_target_values.eq(normalized)
                )

                social_relationships = (
                    social_mentions[
                        social_mask
                    ].copy()
                )

        # --------------------------------------------------------
        # COMBINE FIR + SOCIAL MEDIA RELATIONSHIPS
        # --------------------------------------------------------

        if (
            fir_relationships.empty
            and social_relationships.empty
        ):
            return pd.DataFrame()

        return pd.concat(
            [
                fir_relationships,
                social_relationships
            ],
            ignore_index=True
        )
    # ------------------------------------------------------------
    # FIND RELEVANT COLUMNS
    # ------------------------------------------------------------

    def _find_relevant_columns(
        self,
        df,
        question
    ):

        if df.empty:
            return []

        question_normalized = (
            self._normalize_text(
                question
            )
        )

        tokens = set(
            question_normalized.split()
        )

        results = []

        aliases = {
            "risk": [
                "risk",
                "danger",
                "priority",
                "threat"
            ],
            "case": [
                "case",
                "cases",
                "fir",
                "report",
                "reports"
            ],
            "crime": [
                "crime",
                "criminal",
                "offence",
                "offense"
            ],
            "location": [
                "location",
                "city",
                "state",
                "district",
                "place",
                "where",
                "address"
            ],
            "time": [
                "year",
                "date",
                "when",
                "time",
                "timeline"
            ],
            "severity": [
                "severity",
                "serious",
                "seriousness"
            ],
            "connections": [
                "connection",
                "connections",
                "linked",
                "relationship",
                "relationships",
                "associate",
                "associates"
            ],
            "prior": [
                "prior",
                "previous",
                "history",
                "past"
            ]
        }

        for column in df.columns:

            normalized_column = (
                self._normalize_text(
                    column
                )
            )

            column_tokens = set(
                normalized_column.split()
            )

            score = len(
                tokens & column_tokens
            )

            for alias_words in aliases.values():

                if (
                    tokens
                    & set(alias_words)
                    and any(
                        word in normalized_column
                        for word in alias_words
                    )
                ):
                    score += 2

            if score > 0:
                results.append(
                    (
                        column,
                        score
                    )
                )

        results.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return [
            column
            for column, score in results[:5]
        ]

    # ------------------------------------------------------------
    # GENERIC DATASET SEARCH
    # ------------------------------------------------------------

    def _search_all_data(
        self,
        question
    ):

        results = []

        for filename, df in (
            self.output_data.items()
        ):

            if df.empty:
                continue

            relevant_columns = (
                self._find_relevant_columns(
                    df,
                    question
                )
            )

            if relevant_columns:

                results.append(
                    (
                        filename,
                        df,
                        relevant_columns
                    )
                )

        return results

    # ------------------------------------------------------------
    # QUESTION CLASSIFICATION
    # ------------------------------------------------------------

    def _question_type(
        self,
        question
    ):

        q = self._normalize_text(
            question
        )

        if not q:
            return "summary"

        # --------------------------------------------------------
        # RISK
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "risk",
                "danger",
                "priority",
                "threat"
            ]
        ):

            return "risk"

        # --------------------------------------------------------
        # CONNECTIONS
        # --------------------------------------------------------

        if any(
            phrase in q
            for phrase in [
                "who is",
                "who are",
                "who was",
                "who were",
                "whom"
            ]
        ) and any(
            word in q
            for word in [
                "connected",
                "connection",
                "connections",
                "relationship",
                "relationships",
                "associate",
                "associates",
                "linked"
            ]
        ):

            return "connections"

        # --------------------------------------------------------
        # COUNT
        # --------------------------------------------------------

        if any(
            phrase in q
            for phrase in [
                "how many cases",
                "number of cases",
                "total cases",
                "how many fir",
                "number of fir",
                "total fir",
                "how many records",
                "number of records",
                "total records",
                "how many evidence"
            ]
        ):

            return "count"

        # --------------------------------------------------------
        # LOCATION
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "where",
                "city",
                "state",
                "district",
                "location",
                "located",
                "address",
                "place"
            ]
        ):

            return "location"

        # --------------------------------------------------------
        # TIME
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "when",
                "year",
                "date",
                "timeline",
                "time"
            ]
        ):

            return "time"

        # --------------------------------------------------------
        # GENERAL COUNT
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "how many",
                "count",
                "number",
                "total"
            ]
        ):

            return "count"

        # --------------------------------------------------------
        # EVIDENCE
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "evidence",
                "fir",
                "case",
                "report",
                "record",
                "proof"
            ]
        ):

            return "evidence"

        # --------------------------------------------------------
        # CRIME
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "crime",
                "crimes",
                "criminal",
                "offence",
                "offense",
                "offences",
                "offenses"
            ]
        ):

            return "crime"

        # --------------------------------------------------------
        # SEVERITY
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "severity",
                "serious",
                "seriousness"
            ]
        ):

            return "severity"

        # --------------------------------------------------------
        # PRIOR HISTORY
        # --------------------------------------------------------

        if any(
            word in q
            for word in [
                "prior",
                "previous",
                "history",
                "past"
            ]
        ):

            return "prior"

        return "summary"

    # ------------------------------------------------------------
    # CLEAN VALUES
    # ------------------------------------------------------------

    def _clean_values(
        self,
        series,
        limit=20
    ):

        if series is None:
            return []

        try:

            values = (
                series
                .dropna()
                .astype(str)
                .str.strip()
            )

        except Exception:

            return []

        values = values[
            values != ""
        ]

        values = (
            values
            .replace(
                "nan",
                pd.NA
            )
            .dropna()
        )

        unique_values = (
            values.unique()
        )

        return [
            str(value).strip()
            for value in unique_values[:limit]
            if str(value).strip()
        ]

    # ------------------------------------------------------------
    # FORMAT VALUES
    # ------------------------------------------------------------

    def _format_values(
        self,
        values
    ):

        if not values:
            return "No information available."

        return ", ".join(
            str(value)
            for value in values
        )

    # ------------------------------------------------------------
    # SIMILARITY
    # ------------------------------------------------------------

    def _similarity(
        self,
        first,
        second
    ):

        first_normalized = (
            self._normalize_text(
                first
            )
        )

        second_normalized = (
            self._normalize_text(
                second
            )
        )

        if not first_normalized:
            return 0.0

        if not second_normalized:
            return 0.0

        if (
            first_normalized
            == second_normalized
        ):
            return 1.0

        return SequenceMatcher(
            None,
            first_normalized,
            second_normalized
        ).ratio()

    # ------------------------------------------------------------
    # CANDIDATE ENTITIES
    # ------------------------------------------------------------

    def _candidate_entities(
        self
    ):

        candidates = set()

        dataframes = [
            self.context_df,
            self.evidence_df,
            self.connection_df,
            self.risk_df,
            self.relationship_df
        ]

        candidate_columns = [
            "entity",
            "Entity",
            "entity_name",
            "Entity_Name",
            "name",
            "Name",
            "person",
            "Person",
            "person_name",
            "Person_Name",
            "Accused_Name",
            "Complainant_Name",
            "source",
            "Source",
            "target",
            "Target"
        ]

        for df in dataframes:

            if df.empty:
                continue

            for column in candidate_columns:

                if column not in df.columns:
                    continue

                try:

                    values = (
                        df[column]
                        .dropna()
                        .astype(str)
                        .str.strip()
                    )

                except Exception:

                    continue

                for value in values:

                    value = str(
                        value
                    ).strip()

                    if not value:
                        continue

                    if value.lower() in {
                        "nan",
                        "none",
                        "null",
                        "unknown"
                    }:
                        continue

                    candidates.add(
                        value
                    )
        # --------------------------------------------------------
        # SOCIAL MEDIA USERS
        # --------------------------------------------------------

        social_df = self.output_data.get(
            "social_media_relationships.csv",
            pd.DataFrame()
        )

        if (
            not social_df.empty
            and "source" in social_df.columns
        ):

            # Every relationship source generated by the
            # Social Media pipeline represents a Social Media user.
            for value in (
                social_df["source"]
                .dropna()
                .astype(str)
                .str.strip()
            ):

                if not value:
                    continue

                if value.lower() in {
                    "nan",
                    "none",
                    "null",
                    "unknown"
                }:
                    continue

                candidates.add(
                    value
                )

            # Only explicit MENTIONS targets are treated
            # as additional Social Media user identities.
            if (
                "relationship" in social_df.columns
                and "target" in social_df.columns
            ):

                mention_rows = social_df[
                    social_df["relationship"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    == "MENTIONS"
                ]

                for value in (
                    mention_rows["target"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                ):

                    if not value:
                        continue

                    if value.lower() in {
                        "nan",
                        "none",
                        "null",
                        "unknown"
                    }:
                        continue

                    candidates.add(
                        value
                    )

        return sorted(
            candidates
        )

    # ------------------------------------------------------------
    # ENTITY DATA DESCRIPTION
    # ------------------------------------------------------------

    def _describe_entity_data(
        self,
        entity_name,
        df
    ):

        if df.empty:
            return None

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        lines = []

        for column in df.columns:

            values = (
                self._clean_values(
                    df[column],
                    limit=8
                )
            )

            if not values:
                continue

            formatted = (
                self._format_values(
                    values
                )
            )

            lines.append(
                f"{column}: {formatted}"
            )

        if not lines:
            return None

        return (
            f"Available investigation attributes "
            f"for {resolved_entity}:\n"
            + "\n".join(
                lines
            )
        )

    # ------------------------------------------------------------
    # FIR NUMBER EXTRACTION
    # ------------------------------------------------------------

    def _extract_fir_numbers(
        self,
        df
    ):

        if df.empty:
            return []

        fir_columns = [
            "FIR_No",
            "FIR",
            "FIR_Number",
            "FIR_Number",
            "fir_no",
            "fir_number",
            "Case_ID",
            "case_id",
            "Case_No",
            "case_no"
        ]

        values = []

        for column in fir_columns:

            if column not in df.columns:
                continue

            current = (
                self._clean_values(
                    df[column],
                    limit=100
                )
            )

            values.extend(
                current
            )

        unique_values = []

        for value in values:

            if value not in unique_values:

                unique_values.append(
                    value
                )

        return unique_values

    # ------------------------------------------------------------
    # GENERIC QUESTION DATA
    # ------------------------------------------------------------

    def _question_mentions(
        self,
        question,
        words
    ):

        normalized = (
            self._normalize_text(
                question
            )
        )

        return any(
            word in normalized
            for word in words
        )

    # ------------------------------------------------------------
    # LOCATION EXTRACTION
    # ------------------------------------------------------------

    def _get_location_data(
        self,
        entity_name
    ):

        sources = [
            self.context_df,
            self.evidence_df,
            self.connection_df
        ]

        location_columns = [
            "location",
            "Location",
            "city",
            "City",
            "state",
            "State",
            "district",
            "District",
            "address",
            "Address",
            "place",
            "Place"
        ]

        result = {}

        for df in sources:

            matches = (
                self._entity_matches_dataframe(
                    df,
                    entity_name
                )
            )

            if matches.empty:
                continue

            for column in location_columns:

                if column not in matches.columns:
                    continue

                values = (
                    self._clean_values(
                        matches[column],
                        limit=20
                    )
                )

                if values:
                    result[column] = values

        return result

    # ------------------------------------------------------------
    # TIME DATA
    # ------------------------------------------------------------

    def _get_time_data(
        self,
        entity_name
    ):

        sources = [
            self.context_df,
            self.evidence_df,
            self.connection_df
        ]

        time_columns = [
            "date",
            "Date",
            "year",
            "Year",
            "fir_date",
            "FIR_Date",
            "incident_date",
            "Incident_Date",
            "timestamp",
            "Timestamp",
            "time",
            "Time"
        ]

        result = {}

        for df in sources:

            matches = (
                self._entity_matches_dataframe(
                    df,
                    entity_name
                )
            )

            if matches.empty:
                continue

            for column in time_columns:

                if column not in matches.columns:
                    continue

                values = (
                    self._clean_values(
                        matches[column],
                        limit=20
                    )
                )

                if values:
                    result[column] = values

        return result
    # ------------------------------------------------------------
    # GET EVIDENCE
    # ------------------------------------------------------------

    def get_evidence(
        self,
        entity_name
    ):

        # Existing FIR evidence
        fir_evidence = self._entity_matches_dataframe(
            self.evidence_df,
            entity_name
        )

        # Social Media evidence
        social_media_df = self.output_data.get(
            "normalized_social_media.csv",
            pd.DataFrame()
        )

        social_evidence = pd.DataFrame()

        if not social_media_df.empty:

            normalized_entity = self._normalize_text(
                entity_name
            )

            username_matches = (
                social_media_df["username"]
                .fillna("")
                .astype(str)
                .apply(
                    self._normalize_text
                )
                == normalized_entity
            )

            user_id_matches = (
                social_media_df["user_id"]
                .fillna("")
                .astype(str)
                .apply(
                    self._normalize_text
                )
                == normalized_entity
            )

            social_evidence = social_media_df[
                username_matches | user_id_matches
            ].copy()

        # Combine available evidence sources
        evidence_frames = []

        if not fir_evidence.empty:
            evidence_frames.append(
                fir_evidence
            )

        if not social_evidence.empty:
            evidence_frames.append(
                social_evidence
            )

        if evidence_frames:
            return pd.concat(
                evidence_frames,
                ignore_index=True,
                sort=False
            )

        return pd.DataFrame()

    # ------------------------------------------------------------
    # GET CONNECTIONS
    # ------------------------------------------------------------

    def get_connections(
        self,
        entity_name
    ):

        return self._entity_matches_dataframe(
            self.connection_df,
            entity_name
        )

    # ------------------------------------------------------------
    # GET RISK DATA
    # ------------------------------------------------------------

    def get_risk_data(
        self,
        entity_name
    ):

        return self._entity_matches_dataframe(
            self.risk_df,
            entity_name
        )

    # ------------------------------------------------------------
    # GET CONTEXT
    # ------------------------------------------------------------

    def get_context(
        self,
        entity_name
    ):

        return self._entity_matches_dataframe(
            self.context_df,
            entity_name
        )

    # ------------------------------------------------------------
    # GET CRIME DATA
    # ------------------------------------------------------------

    def _get_crime_data(
        self,
        entity_name
    ):

        sources = [
            self.evidence_df,
            self.context_df,
            self.connection_df
        ]

        crime_columns = [
            "crime",
            "Crime",
            "crime_type",
            "Crime_Type",
            "offence",
            "Offence",
            "offense",
            "Offense",
            "offence_type",
            "Offence_Type",
            "offense_type",
            "Offense_Type",
            "crime_category",
            "Crime_Category",
            "section",
            "Section",
            "ipc_section",
            "IPC_Section"
        ]

        result = {}

        for df in sources:

            matches = (
                self._entity_matches_dataframe(
                    df,
                    entity_name
                )
            )

            if matches.empty:
                continue

            for column in crime_columns:

                if column not in matches.columns:
                    continue

                values = (
                    self._clean_values(
                        matches[column],
                        limit=30
                    )
                )

                if values:
                    result[column] = values

        return result

    # ------------------------------------------------------------
    # GET SEVERITY DATA
    # ------------------------------------------------------------

    def _get_severity_data(
        self,
        entity_name
    ):

        sources = [
            self.risk_df,
            self.context_df,
            self.evidence_df
        ]

        severity_columns = [
            "severity",
            "Severity",
            "severity_level",
            "Severity_Level",
            "risk_level",
            "Risk_Level",
            "risk_category",
            "Risk_Category",
            "classification",
            "Classification",
            "priority",
            "Priority"
        ]

        result = {}

        for df in sources:

            matches = (
                self._entity_matches_dataframe(
                    df,
                    entity_name
                )
            )

            if matches.empty:
                continue

            for column in severity_columns:

                if column not in matches.columns:
                    continue

                values = (
                    self._clean_values(
                        matches[column],
                        limit=20
                    )
                )

                if values:
                    result[column] = values

        return result

    # ------------------------------------------------------------
    # PRIOR / HISTORY DATA
    # ------------------------------------------------------------

    def _get_prior_data(
        self,
        entity_name
    ):

        sources = [
            self.evidence_df,
            self.context_df,
            self.connection_df,
            self.risk_df
        ]

        prior_columns = [
            "prior_cases",
            "Prior_Cases",
            "previous_cases",
            "Previous_Cases",
            "past_cases",
            "Past_Cases",
            "criminal_history",
            "Criminal_History",
            "history",
            "History",
            "previous_offences",
            "Previous_Offences",
            "previous_offenses",
            "Previous_Offenses"
        ]

        result = {}

        for df in sources:

            matches = (
                self._entity_matches_dataframe(
                    df,
                    entity_name
                )
            )

            if matches.empty:
                continue

            for column in prior_columns:

                if column not in matches.columns:
                    continue

                values = (
                    self._clean_values(
                        matches[column],
                        limit=20
                    )
                )

                if values:
                    result[column] = values

        return result

    # ------------------------------------------------------------
    # CONNECTION DESCRIPTION
    # ------------------------------------------------------------

    def _describe_connections(
        self,
        entity_name
    ):

        relations = (
            self._get_relationships(
                entity_name
            )
        )

        if relations.empty:
            return None

        source_column = (
            "source"
            if "source" in relations.columns
            else "Source"
            if "Source" in relations.columns
            else None
        )

        target_column = (
            "target"
            if "target" in relations.columns
            else "Target"
            if "Target" in relations.columns
            else None
        )

        relationship_column = (
            "relationship"
            if "relationship" in relations.columns
            else "Relationship"
            if "Relationship" in relations.columns
            else None
        )

        if (
            source_column is None
            or target_column is None
        ):
            return None

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        normalized_entity = (
            self._normalize_text(
                resolved_entity
            )
        )

        connection_lines = []

        for _, row in relations.head(30).iterrows():

            source = str(
                row.get(
                    source_column,
                    ""
                )
            ).strip()

            target = str(
                row.get(
                    target_column,
                    ""
                )
            ).strip()

            relationship = ""

            if relationship_column:
                relationship = str(
                    row.get(
                        relationship_column,
                        ""
                    )
                ).strip()

            source_normalized = (
                self._normalize_text(
                    source
                )
            )

            if (
                source_normalized
                == normalized_entity
            ):

                connected_entity = target

            else:

                connected_entity = source

            if not connected_entity:
                continue

            if relationship:

                connection_lines.append(
                    f"- {connected_entity} "
                    f"({relationship})"
                )

            else:

                connection_lines.append(
                    f"- {connected_entity}"
                )

        if not connection_lines:
            return None

        unique_lines = []

        for line in connection_lines:

            if line not in unique_lines:
                unique_lines.append(
                    line
                )

        return (
            f"Known relationship links for "
            f"{resolved_entity}:\n"
            + "\n".join(
                unique_lines
            )
        )

    # ------------------------------------------------------------
    # UNIQUE CONNECTION ENTITIES
    # ------------------------------------------------------------

    def _get_connected_entities(
        self,
        entity_name
    ):

        relations = (
            self._get_relationships(
                entity_name
            )
        )

        if relations.empty:
            return []

        source_column = (
            "source"
            if "source" in relations.columns
            else "Source"
            if "Source" in relations.columns
            else None
        )

        target_column = (
            "target"
            if "target" in relations.columns
            else "Target"
            if "Target" in relations.columns
            else None
        )

        if (
            source_column is None
            or target_column is None
        ):
            return []

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        normalized_entity = (
            self._normalize_text(
                resolved_entity
            )
        )

        connected = []

        for _, row in relations.iterrows():

            source = str(
                row.get(
                    source_column,
                    ""
                )
            ).strip()

            target = str(
                row.get(
                    target_column,
                    ""
                )
            ).strip()

            if (
                self._normalize_text(
                    source
                )
                == normalized_entity
            ):

                other = target

            elif (
                self._normalize_text(
                    target
                )
                == normalized_entity
            ):

                other = source

            else:

                continue

            if (
                other
                and self._normalize_text(
                    other
                )
                != normalized_entity
            ):
                connected.append(
                    other
                )

        unique_connected = []

        for entity in connected:

            if entity not in unique_connected:
                unique_connected.append(
                    entity
                )

        return unique_connected

    # ------------------------------------------------------------
    # ENTITY LOCATION RESPONSE
    # ------------------------------------------------------------

    def _answer_location(
        self,
        entity_name
    ):

        location_data = (
            self._get_location_data(
                entity_name
            )
        )

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        if not location_data:

            return (
                f"No reliable location information "
                f"was found for {resolved_entity}."
            )

        lines = []

        preferred_order = [
            "City",
            "city",
            "District",
            "district",
            "State",
            "state",
            "Location",
            "location",
            "Place",
            "place",
            "Address",
            "address"
        ]

        used = set()

        for column in preferred_order:

            if column not in location_data:
                continue

            values = location_data[
                column
            ]

            lines.append(
                f"{column}: "
                f"{self._format_values(values)}"
            )

            used.add(
                column
            )

        for column, values in location_data.items():

            if column in used:
                continue

            lines.append(
                f"{column}: "
                f"{self._format_values(values)}"
            )

        return (
            f"Location information for "
            f"{resolved_entity}:\n"
            + "\n".join(
                lines
            )
        )

    # ------------------------------------------------------------
    # ENTITY TIME RESPONSE
    # ------------------------------------------------------------

    def _answer_time(
        self,
        entity_name
    ):

        time_data = (
            self._get_time_data(
                entity_name
            )
        )

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        if not time_data:

            return (
                f"No reliable date or timeline "
                f"information was found for "
                f"{resolved_entity}."
            )

        lines = []

        for column, values in time_data.items():

            lines.append(
                f"{column}: "
                f"{self._format_values(values)}"
            )

        return (
            f"Timeline information for "
            f"{resolved_entity}:\n"
            + "\n".join(
                lines
            )
        )

    # ------------------------------------------------------------
    # ENTITY CRIME RESPONSE
    # ------------------------------------------------------------

    def _answer_crime(
        self,
        entity_name
    ):

        crime_data = (
            self._get_crime_data(
                entity_name
            )
        )

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        if not crime_data:

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            if not evidence.empty:

                description = (
                    self._describe_entity_data(
                        resolved_entity,
                        evidence
                    )
                )

                if description:
                    return description

            return (
                f"No specific crime or offence "
                f"information was found for "
                f"{resolved_entity}."
            )

        lines = []

        for column, values in crime_data.items():

            lines.append(
                f"{column}: "
                f"{self._format_values(values)}"
            )

        return (
            f"Crime/offence information for "
            f"{resolved_entity}:\n"
            + "\n".join(
                lines
            )
        )

    # ------------------------------------------------------------
    # ENTITY SEVERITY RESPONSE
    # ------------------------------------------------------------

    def _answer_severity(
        self,
        entity_name
    ):

        severity_data = (
            self._get_severity_data(
                entity_name
            )
        )

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        investigation = (
            self.get_investigation_summary(
                resolved_entity
            )
        )

        if severity_data:

            lines = []

            for column, values in (
                severity_data.items()
            ):

                lines.append(
                    f"{column}: "
                    f"{self._format_values(values)}"
                )

            return (
                f"Severity/risk information for "
                f"{resolved_entity}:\n"
                + "\n".join(
                    lines
                )
            )

        if investigation["found"]:

            return (
                f"{resolved_entity} has a calculated "
                f"risk score of "
                f"{investigation['risk_score']:.2f} "
                f"and is classified as "
                f"{investigation['risk_level']}."
            )

        return (
            f"No severity information was found "
            f"for {resolved_entity}."
        )

    # ------------------------------------------------------------
    # PRIOR HISTORY RESPONSE
    # ------------------------------------------------------------

    def _answer_prior(
        self,
        entity_name
    ):

        prior_data = (
            self._get_prior_data(
                entity_name
            )
        )

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        evidence = (
            self.get_evidence(
                resolved_entity
            )
        )

        if prior_data:

            lines = []

            for column, values in prior_data.items():

                lines.append(
                    f"{column}: "
                    f"{self._format_values(values)}"
                )

            return (
                f"Prior/history information for "
                f"{resolved_entity}:\n"
                + "\n".join(
                    lines
                )
            )

        if not evidence.empty:

            fir_numbers = (
                self._extract_fir_numbers(
                    evidence
                )
            )

            if len(fir_numbers) > 1:

                return (
                    f"{resolved_entity} has "
                    f"{len(fir_numbers)} "
                    f"linked FIR/evidence records "
                    f"in the available dataset, "
                    f"which may indicate multiple "
                    f"recorded incidents. This is "
                    f"an analytical observation and "
                    f"not a determination of guilt."
                )

        return (
            f"No explicit prior-history field "
            f"was found for {resolved_entity} "
            f"in the available datasets."
        )
# ------------------------------------------------------------
    # GENERIC VALUE EXTRACTION
    # ------------------------------------------------------------

    def _describe_entity_data(
        self,
        entity_name,
        df
    ):
        if df.empty:
            return None

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        lines = []

        for column in df.columns:

            values = self._clean_values(
                df[column],
                limit=8
            )

            if not values:
                continue

            lines.append(
                f"{column}: "
                + ", ".join(values)
            )

        if not lines:
            return None

        return (
            f"Available evidence attributes for "
            f"{resolved_entity}:\n"
            + "\n".join(lines)
        )

    # ------------------------------------------------------------
    # COLUMN VALUE LOOKUP
    # ------------------------------------------------------------

    def _values_from_columns(
        self,
        df,
        columns,
        limit=20
    ):
        if df.empty:
            return []

        found = []

        for column in columns:

            if column not in df.columns:
                continue

            values = self._clean_values(
                df[column],
                limit=limit
            )

            if values:
                found.append(
                    (
                        column,
                        values
                    )
                )

        return found

    # ------------------------------------------------------------
    # FIR NUMBER EXTRACTION
    # ------------------------------------------------------------

    def _fir_numbers(
        self,
        evidence
    ):
        if evidence.empty:
            return []

        possible_columns = [
            "FIR_No",
            "FIR No",
            "FIR_Number",
            "FIR Number",
            "fir_no",
            "fir_number"
        ]

        for column in possible_columns:

            if column in evidence.columns:

                values = self._clean_values(
                    evidence[column],
                    limit=100
                )

                if values:
                    return values

        return []
# ------------------------------------------------------------
    # FIND ENTITY IN INVESTIGATION CONTEXT
    # ------------------------------------------------------------

    def _find_entity(self, entity_name):
        """
        Find all investigation-context records associated
        with the supplied entity name.
        """

        if self.context_df.empty:
            return pd.DataFrame()

        entity_name = str(
            entity_name or ""
        ).strip()

        if not entity_name:
            return pd.DataFrame()

        normalized_target = (
            self._normalize_text(
                entity_name
            )
        )

        matched_rows = []

        for index, row in self.context_df.iterrows():

            row_text = " ".join(
                str(value)
                for value in row.tolist()
                if pd.notna(value)
            )

            normalized_row = (
                self._normalize_text(
                    row_text
                )
            )

            # Exact normalized entity match
            if normalized_target in normalized_row:
                matched_rows.append(index)

        if not matched_rows:
            return pd.DataFrame(
                columns=self.context_df.columns
            )

        return (
            self.context_df
            .loc[matched_rows]
            .copy()
        )
    # ------------------------------------------------------------
    # MAIN ANSWER ENGINE
    # ------------------------------------------------------------

    def answer(
        self,
        entity_name,
        question
    ):
        question = str(
            question or ""
        ).strip()

        if not question:
            return (
                "Please enter an investigation question."
            )

        resolved_entity = (
            self.resolve_entity(
                entity_name
            )
        )

        if not resolved_entity:
            return (
                "Please provide a valid entity name."
            )

        investigation = (
            self.get_investigation_summary(
                resolved_entity
            )
        )

        question_type = (
            self._question_type(
                question
            )
        )

        # --------------------------------------------------------
        # RISK
        # --------------------------------------------------------

        if question_type == "risk":

            if investigation["found"]:

                return (
                    f"{resolved_entity} has a calculated "
                    f"risk score of "
                    f"{investigation['risk_score']:.2f} "
                    f"and is classified as "
                    f"{investigation['risk_level']}. "
                    f"The investigation context contains "
                    f"{investigation['evidence_count']} "
                    f"linked evidence record(s) and "
                    f"{investigation['relationship_count']} "
                    f"relationship(s). "
                    f"This is an analytical prioritization "
                    f"indicator, not a determination of guilt."
                )

            return (
                f"No risk assessment is available for "
                f"{resolved_entity}."
            )

        # --------------------------------------------------------
        # CONNECTIONS
        # --------------------------------------------------------

        if question_type == "connections":

            connections = (
                self.get_connections(
                    resolved_entity
                )
            )

            if not connections.empty:

                preview = (
                    connections
                    .head(10)
                    .to_string(
                        index=False
                    )
                )

                return (
                    f"Investigative connection records "
                    f"for {resolved_entity}:\n\n"
                    f"{preview}"
                )

            relations = (
                self._get_relationships(
                    resolved_entity
                )
            )

            if not relations.empty:

                preview = (
                    relations
                    .head(10)
                    .to_string(
                        index=False
                    )
                )

                return (
                    f"I found "
                    f"{len(relations)} "
                    f"relationship record(s) "
                    f"associated with "
                    f"{resolved_entity}:\n\n"
                    f"{preview}"
                )

            return (
                f"No evidence-based investigative "
                f"connections were found for "
                f"{resolved_entity}."
            )

        # --------------------------------------------------------
        # COUNT / CASES
        # --------------------------------------------------------

        if question_type == "count":

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            fir_numbers = (
                self._fir_numbers(
                    evidence
                )
            )

            if fir_numbers:

                return (
                    f"{resolved_entity} is linked to "
                    f"{len(fir_numbers)} "
                    f"FIR/evidence record(s)."
                )

            if investigation["found"]:

                return (
                    f"{resolved_entity} is linked to "
                    f"{investigation['evidence_count']} "
                    f"evidence record(s)."
                )

            return (
                f"No linked cases or FIR records were "
                f"found for {resolved_entity}."
            )

        # --------------------------------------------------------
        # EVIDENCE / FIR / CASE
        # --------------------------------------------------------

        if question_type == "evidence":

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            if not evidence.empty:

                fir_numbers = (
                    self._fir_numbers(
                        evidence
                    )
                )

                if fir_numbers:

                    return (
                        f"{resolved_entity} has "
                        f"{len(fir_numbers)} "
                        f"linked FIR record(s): "
                        + ", ".join(
                            fir_numbers[:20]
                        )
                    )

                description = (
                    self._describe_entity_data(
                        resolved_entity,
                        evidence
                    )
                )

                if description:
                    return description

                return (
                    f"Evidence records were found "
                    f"for {resolved_entity}, but the "
                    f"available fields do not provide "
                    f"a concise summary."
                )

            if investigation["found"]:

                return (
                    f"The investigation context records "
                    f"{investigation['evidence_count']} "
                    f"linked evidence record(s) for "
                    f"{resolved_entity}, but no directly "
                    f"matching standardized evidence rows "
                    f"were available."
                )

            return (
                f"No directly linked evidence records "
                f"were found for {resolved_entity}."
            )

        # --------------------------------------------------------
        # LOCATION
        # --------------------------------------------------------

        if question_type == "location":

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            location_columns = [
                "State",
                "state",
                "District",
                "district",
                "City",
                "city",
                "Address",
                "address",
                "Location",
                "location",
                "Place",
                "place"
            ]

            found_locations = (
                self._values_from_columns(
                    evidence,
                    location_columns,
                    limit=10
                )
            )

            if found_locations:

                lines = [
                    f"Location information for "
                    f"{resolved_entity}:"
                ]

                for column, values in (
                    found_locations
                ):
                    lines.append(
                        f"{column}: "
                        + ", ".join(values)
                    )

                return "\n".join(
                    lines
                )

            context_matches = (
                self._find_entity(
                    resolved_entity
                )
            )

            found_locations = (
                self._values_from_columns(
                    context_matches,
                    location_columns,
                    limit=10
                )
            )

            if found_locations:

                lines = [
                    f"Location information for "
                    f"{resolved_entity}:"
                ]

                for column, values in (
                    found_locations
                ):
                    lines.append(
                        f"{column}: "
                        + ", ".join(values)
                    )

                return "\n".join(
                    lines
                )

            if investigation["found"]:

                return (
                    f"Location information for "
                    f"{resolved_entity} was identified "
                    f"in the investigation context, but "
                    f"no standardized location fields were "
                    f"available."
                )

            return (
                f"No location information was found "
                f"for {resolved_entity}."
            )

        # --------------------------------------------------------
        # TIME / TIMELINE
        # --------------------------------------------------------

        if question_type == "time":

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            date_columns = [
                "Date",
                "date",
                "FIR_Date",
                "FIR Date",
                "FIR_DateTime",
                "FIR DateTime",
                "Incident_Date",
                "Incident Date",
                "Incident_DateTime",
                "Incident DateTime",
                "Year",
                "year",
                "Date_of_Incident",
                "Date of Incident"
            ]

            found_dates = (
                self._values_from_columns(
                    evidence,
                    date_columns,
                    limit=20
                )
            )

            if found_dates:

                lines = [
                    f"Timeline information for "
                    f"{resolved_entity}:"
                ]

                for column, values in (
                    found_dates
                ):
                    lines.append(
                        f"{column}: "
                        + ", ".join(values)
                    )

                return "\n".join(
                    lines
                )

            fir_numbers = (
                self._fir_numbers(
                    evidence
                )
            )

            if fir_numbers:

                years = sorted(
                    {
                        match
                        for fir in fir_numbers
                        for match in re.findall(
                            r"\b(?:19|20)\d{2}\b",
                            fir
                        )
                    }
                )

                if years:

                    return (
                        f"Timeline information for "
                        f"{resolved_entity}:\n"
                        f"Years represented in linked FIR "
                        f"records: "
                        + ", ".join(years)
                    )

            if investigation["found"]:

                return (
                    f"Timeline information for "
                    f"{resolved_entity} is present in "
                    f"the investigation context, but no "
                    f"standardized date or year fields "
                    f"were available."
                )

            return (
                f"No timeline information was found "
                f"for {resolved_entity}."
            )

        # --------------------------------------------------------
        # CRIME / OFFENCE
        # --------------------------------------------------------

        if question_type == "crime":

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            crime_columns = [
                "Crime",
                "crime",
                "Crime_Type",
                "Crime Type",
                "CrimeType",
                "Offence",
                "Offense",
                "Offence_Type",
                "Offense_Type",
                "Offence Type",
                "Offense Type",
                "Section",
                "Sections",
                "IPC_Section",
                "IPC Section",
                "Act",
                "Act_Name",
                "Act Name"
            ]

            found_crimes = (
                self._values_from_columns(
                    evidence,
                    crime_columns,
                    limit=20
                )
            )

            if found_crimes:

                lines = [
                    f"Crime/offence information "
                    f"for {resolved_entity}:"
                ]

                for column, values in (
                    found_crimes
                ):
                    lines.append(
                        f"{column}: "
                        + ", ".join(values)
                    )

                return "\n".join(
                    lines
                )

            if investigation["found"]:

                return (
                    f"Crime-related records are associated "
                    f"with {resolved_entity}, but no "
                    f"standardized offence fields were "
                    f"available."
                )

            return (
                f"No crime or offence information was "
                f"found for {resolved_entity}."
            )

        # --------------------------------------------------------
        # SEVERITY
        # --------------------------------------------------------

        if question_type == "severity":

            if investigation["found"]:

                return (
                    f"{resolved_entity} has a calculated "
                    f"risk score of "
                    f"{investigation['risk_score']:.2f}, "
                    f"which corresponds to a "
                    f"{investigation['risk_level']} "
                    f"analytical risk level. This "
                    f"classification is intended for "
                    f"investigative prioritization and "
                    f"does not establish guilt."
                )

            risk_matches = (
                self._entity_matches_dataframe(
                    self.risk_df,
                    resolved_entity
                )
            )

            if not risk_matches.empty:

                record = risk_matches.iloc[0]

                score = self._safe_float(
                    record.get(
                        "risk_score",
                        record.get(
                            "score",
                            0
                        )
                    )
                )

                level = str(
                    record.get(
                        "risk_level",
                        record.get(
                            "level",
                            "UNKNOWN"
                        )
                    )
                ).strip()

                return (
                    f"{resolved_entity} has a calculated "
                    f"risk score of {score:.2f} and "
                    f"an analytical risk level of {level}. "
                    f"This is an investigative prioritization "
                    f"indicator, not a determination of guilt."
                )

            return (
                f"No severity assessment is available "
                f"for {resolved_entity}."
            )

        # --------------------------------------------------------
        # PRIOR / HISTORY
        # --------------------------------------------------------

        if question_type == "prior":

            evidence = (
                self.get_evidence(
                    resolved_entity
                )
            )

            if not evidence.empty:

                fir_numbers = (
                    self._fir_numbers(
                        evidence
                    )
                )

                if len(fir_numbers) > 1:

                    return (
                        f"{resolved_entity} has "
                        f"{len(fir_numbers)} linked "
                        f"FIR/evidence records, indicating "
                        f"multiple records in the available "
                        f"investigation dataset: "
                        + ", ".join(
                            fir_numbers[:20]
                        )
                    )

                if len(fir_numbers) == 1:

                    return (
                        f"{resolved_entity} has one "
                        f"linked FIR/evidence record: "
                        f"{fir_numbers[0]}. The available "
                        f"dataset does not establish a "
                        f"separate prior-history finding."
                    )

                description = (
                    self._describe_entity_data(
                        resolved_entity,
                        evidence
                    )
                )

                if not evidence.empty:

                 fir_numbers = (
                    self._fir_numbers(
                        evidence
                    )
                )

                if len(fir_numbers) > 1:

                    return (
                        f"{resolved_entity} has "
                        f"{len(fir_numbers)} linked "
                        f"FIR/evidence records, indicating "
                        f"multiple records in the available "
                        f"investigation dataset: "
                        + ", ".join(
                            fir_numbers[:20]
                        )
                    )

                if len(fir_numbers) == 1:

                    return (
                        f"{resolved_entity} has one "
                        f"linked FIR/evidence record: "
                        f"{fir_numbers[0]}. The available "
                        f"dataset does not establish a "
                        f"separate prior-history finding."
                    )

                description = (
                    self._describe_entity_data(
                        resolved_entity,
                        evidence
                    )
                )

                if description:
                    return description

            if investigation["found"]:

                if investigation[
                    "evidence_count"
                ] > 0:

                    return (
                        f"The available investigation context "
                        f"contains "
                        f"{investigation['evidence_count']} "
                        f"linked evidence record(s) for "
                        f"{resolved_entity}. A separate "
                        f"prior-history determination is not "
                        f"available from the current standardized "
                        f"fields."
                    )

                return (
                    f"No prior-history records are available "
                    f"for {resolved_entity}."
                )

            return (
                f"No prior-history information was found "
                f"for {resolved_entity}."
            )

        # --------------------------------------------------------
        # SUMMARY
        # --------------------------------------------------------

        if question_type == "summary":

            if investigation["found"]:

                entity_type = investigation.get(
                    "entity_type",
                    "Investigation Entity"
                )

                return (
                    f"Investigation summary for "
                    f"{resolved_entity}:\n"
                    f"Entity type: "
                    f"{entity_type}\n"
                    f"Linked evidence records: "
                    f"{investigation['evidence_count']}\n"
                    f"Relationships: "
                    f"{investigation['relationship_count']}\n"
                    f"Risk score: "
                    f"{investigation['risk_score']:.2f}\n"
                    f"Risk level: "
                    f"{investigation['risk_level']}\n"
                    f"Traceable evidence: "
                    f"{investigation.get('traceable_evidence', investigation['evidence_count'])}\n\n"
                    f"This is an analytical investigation "
                    f"summary and not a determination of guilt."
                )

            return (
                f"No investigation summary is available "
                f"for {resolved_entity}."
            )

        # --------------------------------------------------------
        # GENERIC DATASET QUESTIONS
        # --------------------------------------------------------

        search_results = (
            self._search_all_data(
                question
            )
        )

        if search_results:

            output_parts = []

            for (
                filename,
                df,
                relevant_columns
            ) in search_results[:5]:

                entity_rows = (
                    self._entity_matches_dataframe(
                        df,
                        resolved_entity
                    )
                )

                if entity_rows.empty:
                    continue

                description = (
                    self._describe_entity_data(
                        resolved_entity,
                        entity_rows
                    )
                )

                if description:

                    output_parts.append(
                        f"[{filename}]\n"
                        f"{description}"
                    )

            if output_parts:

                return "\n\n".join(
                    output_parts
                )

        # --------------------------------------------------------
        # FINAL FALLBACK
        # --------------------------------------------------------

        if investigation["found"]:

            return investigation[
                "summary"
            ]

        return (
            f"I could not find enough evidence to "
            f"answer that question for "
            f"{resolved_entity}. "
            f"Please check the entity name or ask about "
            f"information contained in the available "
            f"investigation datasets."
        )


# ================================================================
# STANDALONE TEST
# ================================================================

if __name__ == "__main__":

    assistant = InvestigationAssistant()

    entity = "Ganga Dyal"

    print(
        "\n=========================================="
    )

    print(
        " AI INVESTIGATION ASSISTANT TEST"
    )

    print(
        "==========================================\n"
    )

    print(
        "Resolved entity:",
        assistant.resolve_entity(
            entity
        )
    )

    result = (
        assistant.get_investigation_summary(
            entity
        )
    )

    print(
        "Found:",
        result["found"]
    )

    if result["found"]:

        print(
            "\nSummary:"
        )

        print(
            result["summary"]
        )

    test_questions = [
        "Why is this entity high risk?",
        "How many cases are linked?",
        "What evidence do we have?",
        "Where is this person located?",
        "Who is this person connected to?",
        "When did this person appear in the records?",
        "What crimes are associated with this person?",
        "How severe is the risk?",
        "What is the prior history?",
        "Give me a summary"
    ]

    for question in test_questions:

        print(
            "\nQuestion:",
            question
        )

        print(
            "Answer:",
            assistant.answer(
                entity,
                question
            )
        )

    print(
        "\n==========================================\n"
    )

