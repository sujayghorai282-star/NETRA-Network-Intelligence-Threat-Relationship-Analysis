import os
import pandas as pd


CONTEXT_FILE = "output/investigation_context.csv"


class InvestigatorAPI:

    def __init__(self, context_file=CONTEXT_FILE):

        self.context_file = context_file
        self.context = None

        self.load_context()


    # =========================================================
    # LOAD INVESTIGATION CONTEXT
    # =========================================================

    def load_context(self):

        if not os.path.exists(self.context_file):

            raise FileNotFoundError(
                f"Investigation context not found: "
                f"{self.context_file}"
            )

        self.context = pd.read_csv(
            self.context_file
        )

        self.context["entity"] = (
            self.context["entity"]
            .astype(str)
            .str.strip()
        )


    # =========================================================
    # EXACT ENTITY SEARCH
    # =========================================================

    def search_entity(self, entity_name):

        if not entity_name:
            return None

        entity_name = str(
            entity_name
        ).strip()

        matches = self.context[
            self.context["entity"]
            .str.lower()
            == entity_name.lower()
        ]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()


    # =========================================================
    # PARTIAL ENTITY SEARCH
    # =========================================================

    def search_entities(
        self,
        search_text,
        limit=20
    ):

        if not search_text:
            return []

        search_text = str(
            search_text
        ).strip().lower()

        matches = self.context[
            self.context["entity"]
            .str.lower()
            .str.contains(
                search_text,
                regex=False,
                na=False
            )
        ]

        matches = matches.head(limit)

        return matches.to_dict(
            orient="records"
        )


    # =========================================================
    # GET ENTITIES BY TYPE
    # =========================================================

    def get_entities_by_type(
        self,
        entity_type,
        limit=100
    ):

        if "entity_type" not in self.context.columns:
            return []

        matches = self.context[
            self.context["entity_type"]
            .astype(str)
            .str.upper()
            ==
            str(entity_type).upper()
        ]

        matches = matches.head(limit)

        return matches.to_dict(
            orient="records"
        )


    # =========================================================
    # HIGH RISK ENTITIES
    # =========================================================

    def get_high_risk_entities(
        self,
        limit=20
    ):

        if "risk_level" not in self.context.columns:
            return []

        matches = self.context[
            self.context["risk_level"]
            .astype(str)
            .str.upper()
            == "HIGH"
        ].copy()

        if "risk_score" in matches.columns:

            matches = matches.sort_values(
                "risk_score",
                ascending=False
            )

        matches = matches.head(limit)

        return matches.to_dict(
            orient="records"
        )


    # =========================================================
    # CDR INTELLIGENCE
    # =========================================================

    def get_cdr_intelligence(
        self,
        entity_name
    ):

        if not entity_name:
            return None

        cdr_file = (
            "output/cdr_intelligence.csv"
        )

        if not os.path.exists(cdr_file):
            return None

        cdr_data = pd.read_csv(
            cdr_file
        )

        if "entity" not in cdr_data.columns:
            return None

        cdr_data["entity"] = (
            cdr_data["entity"]
            .astype(str)
            .str.strip()
        )

        matches = cdr_data[
            cdr_data["entity"]
            .str.lower()
            ==
            str(entity_name)
            .strip()
            .lower()
        ]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()


    # =========================================================
    # CDR CONNECTIONS
    # =========================================================

    def get_cdr_connections(
        self,
        entity_name,
        limit=20
    ):

        if not entity_name:
            return []

        cdr_file = (
            "output/normalized_cdr_relationships.csv"
        )

        if not os.path.exists(cdr_file):
            return []

        cdr_data = pd.read_csv(
            cdr_file
        )

        required_columns = {
            "source",
            "target",
            "relationship",
            "record_id"
        }

        if not required_columns.issubset(
            cdr_data.columns
        ):
            return []

        entity_name = str(
            entity_name
        ).strip().lower()

        source_matches = (
            cdr_data["source"]
            .astype(str)
            .str.strip()
            .str.lower()
            == entity_name
        )

        target_matches = (
            cdr_data["target"]
            .astype(str)
            .str.strip()
            .str.lower()
            == entity_name
        )

        matches = cdr_data[
            source_matches | target_matches
        ].copy()

        if matches.empty:
            return []

        matches = matches.head(limit)

        return matches.to_dict(
            orient="records"
        )


# =============================================================
# BASIC API TEST
# =============================================================

if __name__ == "__main__":

    print("\n==========================================")
    print(" INVESTIGATOR API TEST")
    print("==========================================\n")

    try:

        api = InvestigatorAPI()

        print(
            "Investigation entities:",
            len(api.context)
        )


        # -----------------------------------------------------
        # EXACT ENTITY TEST
        # -----------------------------------------------------

        test_entity = (
            api.context.iloc[0]["entity"]
        )

        print(
            "\nExact entity test:",
            test_entity
        )

        result = api.search_entity(
            test_entity
        )

        if result:

            print(
                "Entity type:",
                result.get(
                    "entity_type",
                    "N/A"
                )
            )

            print(
                "Evidence count:",
                result.get(
                    "evidence_count",
                    "N/A"
                )
            )

            print(
                "Risk score:",
                result.get(
                    "risk_score",
                    "N/A"
                )
            )

            print(
                "Risk level:",
                result.get(
                    "risk_level",
                    "N/A"
                )

            )

        else:

            print(
                "Entity not found."
            )


        # -----------------------------------------------------
        # PARTIAL SEARCH TEST
        # -----------------------------------------------------

        print(
            "\nPartial search test: Ganga"
        )

        results = api.search_entities(
            "Ganga",
            limit=5
        )

        print(
            "Matches found:",
            len(results)
        )

        for item in results:

            print(
                " -",
                item.get(
                    "entity",
                    "Unknown"
                ),
                "|",
                item.get(
                    "entity_type",
                    "Unknown"
                )
            )


        # -----------------------------------------------------
        # CDR INTELLIGENCE TEST
        # -----------------------------------------------------

        cdr_test_entity = "SUB00929"

        print(
            "\nCDR intelligence test:",
            cdr_test_entity
        )

        cdr_result = api.get_cdr_intelligence(
            cdr_test_entity
        )

        if cdr_result:

            print(
                "CDR intelligence found:"
            )

            for key, value in cdr_result.items():

                print(
                    f" {key}: {value}"
                )

        else:

            print(
                "No CDR intelligence found."
            )


        # -----------------------------------------------------
        # CDR CONNECTION TEST
        # -----------------------------------------------------

        print(
            "\nCDR connections test:",
            cdr_test_entity
        )

        cdr_connections = (
            api.get_cdr_connections(
                cdr_test_entity,
                limit=5
            )
        )

        print(
            "Connections found:",
            len(cdr_connections)
        )

        for connection in cdr_connections:

            print(
                " -",
                connection
            )


        # -----------------------------------------------------
        # HIGH RISK TEST
        # -----------------------------------------------------

        print(
            "\nHigh-risk entities:"
        )

        high_risk = (
            api.get_high_risk_entities(
                limit=5
            )
        )

        for entity in high_risk:

            print(
                " -",
                entity.get(
                    "entity",
                    "Unknown"
                ),
                "| Risk:",
                entity.get(
                    "risk_score",
                    "N/A"
                ),
                "|",
                entity.get(
                    "risk_level",
                    "N/A"
                )
            )


    except Exception as error:

        print(
            "\nAPI ERROR:"
        )

        print(error)

    print(
        "\n=========================================="
    )