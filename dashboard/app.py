import streamlit as st
import pandas as pd
import os
import subprocess
import sys
import streamlit.components.v1 as components
import plotly.express as px
import re
from pathlib import Path
# --------------------------------------------------
# PROJECT ROOT PATH
# --------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )

def run_script(script, args=None):
    command = [
        sys.executable,
        os.path.join(PROJECT_ROOT, script)
    ]

    if args:
        command.extend(str(arg) for arg in args)

    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NETRA — Network Intelligence & Threat Relationship Analysis",
    page_icon="👁️",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

# ============================================================
# NETRA SYSTEM HEADER
# ============================================================

st.title("👁️ NETRA")

st.subheader(
    "Network Intelligence & Threat Relationship Analysis"
)

st.caption(
    "AI-assisted investigation support for multi-source evidence "
    "analysis, entity relationships, network intelligence and "
    "investigative prioritization."
)

st.caption(
    "Investigation Support Platform • FIR • CDR • Financial Transactions • Social Media Intelligence"
)


# ============================================================
# PATHS
# ============================================================

OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "output")

UPLOAD_ROOT = os.path.join(PROJECT_ROOT, "data", "uploads")

FIR_UPLOAD_FOLDER = os.path.join(
    UPLOAD_ROOT,
    "fir"
)

CDR_UPLOAD_FOLDER = os.path.join(
    UPLOAD_ROOT,
    "cdr"
)
TRANSACTION_UPLOAD_FOLDER = os.path.join(
    UPLOAD_ROOT,
    "transaction"
)
SOCIAL_MEDIA_UPLOAD_FOLDER = os.path.join(
    UPLOAD_ROOT,
    "social_media"
)
# Create upload folders if they don't exist

os.makedirs(
    FIR_UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    CDR_UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    TRANSACTION_UPLOAD_FOLDER,
    exist_ok=True
)
os.makedirs(
    SOCIAL_MEDIA_UPLOAD_FOLDER,
    exist_ok=True
)
if not os.path.exists(OUTPUT_FOLDER):

    st.error(
        "❌ Output folder not found!"
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "saved_file_path" not in st.session_state:

    st.session_state.saved_file_path = None


if "saved_file_type" not in st.session_state:

    st.session_state.saved_file_type = None


if "saved_file_name" not in st.session_state:

    st.session_state.saved_file_name = None


if "processing_complete" not in st.session_state:

    st.session_state.processing_complete = False


# ============================================================
# DATA LOADING FUNCTION
# ============================================================

@st.cache_data
def load_csv(filename):

    path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    if not os.path.exists(path):

        return None

    try:

        return pd.read_csv(path)

    except Exception as e:

        st.error(
            f"Error loading {filename}: {e}"
        )

        return None

# ============================================================
# UNIVERSAL FIR COLUMN NORMALIZER
# ============================================================

def normalize_fir_column_name(column_name):
    name = str(column_name).strip().lower()
    name = re.sub(r"[\s\-/]+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


FIR_COLUMN_ALIASES = {

    "FIR_No": [
        "fir_no",
        "fir_number",
        "fir_num",
        "fir_id",
        "firid",
        "case_no",
        "case_number",
        "case_id",
        "crime_no",
        "crime_number",
        "complaint_no",
        "complaint_number",
        "fir"
    ],

    "Date_Filed": [
        "date_filed",
        "fir_date",
        "date_of_fir",
        "registration_date",
        "registered_on",
        "date_registered",
        "filing_date",
        "date"
    ],

    "State": [
        "state",
        "state_name",
        "province",
        "region"
    ],

    "District": [
        "district",
        "district_name"
    ],

    "Police_Station": [
        "police_station",
        "police_station_name",
        "ps_name",
        "ps",
        "station",
        "station_name",
        "police_post"
    ],

    "Complainant_Name": [
        "complainant_name",
        "complainant",
        "informant",
        "informant_name",
        "victim",
        "victim_name",
        "reporter",
        "reporting_person",
        "applicant"
    ],

    "Accused_Name": [
        "accused_name",
        "accused",
        "suspect",
        "suspect_name",
        "offender",
        "offender_name",
        "defendant",
        "defendant_name",
        "criminal_name"
    ],

    "Legal_Section": [
        "legal_section",
        "section",
        "sections",
        "ipc_section",
        "ipc_sections",
        "law_section",
        "act_section",
        "offence_section",
        "offense_section",
        "legal_provision"
    ],

    "Crime_Category": [
        "crime_category",
        "crime_type",
        "crime",
        "offence",
        "offense",
        "offence_type",
        "offense_type",
        "category",
        "crime_classification"
    ],

    "Incident_Description": [
        "incident_description",
        "description",
        "incident_details",
        "incident",
        "narrative",
        "case_description",
        "complaint_details",
        "details",
        "remarks"
    ],

    "Case_Status": [
        "case_status",
        "status",
        "investigation_status",
        "case_state",
        "disposal_status",
        "current_status"
    ]
}


def normalize_fir_dataframe(uploaded_df):

    df = uploaded_df.copy()

    normalized_columns = {
        column: normalize_fir_column_name(column)
        for column in df.columns
    }

    alias_lookup = {}

    for canonical_name, aliases in FIR_COLUMN_ALIASES.items():

        for alias in aliases:

            normalized_alias = normalize_fir_column_name(alias)

            alias_lookup[normalized_alias] = canonical_name

        alias_lookup[
            normalize_fir_column_name(canonical_name)
        ] = canonical_name

    mapping_report = {}

    for original_column, normalized_column in normalized_columns.items():

        canonical_name = alias_lookup.get(
            normalized_column
        )

        if canonical_name is None:
            continue

        if canonical_name in df.columns:
            continue

        df[canonical_name] = df[original_column]

        mapping_report[canonical_name] = original_column

    return df, mapping_report
# ============================================================
# EVIDENCE UPLOAD
# ============================================================

st.sidebar.divider()

st.sidebar.header(
    "📂 Evidence Upload"
)

st.sidebar.markdown(
    "Upload investigation evidence for processing."
)


evidence_type = st.sidebar.selectbox(
    "Evidence Type",
    [
        "FIR",
        "CDR",
        "TRANSACTION",
        "SOCIAL_MEDIA"
    ]
)


uploaded_file = st.sidebar.file_uploader(
    "Upload Evidence File",
    type=[
        "csv",
        "pdf",
        "docx"
    ],
    help="Supported formats: CSV, PDF and DOCX"
)


# ============================================================
# UPLOADED FILE INFORMATION
# ============================================================

if uploaded_file is not None:

    st.sidebar.success(
        f"Uploaded: {uploaded_file.name}"
    )

    st.sidebar.info(
        f"Evidence Type: {evidence_type}"
    )

    st.sidebar.write(
        f"File Size: "
        f"{uploaded_file.size / 1024:.1f} KB"
    )

    st.sidebar.divider()


    # ========================================================
    # SAVE EVIDENCE
    # ========================================================

    if st.sidebar.button(
        "💾 Save Evidence",
        use_container_width=True
    ):

        if evidence_type == "FIR":

            upload_folder = FIR_UPLOAD_FOLDER

        elif evidence_type == "CDR":

            upload_folder = CDR_UPLOAD_FOLDER

        elif evidence_type == "TRANSACTION":

            upload_folder = TRANSACTION_UPLOAD_FOLDER

        elif evidence_type == "SOCIAL_MEDIA":

            upload_folder = SOCIAL_MEDIA_UPLOAD_FOLDER

        else:

            st.sidebar.error(
                f"❌ Unsupported evidence type: {evidence_type}"
            )

            st.stop()

        uploaded_file_path = os.path.join(
            upload_folder,
            uploaded_file.name
        )
        
        # ====================================================
        # FIR VALIDATION
        # ====================================================

        if evidence_type == "FIR":

            if not uploaded_file.name.lower().endswith(".csv"):

                st.sidebar.error(
                    "❌ FIR validation currently supports CSV files."
                )

            else:

                try:

                    uploaded_df = pd.read_csv(
                        uploaded_file
                    )

                    # ============================================================
                    # UNIVERSAL FIR COLUMN NORMALIZATION
                    # ============================================================

                    uploaded_df, column_mapping = normalize_fir_dataframe(
                        uploaded_df
                    )

                    # ------------------------------------------------------------
                    # UNIVERSAL DATASET ACCEPTANCE
                    # ------------------------------------------------------------
                    # Do not enforce the legacy 12-column FIR schema here.
                    # The universal loader will validate and standardize the
                    # uploaded dataset when processing begins.

                    # ------------------------------------------------------------
                    # EMPTY FILE CHECK
                    # ------------------------------------------------------------

                    if uploaded_df.empty:

                        st.sidebar.error(
                            "❌ Uploaded CSV does not contain any records."
                        )

                    else:

                        # --------------------------------------------------------
                        # SAVE UPLOADED EVIDENCE
                        # --------------------------------------------------------

                        uploaded_df.to_csv(
                            uploaded_file_path,
                            index=False
                        )

                        st.session_state.saved_file_path = (
                            uploaded_file_path
                        )

                        st.session_state.saved_file_type = "FIR"

                        st.session_state.saved_file_name = (
                            uploaded_file.name
                        )

                        st.session_state.processing_complete = False

                        # --------------------------------------------------------
                        # SHOW NORMALIZATION REPORT
                        # --------------------------------------------------------

                        if column_mapping:

                            st.sidebar.success(
                                "✅ FIR evidence recognized and normalized."
                            )

                            st.sidebar.write(
                                "🔄 Columns automatically mapped:"
                            )

                            for canonical_column, original_column in column_mapping.items():

                                st.sidebar.write(
                                    f"• `{original_column}` → `{canonical_column}`"
                                )

                        else:

                            st.sidebar.info(
                                "ℹ️ No standard column names were detected. "
                                "Available evidence has been retained."
                            )

                        # --------------------------------------------------------
                        # SHOW UNRECOGNIZED FIELDS
                        # --------------------------------------------------------

                            st.sidebar.success(
                            "✅ Evidence file accepted. Universal dataset detection "
                            "will be performed during processing."
)

                        # --------------------------------------------------------
                        # FINAL INGESTION STATUS
                        # --------------------------------------------------------

                        st.sidebar.success(
                            "✅ FIR evidence accepted for processing."
                        )

                        st.sidebar.write(
                            f"📄 Records detected: {len(uploaded_df):,}"
                        )

                        st.sidebar.write(
                            f"📊 Columns detected: {len(uploaded_df.columns)}"
                        )


                except Exception as e:

                    st.sidebar.error(
                        f"❌ Unable to validate FIR file: {e}"
                    )


        # ====================================================
        # CDR SAVE
        # ====================================================

        elif evidence_type == "CDR":

                        try:

                            with open(
                                uploaded_file_path,
                                "wb"
                            ) as f:

                                f.write(
                                    uploaded_file.getbuffer()
                                )

                            st.session_state.saved_file_path = (
                                uploaded_file_path
                            )

                            st.session_state.saved_file_type = (
                                "CDR"
                            )

                            st.session_state.saved_file_name = (
                                uploaded_file.name
                            )

                            st.sidebar.success(
                                "✅ CDR evidence saved successfully."
                            )

                        except Exception as e:

                            st.sidebar.error(
                                f"❌ Unable to save CDR file: {e}"
                            )
# ====================================================
        # TRANSACTION SAVE
        # ====================================================

        elif evidence_type == "TRANSACTION":

            try:

                with open(
                    uploaded_file_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )

                st.session_state.saved_file_path = (
                    uploaded_file_path
                )

                st.session_state.saved_file_type = (
                    "TRANSACTION"
                )

                st.session_state.saved_file_name = (
                    uploaded_file.name
                )

                st.session_state.processing_complete = False

                st.sidebar.success(
                    "✅ Transaction evidence saved successfully."
                )

            except Exception as e:

                st.sidebar.error(
                    f"❌ Unable to save transaction file: {e}"
                )
        # ====================================================
        # SOCIAL MEDIA SAVE
        # ====================================================
        elif evidence_type == "SOCIAL_MEDIA":

            try:

                with open(
                    uploaded_file_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )

                st.session_state.saved_file_path = (
                    uploaded_file_path
                )

                st.session_state.saved_file_type = (
                    "SOCIAL_MEDIA"
                )

                st.session_state.saved_file_name = (
                    uploaded_file.name
                )

                st.session_state.processing_complete = False

                st.sidebar.success(
                    "✅ Social Media evidence saved successfully."
                )

            except Exception as e:

                st.sidebar.error(
                    f"❌ Unable to save social media file: {e}"
                )            

# ====================================================
# CDR PROCESSING
# ====================================================

if (
    st.session_state.get("saved_file_type") == "CDR"
    and os.path.exists(
        st.session_state.get("saved_file_path", "")
    )
):

    st.divider()

    st.markdown("### 📞 CDR Processing")

    st.caption(
        "Process the uploaded CDR file to generate communication intelligence."
    )

    if st.button(
        "⚙️ Process CDR",
        use_container_width=True
    ):

        st.write("🔍 Process CDR button clicked")

        with st.spinner(
            "Processing uploaded CDR..."
        ):

            result = run_script(
                "src/data_processing/cdr_normalizer.py",
                [
                    st.session_state.saved_file_path
                ]
            )

            if result.returncode != 0:

                st.error(
                    "❌ CDR normalization failed."
                )

                st.code(
                    result.stderr or result.stdout
                )

            else:

                st.success(
                    "✅ CDR normalization completed successfully."
                )

                st.info(
                    "📊 CDR data has been normalized and is ready "
                    "for intelligence analysis."
                )

                if result.stdout:

                    with st.expander(
                        "View CDR Processing Log"
                    ):

                        st.code(
                            result.stdout
                        )
# ============================================================
# TRANSACTION PROCESSING
# ============================================================

elif (
    st.session_state.get("saved_file_type") == "TRANSACTION"
    and st.session_state.get("saved_file_path")
):

    st.divider()

    st.subheader("💳 Transaction Processing")

    saved_transaction = (
        st.session_state.saved_file_path
    )

    st.write(
        f"📄 Processing: "
        f"`{st.session_state.saved_file_name}`"
    )

    if not os.path.exists(saved_transaction):

        st.error(
            "❌ Saved transaction file could not be found."
        )

    else:

        if st.button(
            "⚙️ Process Transaction",
            use_container_width=True
        ):

            with st.spinner(
                "Processing transaction intelligence..."
            ):

                # ------------------------------------------------
                # 1. TRANSACTION NORMALIZATION
                # ------------------------------------------------

                result = run_script(
                    "src/transactions/transaction_normalizer.py",
                    [saved_transaction]
                )

                if result.returncode != 0:

                    st.error(
                        "❌ Transaction normalization failed."
                    )

                    st.code(
                        result.stderr or result.stdout
                    )

                    st.stop()

                st.success(
                    "✅ Transaction normalization completed."
                )

                # ------------------------------------------------
                # 2. TRANSACTION INTELLIGENCE
                # ------------------------------------------------

                result2 = run_script(
                    "src/transactions/transaction_intelligence.py"
                )

                if result2.returncode != 0:

                    st.error(
                        "❌ Transaction intelligence processing failed."
                    )

                    st.code(
                        result2.stderr or result2.stdout
                    )

                    st.stop()

                st.success(
                    "✅ Transaction intelligence completed."
                )

                # ------------------------------------------------
                # 3. OUTPUT VALIDATION
                # ------------------------------------------------

                normalized_transaction_output = os.path.join(
                    PROJECT_ROOT,
                    "output",
                    "normalized_transaction_data.csv"
                )

                transaction_intelligence_output = os.path.join(
                    PROJECT_ROOT,
                    "output",
                    "transaction_intelligence.csv"
                )

                if not os.path.exists(
                    normalized_transaction_output
                ):

                    st.error(
                        "❌ Normalized transaction output was not generated."
                    )

                    st.stop()

                if not os.path.exists(
                    transaction_intelligence_output
                ):

                    st.error(
                        "❌ Transaction intelligence output was not generated."
                    )

                    st.stop()

                st.success(
                    "✅ Transaction evidence processing completed successfully."
                )

                st.session_state.processing_complete = True

# ============================================================
# SOCIAL MEDIA PROCESSING
# ============================================================

elif (
    st.session_state.get("saved_file_type") == "SOCIAL_MEDIA"
    and st.session_state.get("saved_file_path")
):

    st.divider()

    st.subheader("📱 Social Media Processing")

    saved_social_media = (
        st.session_state.saved_file_path
    )

    st.write(
        f"📄 Processing: "
        f"`{st.session_state.saved_file_name}`"
    )

    if not os.path.exists(saved_social_media):

        st.error(
            "❌ Saved social media file could not be found."
        )

    else:

        if st.button(
            "⚙️ Process Social Media",
            use_container_width=True
        ):

            with st.spinner(
                "Processing social media intelligence..."
            ):

                # ------------------------------------------------
                # 1. SOCIAL MEDIA NORMALIZATION
                # ------------------------------------------------

                result = run_script(
                    "src/social_media/social_media_normalizer.py",
                    [saved_social_media]
                )

                if result.returncode != 0:

                    st.error(
                        "❌ Social media normalization failed."
                    )

                    st.code(
                        result.stderr or result.stdout
                    )

                    st.stop()

                st.success(
                    "✅ Social media normalization completed."
                )

                # ------------------------------------------------
                # 2. SOCIAL MEDIA RELATIONSHIP EXTRACTION
                # ------------------------------------------------

                result2 = run_script(
                    "src/social_media/social_media_relationships.py"
                )

                if result2.returncode != 0:

                    st.error(
                        "❌ Social media relationship extraction failed."
                    )

                    st.code(
                        result2.stderr or result2.stdout
                    )

                    st.stop()

                st.success(
                    "✅ Social media relationship extraction completed."
                )

                # ------------------------------------------------
                # 3. OUTPUT VALIDATION
                # ------------------------------------------------

                normalized_social_media_output = os.path.join(
                    PROJECT_ROOT,
                    "output",
                    "normalized_social_media.csv"
                )

                social_media_relationship_output = os.path.join(
                    PROJECT_ROOT,
                    "output",
                    "social_media_relationships.csv"
                )

                if not os.path.exists(
                    normalized_social_media_output
                ):

                    st.error(
                        "❌ Normalized social media output was not generated."
                    )

                    st.stop()

                if not os.path.exists(
                    social_media_relationship_output
                ):

                    st.error(
                        "❌ Social media relationship output was not generated."
                    )

                    st.stop()

                st.success(
                    "✅ Social media evidence processing completed successfully."
                )

                st.session_state.processing_complete = True               
# ============================================================
# SAVED EVIDENCE STATUS
# ============================================================

if (
    st.session_state.saved_file_path
    and os.path.exists(
        st.session_state.saved_file_path
    )
):

    st.sidebar.divider()

    st.sidebar.success(
        "📁 Evidence saved"
    )

    st.sidebar.caption(
        st.session_state.saved_file_name
    )


# ============================================================
# PROCESS FIR
# ============================================================

if (
    st.session_state.saved_file_type == "FIR"
    and st.session_state.saved_file_path
    and os.path.exists(
        st.session_state.saved_file_path
    )
):

    st.sidebar.divider()

    st.sidebar.subheader(
        "⚙️ Evidence Processing"
    )


    if st.sidebar.button(
        "⚙️ Process FIR",
        use_container_width=True
    ):

        fir_path = (
            st.session_state.saved_file_path
        )


        with st.spinner(
            "Processing FIR evidence..."
        ):

            try:

                # --------------------------------------------
                # STEP 1
                # FIR STANDARDIZATION
                # --------------------------------------------

                st.sidebar.info(
                    "1/4 Standardizing FIR data..."
                )


                loader_result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(PROJECT_ROOT, "src", "data_processing", "load_fir_data.py"),
                        fir_path
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )


                if loader_result.returncode != 0:

                    st.error("❌ FIR standardization failed.")

                    st.code(
                        f"STDOUT:\n{loader_result.stdout}\n\n"
                        f"STDERR:\n{loader_result.stderr}"
                    )

                    st.stop()


                # --------------------------------------------
                # STEP 2
                # RELATIONSHIP EXTRACTION
                # --------------------------------------------

                st.sidebar.info(
                    "2/4 Extracting relationships..."
                )


                relation_result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(PROJECT_ROOT, "src", "nlp", "process_relationships.py")
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )


                if relation_result.returncode != 0:

                    st.error(
                        "❌ Relationship extraction failed."
                    )

                    st.code(
                        relation_result.stderr
                    )

                    st.stop()


                # --------------------------------------------
                # STEP 3
                # NETWORK BUILDING
                # --------------------------------------------

                st.sidebar.info(
                    "3/4 Building criminal network..."
                )


                network_result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(PROJECT_ROOT, "src", "graph", "build_network.py")
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )


                if network_result.returncode != 0:

                    st.error(
                        "❌ Network construction failed."
                    )

                    st.code(
                        network_result.stderr
                    )

                    st.stop()


                # --------------------------------------------
                # STEP 4
                # RISK ANALYSIS
                # --------------------------------------------

                st.sidebar.info(
                    "4/4 Calculating risk scores..."
                )


                network_analysis_result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(PROJECT_ROOT, "src", "analytics", "network_analysis.py")
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )


                if network_analysis_result.returncode != 0:

                    st.error(
                        "❌ Network analysis failed."
                    )

                    st.code(
                        network_analysis_result.stderr
                    )

                    st.stop()


                risk_result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(PROJECT_ROOT, "src", "detection", "risk_scoring.py")
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )


                if risk_result.returncode != 0:

                    st.error(
                        "❌ Risk scoring failed."
                    )

                    st.code(
                        risk_result.stderr
                    )

                    st.stop()


                # --------------------------------------------
                # PROCESSING COMPLETE
                # --------------------------------------------

                st.session_state.processing_complete = (
                    True
                )


                st.cache_data.clear()


                st.sidebar.success(
                    "✅ FIR processing completed!"
                )


                st.success(
                    "🚀 FIR evidence successfully processed "
                    "through the intelligence pipeline."
                )


                with st.expander(
                    "📋 View Processing Logs"
                ):

                    st.subheader(
                        "FIR Standardization"
                    )

                    st.code(
                        loader_result.stdout
                    )


                    st.subheader(
                        "Relationship Extraction"
                    )

                    st.code(
                        relation_result.stdout
                    )


                    st.subheader(
                        "Network Construction"
                    )

                    st.code(
                        network_result.stdout
                    )


                    st.subheader(
                        "Network Analysis"
                    )

                    st.code(
                        network_analysis_result.stdout
                    )


                    st.subheader(
                        "Risk Analysis"
                    )

                    st.code(
                        risk_result.stdout
                    )


            except Exception as e:

                st.error(
                    f"❌ Unexpected processing error: {e}"
                )


# ============================================================
# CURRENT INVESTIGATION SELECTION
# ============================================================
# Keep the selected entity available to all downstream dashboard sections.
selected_entity = st.session_state.get("selected_investigation_entity")


# ============================================================
# LOAD OUTPUT DATA
# ============================================================

risk_df = load_csv(
    "risk_analysis.csv"
)

entities_df = load_csv(
    "extracted_entities.csv"
)

relations_df = load_csv(
    "extracted_relationships.csv"
)

network_df = load_csv(
    "network_analysis.csv"
)

# ============================================================
# INTELLIGENCE OVERVIEW
# ============================================================

st.header(
    "📊 Intelligence Overview"
)


col1, col2, col3, col4 = st.columns(4)


# Total entities

if (
    entities_df is not None
    and "entity" in entities_df.columns
):

    total_entities = (
        entities_df["entity"]
        .nunique()
    )

else:

    total_entities = 0


# Relationships

if relations_df is not None:

    total_relationships = (
        len(relations_df)
    )

else:

    total_relationships = 0


# High risk

if (
    risk_df is not None
    and "risk_level" in risk_df.columns
):

    high_risk_count = len(
        risk_df[
            risk_df["risk_level"]
            .astype(str)
            .str.upper()
            == "HIGH"
        ]
    )

else:

    high_risk_count = 0


# Repeat FIR

if (
    risk_df is not None
    and "fir_count" in risk_df.columns
):

    repeat_fir_count = len(
        risk_df[
            risk_df["fir_count"] > 1
        ]
    )

else:

    repeat_fir_count = 0


col1.metric(
    "🧩 Total Entities",
    f"{total_entities:,}"
)

col2.metric(
    "🔗 Relationships",
    f"{total_relationships:,}"
)

col3.metric(
    "🚨 High Risk Entities",
    f"{high_risk_count:,}"
)

col4.metric(
    "🔁 Repeat FIR Entities",
    f"{repeat_fir_count:,}"
)


# ============================================================
# RISK INTELLIGENCE
# ============================================================

st.divider()

st.header(
    "⚠️ Risk Intelligence"
)

st.caption(
    "Analytical prioritization based on network relationships, "
    "case recurrence and available investigative evidence. "
    "Risk level does not determine guilt or innocence."
)


if (
    risk_df is not None
    and not risk_df.empty
):

    risk_counts = (
        risk_df["risk_level"]
        .astype(str)
        .str.upper()
        .value_counts()
    )

    low_count = risk_counts.get(
        "LOW",
        0
    )

    medium_count = risk_counts.get(
        "MEDIUM",
        0
    )

    high_count = risk_counts.get(
        "HIGH",
        0
    )

    risk_col1, risk_col2, risk_col3 = (
        st.columns(3)
    )

    with risk_col1:
        st.metric(
            "🟢 Low Risk",
            f"{low_count:,}"
        )

    with risk_col2:
        st.metric(
            "🟡 Medium Risk",
            f"{medium_count:,}"
        )

    with risk_col3:
        st.metric(
            "🔴 High Risk",
            f"{high_count:,}"
        )

else:

    low_count = 0
    medium_count = 0
    high_count = 0

    st.warning(
        "Risk analysis data is not available."
    )


# ============================================================
# HIGH RISK ENTITIES
# ============================================================

st.divider()

st.header(
    "🚨 High Risk Entities"
)

st.caption(
    "Entities requiring higher investigative attention based on "
    "network structure, case recurrence and available evidence."
)


if (
    risk_df is not None
    and not risk_df.empty
):

    high_risk_df = risk_df[
        risk_df["risk_level"]
        .astype(str)
        .str.upper()
        == "HIGH"
    ].copy()


    if not high_risk_df.empty:

        high_risk_df = (
            high_risk_df
            .sort_values(
                "risk_score",
                ascending=False
            )
        )


        st.dataframe(
    high_risk_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "entity": st.column_config.TextColumn(
            "Entity"
        ),
        "risk_score": st.column_config.NumberColumn(
            "Risk Score",
            format="%.2f"
        ),
        "risk_level": st.column_config.TextColumn(
            "Risk Level"
        ),
        "connections": st.column_config.NumberColumn(
            "Connections"
        ),
        "fir_count": st.column_config.NumberColumn(
            "FIR Count"
        ),
        "direct_complainants": st.column_config.NumberColumn(
            "Direct Complainants"
        ),
        "investigative_connections": st.column_config.NumberColumn(
            "Investigative Connections"
        )
    }
)

    else:

        st.success(
            "No HIGH risk entities detected."
        )

else:

    st.warning(
        "Risk analysis file not found."
    )


# ============================================================
# INVESTIGATION INSIGHTS
# ============================================================

st.divider()

st.header(
    "🔍 Investigation Insights"
)


if (
    risk_df is not None
    and not risk_df.empty
):

    insight_col1, insight_col2 = (
        st.columns(2)
    )


    # --------------------------------------------------------
    # RISK DISTRIBUTION
    # --------------------------------------------------------

    with insight_col1:

        st.subheader(
            "📊 Risk Level Distribution"
        )


        risk_chart_df = (
            risk_df["risk_level"]
            .astype(str)
            .str.upper()
            .value_counts()
            .reset_index()
        )


        risk_chart_df.columns = [
            "Risk Level",
            "Count"
        ]


        fig = px.bar(
            risk_chart_df,
            x="Risk Level",
            y="Count",
            title="Entities by Risk Level"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # TOP RISK SCORES
    # --------------------------------------------------------

    with insight_col2:

        st.subheader(
            "🎯 Top Risk Scores"
        )


        if (
            "risk_score" in risk_df.columns
            and "entity" in risk_df.columns
        ):

            top_risk_df = (
                risk_df
                .sort_values(
                    "risk_score",
                    ascending=False
                )
                .head(10)
            )


            fig2 = px.bar(
                top_risk_df,
                x="entity",
                y="risk_score",
                title="Top 10 Risk Scores"
            )


            st.plotly_chart(
                fig2,
                use_container_width=True
            )


    # ========================================================
    # INVESTIGATION PRIORITY
    # ========================================================

    st.subheader(
        "🎯 Investigation Priority List"
    )


    priority_columns = [
        "entity",
        "risk_score",
        "risk_level",
        "fir_count",
        "direct_complainants",
        "investigative_connections",
        "connections"
    ]


    available_priority_columns = [
        column
        for column in priority_columns
        if column in risk_df.columns
    ]


    if available_priority_columns:

        priority_df = (
            risk_df[
                available_priority_columns
            ]
            .sort_values(
                "risk_score",
                ascending=False
            )
            .head(20)
        )


        st.dataframe(
            priority_df,
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # AI INVESTIGATION SUMMARY
    # ========================================================

    st.subheader(
        "🤖 AI Investigation Summary"
    )


    st.info(
        f"""
**Investigation Findings**

• {high_risk_count:,} entities are currently classified as HIGH RISK.

• {medium_count:,} entities are classified as MEDIUM RISK.

• {repeat_fir_count:,} entities appear in more than one FIR.

• Network relationships and entity connectivity are used to calculate investigation priority.

• High-risk entities should be prioritized for further evidence review and investigation.

**Important:** Risk classification represents an analytical priority signal and does not establish guilt or criminal liability.
"""
    )


# ============================================================
# NETWORK ANALYSIS
# ============================================================

st.divider()

st.header(
    "🕸️ Network Analysis"
)


if (
    network_df is not None
    and not network_df.empty
):

    st.caption(
    "Top entities ranked using network influence metrics. "
    "Degree centrality highlights highly connected entities, "
    "betweenness identifies bridge entities, PageRank measures "
    "network importance, and the influence score combines these "
    "signals for investigative prioritization."
)


    network_columns = [
        "entity",
        "degree_centrality",
        "betweenness_centrality",
        "pagerank",
        "influence_score"
    ]


    available_network_columns = [
        column
        for column in network_columns
        if column in network_df.columns
    ]


    st.dataframe(
    network_df[
        available_network_columns
    ].head(20),
    use_container_width=True,
    hide_index=True,
    column_config={
        "entity": st.column_config.TextColumn(
            "Entity"
        ),
        "degree_centrality": st.column_config.NumberColumn(
            "Degree Centrality",
            format="%.4f"
        ),
        "betweenness_centrality": st.column_config.NumberColumn(
            "Betweenness Centrality",
            format="%.4f"
        ),
        "pagerank": st.column_config.NumberColumn(
            "PageRank",
            format="%.4f"
        ),
        "influence_score": st.column_config.NumberColumn(
            "Influence Score",
            format="%.2f"
        )
    }
)

else:

    st.warning(
        "Network analysis data is not available."
    )


# ============================================================
# ENTITY EXPLORER
# ============================================================
st.header("🔎 Entity Explorer")

try:

    from src.api.investigator_api import InvestigatorAPI

    investigator_api = InvestigatorAPI()

    search_entity = st.text_input(
        "Search for an entity",
        placeholder=(
            "Enter person, location, organisation, "
            "police station, crime category, etc."
        ),
        key="investigator_entity_search"
    )

    if search_entity:

        search_results = investigator_api.search_entities(
            search_entity,
            limit=100
        )

        if search_results:

            st.success(
                f"Found {len(search_results):,} "
                "matching entities."
            )

            results_df = pd.DataFrame(
                search_results
            )

            preferred_columns = [
                "entity",
                "entity_type",
                "evidence_count",
                "relationship_count",
                "risk_score",
                "risk_level",
                "traceable_evidence_count"
            ]

            available_columns = [
                column
                for column in preferred_columns
                if column in results_df.columns
            ]

            if available_columns:

                display_df = results_df[
                    available_columns
                ].copy()

            else:

                display_df = results_df

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            # ==========================================
            # SELECT ENTITY
            # ==========================================

            entity_names = results_df[
                "entity"
            ].astype(str).tolist()

            selected_entity = st.selectbox(
    "🔎 Select an entity to investigate",
    entity_names,
    key="selected_investigation_entity",
    help="Choose an entity to view its evidence, risk profile, relationships and investigation network."
)

            if selected_entity:

                investigation = (
                    investigator_api.search_entity(
                        selected_entity
                    )
                )

                if investigation:

                    # ==================================
                    # INVESTIGATION WORKSPACE
                    # ==================================

                    st.subheader(
                        f"📋 Investigation Workspace — "
                        f"{selected_entity}"
                    )

                    # ==================================
                    # ENTITY OVERVIEW
                    # ==================================

                    st.markdown(
                        "### 👤 Entity Overview"
                    )

                    col1, col2, col3, col4 = (
                        st.columns(4)
                    )

                    with col1:

                        st.metric(
                            "Entity Type",
                            investigation.get(
                                "entity_type",
                                "UNKNOWN"
                            )
                        )

                    with col2:

                        st.metric(
                            "Evidence Records",
                            investigation.get(
                                "evidence_count",
                                0
                            )
                        )

                    with col3:

                        st.metric(
                            "Relationships",
                            investigation.get(
                                "relationship_count",
                                0
                            )
                        )

                    with col4:

                        risk_score = investigation.get(
                            "risk_score",
                            0
                        )

                        try:

                            if pd.notna(risk_score):

                                risk_score_display = (
                                    f"{float(risk_score):.2f}"
                                )

                            else:

                                risk_score_display = "N/A"

                        except (
                            ValueError,
                            TypeError
                        ):

                            risk_score_display = str(
                                risk_score
                            )

                        st.metric(
                            "Risk Score",
                            risk_score_display
                        )

                    # ==================================
                    # RISK ASSESSMENT
                    # ==================================

                    risk_level = investigation.get(
                        "risk_level",
                        "UNKNOWN"
                    )

                    st.markdown(
                        "### ⚠️ Risk Assessment"
                    )

                    if (
                        pd.notna(risk_level)
                        and str(risk_level).upper()
                        == "HIGH"
                    ):

                        st.error(
                            f"🔴 HIGH PRIORITY — "
                            f"{selected_entity}"
                        )

                    elif (
                        pd.notna(risk_level)
                        and str(risk_level).upper()
                        == "MEDIUM"
                    ):

                        st.warning(
                            f"🟠 MEDIUM PRIORITY — "
                            f"{selected_entity}"
                        )

                    else:

                        st.info(
                            f"🟢 "
                            f"{str(risk_level).upper()} "
                            f"PRIORITY — "
                            f"{selected_entity}"
                        )

                    # ==================================
                    # INVESTIGATION SUMMARY
                    # ==================================

                    st.markdown(
                        "### 📊 Investigation Summary"
                    )

                    summary_col1, summary_col2, summary_col3 = (
                        st.columns(3)
                    )

                    with summary_col1:

                        st.metric(
                            "Direct Complainants",
                            investigation.get(
                                "direct_complainants",
                                0
                            )
                        )

                    with summary_col2:

                        st.metric(
                            "Investigative Connections",
                            investigation.get(
                                "investigative_connections",
                                0
                            )
                        )

                    with summary_col3:

                        st.metric(
                            "Traceable Evidence",
                            investigation.get(
                                "traceable_evidence_count",
                                0
                            )
                        )

                    # ==================================
                    # INVESTIGATION TABS
                    # ==================================

                    (
                        tab_profile,
                        tab_evidence,
                        tab_connections,
                        tab_traceability
                    ) = st.tabs(
                        [
                            "👤 Profile",
                            "📄 Evidence",
                            "🔗 Connections",
                            "🧾 Traceability"
                        ]
                    )

                    # ==================================
                    # PROFILE TAB
                    # ==================================

                    with tab_profile:

                        profile_data = {
                            "Entity":
                                investigation.get(
                                    "entity"
                                ),
                            "Entity Type":
                                investigation.get(
                                    "entity_type"
                                ),
                            "Evidence Records":
                                investigation.get(
                                    "evidence_count"
                                ),
                            "Relationships":
                                investigation.get(
                                    "relationship_count"
                                ),
                            "Risk Score":
                                investigation.get(
                                    "risk_score"
                                ),
                            "Risk Level":
                                investigation.get(
                                    "risk_level"
                                ),
                            "Direct Complainants":
                                investigation.get(
                                    "direct_complainants"
                                ),
                            "Investigative Connections":
                                investigation.get(
                                    "investigative_connections"
                                )
                        }

                        profile_df = pd.DataFrame(
                            profile_data.items(),
                            columns=[
                                "Field",
                                "Value"
                            ]
                        )

                        st.dataframe(
                            profile_df,
                            use_container_width=True,
                            hide_index=True
                        )

                    # ==================================
                    # EVIDENCE TAB
                    # ==================================

                    with tab_evidence:

                        st.markdown(
                            "#### 📄 Linked FIR Evidence"
                        )

                        evidence_records = (
                            investigation.get(
                                "evidence_records",
                                ""
                            )
                        )

                        if pd.notna(
                            evidence_records
                        ):

                            evidence_text = str(
                                evidence_records
                            ).strip()

                            if evidence_text:

                                evidence_list = [
                                    item.strip()
                                    for item in
                                    evidence_text.split("|")
                                    if item.strip()
                                ]

                                fir_file = os.path.join(
                                    OUTPUT_FOLDER,
                                    "standardized_fir_data.csv"
                                )

                                if os.path.exists(
                                    fir_file
                                ):

                                    try:

                                        fir_df = pd.read_csv(
                                            fir_file
                                        )

                                        if (
                                            "report_id"
                                            in fir_df.columns
                                        ):

                                            fir_df[
                                                "_record_id"
                                            ] = (
                                                fir_df[
                                                    "report_id"
                                                ]
                                                .astype(str)
                                                .str.strip()
                                            )

                                        elif (
                                            "FIR_No"
                                            in fir_df.columns
                                        ):

                                            fir_df[
                                                "_record_id"
                                            ] = (
                                                fir_df[
                                                    "FIR_No"
                                                ]
                                                .astype(str)
                                                .str.strip()
                                            )

                                        else:

                                            fir_df[
                                                "_record_id"
                                            ] = ""

                                        linked_firs = fir_df[
                                            fir_df[
                                                "_record_id"
                                            ].isin(
                                                evidence_list
                                            )
                                        ].copy()

                                        st.write(
                                            f"**{len(linked_firs):,} "
                                            "linked FIR record(s) found.**"
                                        )

                                        if not linked_firs.empty:

                                            display_columns = [
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

                                            available_fir_columns = [
                                                column
                                                for column
                                                in display_columns
                                                if column
                                                in linked_firs.columns
                                            ]

                                            st.dataframe(
                                                linked_firs[
                                                    available_fir_columns
                                                ],
                                                use_container_width=True,
                                                hide_index=True
                                            )

                                            st.markdown(
                                                "#### 🔍 FIR Details"
                                            )

                                            for _, fir in (
                                                linked_firs.iterrows()
                                            ):

                                                fir_number = fir.get(
                                                    "FIR_No",
                                                    fir.get(
                                                        "report_id",
                                                        "Unknown"
                                                    )
                                                )

                                                with st.expander(
                                                    f"📄 {fir_number}"
                                                ):

                                                    detail_col1, detail_col2 = (
                                                        st.columns(2)
                                                    )

                                                    with detail_col1:

                                                        st.write(
                                                            "**Date Filed:**",
                                                            fir.get(
                                                                "Date_Filed",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**State:**",
                                                            fir.get(
                                                                "State",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**District:**",
                                                            fir.get(
                                                                "District",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**Police Station:**",
                                                            fir.get(
                                                                "Police_Station",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**Crime Category:**",
                                                            fir.get(
                                                                "Crime_Category",
                                                                "N/A"
                                                            )
                                                        )

                                                    with detail_col2:

                                                        st.write(
                                                            "**Complainant:**",
                                                            fir.get(
                                                                "Complainant_Name",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**Accused:**",
                                                            fir.get(
                                                                "Accused_Name",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**Legal Section:**",
                                                            fir.get(
                                                                "Legal_Section",
                                                                "N/A"
                                                            )
                                                        )

                                                        st.write(
                                                            "**Case Status:**",
                                                            fir.get(
                                                                "Case_Status",
                                                                "N/A"
                                                            )
                                                        )

                                                    st.markdown(
                                                        "**Incident Description**"
                                                    )

                                                    st.write(
                                                        fir.get(
                                                            "Incident_Description",
                                                            "No description available."
                                                        )
                                                    )

                                        else:

                                            st.warning(
                                                "Evidence IDs were found, "
                                                "but matching FIR records "
                                                "were not found."
                                            )

                                    except Exception as e:

                                        st.error(
                                            f"Unable to load FIR evidence: {e}"
                                        )

                                else:

                                    st.warning(
                                        "Standardized FIR evidence "
                                        "file is not available."
                                    )

                            else:

                                st.info(
                                    "No linked evidence records found."
                                )

                        else:

                            st.info(
                                "No linked evidence records found."
                            )

                   

                    # ==================================
                    # CONNECTIONS TAB
                    # ==================================

                    with tab_connections:

                        st.markdown(
                            "#### 🔗 Connected Entities"
                        )

                        connected_entities = (
                            investigation.get(
                                "connected_entities",
                                ""
                            )
                        )

                        if pd.notna(
                            connected_entities
                        ):

                            connection_text = str(
                                connected_entities
                            ).strip()

                            if connection_text:

                                connection_list = [
                                    item.strip()
                                    for item in connection_text.split("|")
                                    if item.strip()
                                ]

                                st.write(
                                    f"**{len(connection_list):,} "
                                    "connected entities identified.**"
                                )

                                # ------------------------------------------
                                # INTERACTIVE CONNECTION SELECTOR
                                # ------------------------------------------

                                connection_options = [
                                    entity
                                    for entity in connection_list
                                    if entity != selected_entity
                                ]

                                if connection_options:

                                    selected_connection = st.selectbox(
                                        "Select a connected entity to investigate",
                                        connection_options,
                                        key=(
                                            "connected_entity_selector_"
                                            + str(selected_entity)
                                        )
                                    )

                                    if selected_connection:

                                        st.markdown(
                                            f"### 🔍 {selected_connection}"
                                        )

                                        investigate_connection = st.button(
                                            "Investigate Connected Entity",
                                            key=(
                                                "investigate_connection_"
                                                + str(selected_entity)
                                                + "_"
                                                + str(selected_connection)
                                            )
                                        )

                                        if investigate_connection:

                                            try:

                                                connected_investigation = (
                                                    investigator_api.search_entity(
                                                        selected_connection
                                                    )
                                                )

                                                if connected_investigation:

                                                    st.success(
                                                        "Connected entity profile "
                                                        "loaded successfully."
                                                    )

                                                    connection_col1, connection_col2, connection_col3 = (
                                                        st.columns(3)
                                                    )

                                                    with connection_col1:

                                                        st.metric(
                                                            "Entity Type",
                                                            connected_investigation.get(
                                                                "entity_type",
                                                                "UNKNOWN"
                                                            )
                                                        )

                                                    with connection_col2:

                                                        st.metric(
                                                            "Evidence Records",
                                                            connected_investigation.get(
                                                                "evidence_count",
                                                                0
                                                            )
                                                        )

                                                    with connection_col3:

                                                        st.metric(
                                                            "Relationships",
                                                            connected_investigation.get(
                                                                "relationship_count",
                                                                0
                                                            )
                                                        )

                                                    st.markdown(
                                                        "#### 📋 Connected Entity Profile"
                                                    )

                                                    connected_profile = {
                                                        "Entity":
                                                            connected_investigation.get(
                                                                "entity"
                                                            ),
                                                        "Entity Type":
                                                            connected_investigation.get(
                                                                "entity_type"
                                                            ),
                                                        "Evidence Records":
                                                            connected_investigation.get(
                                                                "evidence_count"
                                                            ),
                                                        "Relationships":
                                                            connected_investigation.get(
                                                                "relationship_count"
                                                            ),
                                                        "Risk Score":
                                                            connected_investigation.get(
                                                                "risk_score"
                                                            ),
                                                        "Risk Level":
                                                            connected_investigation.get(
                                                                "risk_level"
                                                            ),
                                                        "Direct Complainants":
                                                            connected_investigation.get(
                                                                "direct_complainants"
                                                            ),
                                                        "Investigative Connections":
                                                            connected_investigation.get(
                                                                "investigative_connections"
                                                            )
                                                    }

                                                    connected_profile_df = pd.DataFrame(
                                                        connected_profile.items(),
                                                        columns=[
                                                            "Field",
                                                            "Value"
                                                        ]
                                                    )

                                                    st.dataframe(
                                                        connected_profile_df,
                                                        use_container_width=True,
                                                        hide_index=True
                                                    )

                                                    # ----------------------------------
                                                    # CONNECTED ENTITY EVIDENCE
                                                    # ----------------------------------

                                                    st.markdown(
                                                        "#### 📄 Linked Evidence"
                                                    )

                                                    connected_evidence = (
                                                        connected_investigation.get(
                                                            "evidence_records",
                                                            ""
                                                        )
                                                    )

                                                    if pd.notna(
                                                        connected_evidence
                                                    ):

                                                        connected_evidence_text = str(
                                                            connected_evidence
                                                        ).strip()

                                                        if connected_evidence_text:

                                                            connected_evidence_list = [
                                                                item.strip()
                                                                for item in connected_evidence_text.split("|")
                                                                if item.strip()
                                                            ]

                                                            connected_evidence_df = pd.DataFrame(
                                                                {
                                                                    "Evidence Record ID":
                                                                        connected_evidence_list
                                                                }
                                                            )

                                                            st.dataframe(
                                                                connected_evidence_df,
                                                                use_container_width=True,
                                                                hide_index=True
                                                            )

                                                        else:

                                                            st.info(
                                                                "No linked evidence found."
                                                            )

                                                    else:

                                                        st.info(
                                                            "No linked evidence found."
                                                        )

                                                else:

                                                    st.warning(
                                                        "Investigation profile for "
                                                        f"{selected_connection} "
                                                        "could not be loaded."
                                                    )

                                            except Exception as connection_error:

                                                st.error(
                                                    "Unable to investigate connected "
                                                    f"entity: {connection_error}"
                                                )

                                else:

                                    st.info(
                                        "No other connected entities available."
                                    )

                            else:

                                st.info(
                                    "No connected entities found."
                                )

                        else:

                            st.info(
                                "No connected entities found."
                            )

                        # ==============================================
                        # RELATIONSHIP TYPES
                        # ==============================================

                        st.markdown(
                            "#### 🔗 Relationship Types"
                        )

                        relationship_types = (
                            investigation.get(
                                "relationship_types",
                                ""
                            )
                        )

                        if pd.notna(
                            relationship_types
                        ):

                            relationship_text = str(
                                relationship_types
                            ).strip()

                            if relationship_text:

                                relationship_list = [
                                    item.strip()
                                    for item in relationship_text.split("|")
                                    if item.strip()
                                ]

                                relationship_df = pd.DataFrame(
                                    {
                                        "Relationship Type":
                                            relationship_list
                                    }
                                )

                                st.dataframe(
                                    relationship_df,
                                    use_container_width=True,
                                    hide_index=True
                                )

                            else:

                                st.info(
                                    "No relationship types found."
                                )

                        else:

                            st.info(
                                "No relationship types found."
                            )

                    # ==================================
                    # TRACEABILITY TAB
                    # ==================================

                    with tab_traceability:

                        st.markdown(
                            "#### 🧾 Evidence Traceability"
                        )

                        st.info(
                            "Every relationship shown by the "
                            "intelligence system must remain "
                            "traceable to its originating "
                            "evidence record."
                        )

                        traceability_data = {
                            "Entity":
                                investigation.get(
                                    "entity"
                                ),
                            "Traceable Evidence":
                                investigation.get(
                                    "traceable_evidence_count"
                                ),
                            "Evidence Records":
                                investigation.get(
                                    "evidence_count"
                                ),
                            "Relationship Count":
                                investigation.get(
                                    "relationship_count"
                                )
                        }

                        traceability_df = pd.DataFrame(
                            traceability_data.items(),
                            columns=[
                                "Field",
                                "Value"
                            ]
                        )

                        st.dataframe(
                            traceability_df,
                            use_container_width=True,
                            hide_index=True
                        )

                        st.success(
                            "Evidence-backed investigation "
                            "context loaded."
                        )

                else:

                    st.warning(
                        "Investigation profile "
                        "could not be loaded."
                    )

        else:

            st.warning(
                f"No entity found matching "
                f"'{search_entity}'."
            )

    else:

        st.info(
            "Search for an entity to begin "
            "an investigation."
        )

except Exception as e:

    st.error(
        f"Investigator API unavailable: {e}"
    )


# ============================================================
# INVESTIGATION TIMELINE
# ============================================================

st.divider()

st.header("🕒 Investigation Timeline")

st.caption(
    "Chronological FIR activity associated with the selected entity."
)

timeline_file = os.path.join(
    OUTPUT_FOLDER,
    "investigation_timeline.csv"
)

# Get the currently selected entity safely
timeline_entity = st.session_state.get(
    "selected_entity",
    selected_entity if "selected_entity" in locals() else None
)

if timeline_entity:

    if os.path.exists(timeline_file):

        try:

            timeline_df = pd.read_csv(
                timeline_file
            )

            timeline_df["event_date"] = pd.to_datetime(
                timeline_df["event_date"],
                errors="coerce"
            )

            entity_timeline = timeline_df[
                timeline_df["entity"].astype(str).str.casefold()
                == str(timeline_entity).casefold()
            ].copy()

            entity_timeline = entity_timeline.sort_values(
                by="event_date"
            )

            if not entity_timeline.empty:

                st.success(
                    f"Timeline loaded for **{timeline_entity}**."
                )

                st.write(
                    f"**{len(entity_timeline)} FIR event(s)** found."
                )

                display_timeline = entity_timeline[
                    [
                        "event_date",
                        "FIR_No",
                        "event_type",
                        "Crime_Category",
                        "Legal_Section",
                        "State",
                        "District",
                        "Police_Station",
                        "Case_Status"
                    ]
                ].copy()

                display_timeline["event_date"] = (
                    display_timeline["event_date"]
                    .dt.strftime("%d %b %Y")
                )

                display_timeline = display_timeline.rename(
                    columns={
                        "event_date": "Date",
                        "FIR_No": "FIR",
                        "event_type": "Event",
                        "Crime_Category": "Crime Category",
                        "Legal_Section": "Legal Section",
                        "State": "State",
                        "District": "District",
                        "Police_Station": "Police Station",
                        "Case_Status": "Case Status"
                    }
                )

                st.dataframe(
                    display_timeline,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader(
                    "Chronological Evidence Events"
                )

                for _, event in entity_timeline.iterrows():

                    event_date = event["event_date"]

                    if pd.notna(event_date):

                        formatted_date = (
                            event_date.strftime("%d %B %Y")
                        )

                    else:

                        formatted_date = "Unknown date"

                    with st.expander(
                        f"📌 {formatted_date} — "
                        f"{event['FIR_No']} — "
                        f"{event['Crime_Category']}"
                    ):

                        timeline_col1, timeline_col2 = (
                            st.columns(2)
                        )

                        with timeline_col1:

                            st.write(
                                f"**FIR:** {event['FIR_No']}"
                            )

                            st.write(
                                f"**Date:** {formatted_date}"
                            )

                            st.write(
                                f"**Crime Category:** "
                                f"{event['Crime_Category']}"
                            )

                            st.write(
                                f"**Legal Section:** "
                                f"{event['Legal_Section']}"
                            )

                        with timeline_col2:

                            st.write(
                                f"**State:** {event['State']}"
                            )

                            st.write(
                                f"**District:** {event['District']}"
                            )

                            st.write(
                                f"**Police Station:** "
                                f"{event['Police_Station']}"
                            )

                            st.write(
                                f"**Case Status:** "
                                f"{event['Case_Status']}"
                            )

            else:

                st.info(
                    f"No timeline events found for "
                    f"**{timeline_entity}**."
                )

        except Exception as timeline_error:

            st.error(
                "Unable to load investigation timeline: "
                f"{timeline_error}"
            )

    else:

        st.warning(
            "Investigation timeline has not been generated yet."
        )

else:

    st.info(
        "Select an entity in Entity Explorer to view its timeline."
    )

# ============================================================
# AI INVESTIGATION ASSISTANT
# ============================================================

st.divider()

st.header("🤖 AI Investigation Assistant")

st.caption(
    "Evidence-grounded analytical assistance for the selected entity."
)

try:

    from src.ai.investigation_assistant import (
        InvestigationAssistant
    )

    ai_assistant = InvestigationAssistant()

    ai_question = st.text_input(
        "Ask an investigation question",
        placeholder=(
            "Example: Why is this entity high risk?"
        ),
        key="ai_investigation_question"
    )

    if st.button(
        "🤖 Analyze",
        use_container_width=True,
        key="ai_analyze_button"
    ):

        if not selected_entity:
            st.warning("Please select an entity in Entity Explorer first.")
        elif not ai_question.strip():

            st.warning(
                "Please enter an investigation question."
            )

        else:

            with st.spinner(
                "Analyzing available evidence..."
            ):

                ai_answer = ai_assistant.answer(
                    selected_entity,
                    ai_question
                )

            st.subheader("Investigation Analysis")

            st.info(
                ai_answer
            )

            st.caption(
                "⚠️ AI output is an analytical aid based on "
                "available evidence. It does not determine guilt "
                "or innocence."
            )

except Exception as ai_error:

    st.error(
        "Unable to load AI Investigation Assistant: "
        f"{ai_error}"
    )
# ============================================================
# ENTITY INVESTIGATION NETWORK
# ============================================================

st.divider()

st.header("🌐 Entity Investigation Network")

st.caption(
    "Interactive focused network for exploring evidence-supported "
    "relationships around a selected entity."
)

st.info(
    "Use Depth 1 for direct connections or Depth 2 to explore "
    "second-level connections."
)

network_col1, network_col2 = st.columns([1, 3])

with network_col1:

    network_depth = st.selectbox(
        "Network depth",
        [1, 2],
        index=0,
        help=(
            "Depth 1 shows direct connections. "
            "Depth 2 expands the investigation to second-level connections."
        ),
        key="investigation_network_depth"
    )

    build_network_button = st.button(
        "🔍 Build Investigation Network",
        use_container_width=True,
        key="build_investigation_network"
    )

with network_col2:

    if selected_entity:
        st.info(
            f"Ready to build a focused investigation network for **{selected_entity}**."
        )
    else:
        st.info(
            "Select an entity above and build its focused investigation network."
        )


if build_network_button and not selected_entity:
    st.warning("Please select an entity in Entity Explorer first.")


if build_network_button and selected_entity:

    try:

        from src.graph.investigation_network import build_entity_network

        with st.spinner(
            f"Building investigation network for {selected_entity}..."
        ):

            network_path = build_entity_network(
                selected_entity,
                depth=network_depth,
                max_neighbors=100
            )

        st.session_state["investigation_network_path"] = network_path

        st.session_state["investigation_network_entity"] = selected_entity

        st.success(
    f"Investigation network built successfully for **{selected_entity}** "
    f"using Depth {network_depth}."
)

    except Exception as network_error:

        st.error(
            "Unable to build investigation network: "
            f"{network_error}"
        )


network_path = st.session_state.get(
    "investigation_network_path"
)

network_entity = st.session_state.get(
    "investigation_network_entity"
)


if (
    network_path
    and network_entity == selected_entity
    and os.path.exists(network_path)
):

    try:

        with open(
            network_path,
            "r",
            encoding="utf-8"
        ) as network_file:

            network_html = network_file.read()

        st.caption(
    f"Showing the focused investigation network for **{selected_entity}**."
)

        components.html(
            network_html,
            height=750,
            scrolling=True
        )

    except Exception as network_display_error:

        st.error(
            "Unable to display investigation network: "
            f"{network_display_error}"
        )


 # ==========================================
# CDR INTELLIGENCE
# ==========================================

st.header("📞 CDR Intelligence")

try:
    cdr_intelligence_file = "output/cdr_intelligence.csv"

    if not os.path.exists(cdr_intelligence_file):

        st.warning(
            "CDR intelligence data is not available. "
            "Please upload and process a CDR dataset first."
        )

    else:

        cdr_intelligence = pd.read_csv(
            cdr_intelligence_file
        )

        if cdr_intelligence.empty:

            st.info(
                "No CDR intelligence records are available."
            )

        elif "entity" not in cdr_intelligence.columns:

            st.error(
                "Invalid CDR intelligence file: "
                "'entity' column is missing."
            )

        else:

            # -------------------------------------------------
            # STANDALONE CDR ENTITY SELECTION
            # -------------------------------------------------

            cdr_entities = (
                cdr_intelligence["entity"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            cdr_entities = sorted(cdr_entities)

            st.subheader(
                "🔎 Select CDR Subscriber"
            )

            selected_cdr_entity = st.selectbox(
                "CDR Subscriber ID",
                cdr_entities,
                key="selected_cdr_entity"
            )

            # -------------------------------------------------
            # CDR INTELLIGENCE
            # -------------------------------------------------

            cdr_match = cdr_intelligence[
                cdr_intelligence["entity"]
                .astype(str)
                .str.strip()
                == selected_cdr_entity
            ]

            if not cdr_match.empty:

                cdr_record = (
                    cdr_match.iloc[0]
                )

                st.subheader(
                    f"Communication Intelligence — "
                    f"{selected_cdr_entity}"
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total Calls",
                    int(
                        cdr_record.get(
                            "total_calls",
                            0
                        )
                    )
                )

                col2.metric(
                    "Unique Contacts",
                    int(
                        cdr_record.get(
                            "unique_contacts",
                            0
                        )
                    )
                )

                col3.metric(
                    "Outgoing Calls",
                    int(
                        cdr_record.get(
                            "outgoing_calls",
                            0
                        )
                    )
                )

                col4.metric(
                    "Incoming Calls",
                    int(
                        cdr_record.get(
                            "incoming_calls",
                            0
                        )
                    )
                )

                st.metric(
                    "CDR Activity Score",
                    round(
                        float(
                            cdr_record.get(
                                "cdr_activity_score",
                                0
                            )
                        ),
                        2
                    )
                )

                # -------------------------------------------------
                # COMMUNICATION CONNECTIONS
                # -------------------------------------------------

                st.subheader(
                    "📡 Communication Connections"
                )

                try:

                    from src.api.investigator_api import (
                        InvestigatorAPI
                    )

                    cdr_api = InvestigatorAPI()

                    cdr_connections = (
                        cdr_api.get_cdr_connections(
                            selected_cdr_entity,
                            limit=20
                        )
                    )

                    if cdr_connections:

                        cdr_connections_df = (
                            pd.DataFrame(
                                cdr_connections
                            )
                        )

                        display_columns = [
                            column
                            for column in [
                                "source",
                                "target",
                                "relationship",
                                "record_id",
                                "evidence_type"
                            ]
                            if column
                            in cdr_connections_df.columns
                        ]

                        st.dataframe(
                            cdr_connections_df[
                                display_columns
                            ],
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.info(
                            "No communication connections "
                            "found for this subscriber."
                        )

                except Exception as connection_error:

                    st.warning(
                        "Unable to load CDR connections: "
                        f"{connection_error}"
                    )

            else:

                st.info(
                    "No CDR intelligence found for "
                    f"{selected_cdr_entity}."
                )

except Exception as cdr_error:

    st.error(
        f"CDR Intelligence error: {cdr_error}"
    ) 
    # ==========================================
# SOCIAL MEDIA INTELLIGENCE
# ==========================================

st.header("📱 Social Media Intelligence")

try:
    social_media_file = "output/normalized_social_media.csv"
    social_media_relationship_file = (
        "output/social_media_relationships.csv"
    )

    if not os.path.exists(social_media_file):

        st.warning(
            "Social Media intelligence data is not available. "
            "Please upload and process a Social Media dataset first."
        )

    else:

        social_media_df = pd.read_csv(
            social_media_file
        )

        if social_media_df.empty:

            st.info(
                "No Social Media intelligence records are available."
            )

        else:

            # -------------------------------------------------
            # SOCIAL MEDIA OVERVIEW
            # -------------------------------------------------

            st.subheader("📊 Social Media Overview")

            total_posts = len(social_media_df)

            unique_users = (
                social_media_df["username"]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .nunique()
            )

            total_mentions = 0
            total_hashtags = 0
            total_organizations = 0

            for value in social_media_df["mentions"]:
                if pd.notna(value) and str(value).strip():
                    total_mentions += len(
                        [
                            x for x in str(value).replace(";", ",").split(",")
                            if x.strip()
                        ]
                    )

            for value in social_media_df["hashtags"]:
                if pd.notna(value) and str(value).strip():
                    total_hashtags += len(
                        [
                            x for x in str(value).replace(";", ",").split(",")
                            if x.strip()
                        ]
                    )

            for value in social_media_df["organizations"]:
                if pd.notna(value) and str(value).strip():
                    total_organizations += len(
                        [
                            x for x in str(value).replace(";", ",").split(",")
                            if x.strip()
                        ]
                    )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total Posts",
                total_posts
            )

            col2.metric(
                "Unique Users",
                unique_users
            )

            col3.metric(
                "Mentions",
                total_mentions
            )

            col4.metric(
                "Hashtags",
                total_hashtags
            )

            col5, col6 = st.columns(2)

            col5.metric(
                "Organizations Referenced",
                total_organizations
            )

            col6.metric(
                "Locations",
                social_media_df["location"]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .nunique()
            )

            # -------------------------------------------------
            # SOCIAL MEDIA USER SELECTION
            # -------------------------------------------------

            social_users = (
                social_media_df["username"]
                .dropna()
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()
            )

            social_users = sorted(social_users)

            st.subheader(
                "🔎 Select Social Media User"
            )

            selected_social_user = st.selectbox(
                "Social Media User",
                social_users,
                key="selected_social_media_user"
            )

            # -------------------------------------------------
            # SELECTED USER INTELLIGENCE
            # -------------------------------------------------

            user_posts = social_media_df[
                social_media_df["username"]
                .astype(str)
                .str.strip()
                == selected_social_user
            ]

            if not user_posts.empty:

                st.subheader(
                    f"📱 Social Media Intelligence — "
                    f"{selected_social_user}"
                )

                user_post_count = len(user_posts)

                user_locations = (
                    user_posts["location"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .replace("", pd.NA)
                    .dropna()
                    .unique()
                    .tolist()
                )

                user_mentions = []

                for value in user_posts["mentions"]:
                    if pd.notna(value) and str(value).strip():
                        user_mentions.extend(
                            [
                                x.strip().lstrip("@")
                                for x in str(value)
                                .replace(";", ",")
                                .split(",")
                                if x.strip()
                            ]
                        )

                user_hashtags = []

                for value in user_posts["hashtags"]:
                    if pd.notna(value) and str(value).strip():
                        user_hashtags.extend(
                            [
                                x.strip()
                                for x in str(value)
                                .replace(";", ",")
                                .split(",")
                                if x.strip()
                            ]
                        )

                user_organizations = []

                for value in user_posts["organizations"]:
                    if pd.notna(value) and str(value).strip():
                        user_organizations.extend(
                            [
                                x.strip()
                                for x in str(value)
                                .replace(";", ",")
                                .split(",")
                                if x.strip()
                            ]
                        )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Posts",
                    user_post_count
                )

                col2.metric(
                    "Mentions",
                    len(user_mentions)
                )

                col3.metric(
                    "Hashtags",
                    len(user_hashtags)
                )

                col4.metric(
                    "Locations",
                    len(user_locations)
                )

                # -------------------------------------------------
                # USER EVIDENCE
                # -------------------------------------------------

                st.subheader(
                    "📝 Social Media Evidence"
                )

                evidence_columns = [
                    column
                    for column in [
                        "post_id",
                        "username",
                        "post_text",
                        "timestamp",
                        "location",
                        "mentions",
                        "hashtags",
                        "organizations"
                    ]
                    if column in user_posts.columns
                ]

                st.dataframe(
                    user_posts[evidence_columns],
                    use_container_width=True,
                    hide_index=True
                )

                # -------------------------------------------------
                # SOCIAL MEDIA CONNECTIONS
                # -------------------------------------------------

                st.subheader(
                    "👥 Direct Social Media Connections"
                )

                if os.path.exists(
                    social_media_relationship_file
                ):

                    social_relationships = pd.read_csv(
                        social_media_relationship_file
                    )

                    user_connections = social_relationships[
                        (
                            social_relationships["source"]
                            .astype(str)
                            .str.strip()
                            == selected_social_user
                        )
                        |
                        (
                            social_relationships["target"]
                            .astype(str)
                            .str.strip()
                            == selected_social_user
                        )
                    ].copy()

                    # Only explicit user-to-user mentions are treated
                    # as direct Social Media connections.
                    user_connections = user_connections[
                        user_connections["relationship"] == "MENTIONS"
                    ]

                    if not user_connections.empty:

                        st.dataframe(
                            user_connections[
                                [
                                    "source",
                                    "relationship",
                                    "target"
                                ]
                            ],
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.info(
                            "No explicit user-to-user Social Media connections "
                            "were found for this user."
                        )

                else:

                    st.info(
                        "Social Media relationship data "
                        "is not available."
                    )

            else:

                st.info(
                    "No Social Media intelligence found for "
                    f"{selected_social_user}."
                )
                st.subheader("📊 Social Media Activity")

                activity_relationships = social_relationships[
                    social_relationships["relationship"].isin(
                        [
                            "POSTS",
                            "USES_HASHTAG",
                            "REFERENCES"
                        ]
                    )
                    &
                    (
                        social_relationships["source"]
                        .astype(str)
                        .str.strip()
                        == selected_social_user
                    )
                ].copy()

                if not activity_relationships.empty:
                    st.dataframe(
                        activity_relationships[
                            [
                                "source",
                                "relationship",
                                "target"
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(
                        "No Social Media activity records "
                        "were found for this user."
                    )

except Exception as social_media_error:

    st.error(
        f"Social Media Intelligence error: "
        f"{social_media_error}"
    )  
 # ==========================================
# FIR + CDR CORRELATION
# ==========================================

st.header("🔗 FIR + CDR Correlation")

try:

    correlation_file = "output/fir_cdr_correlation.csv"

    if not os.path.exists(correlation_file):

        st.warning(
            "FIR + CDR correlation data is not available."
        )

    else:

        correlation_df = pd.read_csv(
            correlation_file
        )

        if correlation_df.empty:

            st.info(
                "No FIR + CDR correlations are currently available."
            )

        else:

            st.subheader(
                "🔎 Select Correlated Entity"
            )

            correlation_entities = (
                correlation_df["fir_entity"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            correlation_entities = sorted(
                correlation_entities
            )

            selected_correlation_entity = st.selectbox(
                "FIR Entity",
                correlation_entities,
                key="selected_correlation_entity"
            )

            selected_correlation = correlation_df[
                correlation_df["fir_entity"]
                .astype(str)
                .str.strip()
                ==
                selected_correlation_entity
            ]

            if not selected_correlation.empty:

                record = (
                    selected_correlation.iloc[0]
                )

                # ------------------------------------------
                # IDENTITY LINK
                # ------------------------------------------

                st.subheader(
                    "🧩 Identity Resolution"
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "FIR Entity",
                    record["fir_entity"]
                )

                col2.metric(
                    "CDR Subscriber",
                    record["subscriber_id"]
                )

                col3.metric(
                    "Mapping Status",
                    record["mapping_status"]
                )

                st.caption(
                    "Mapping source: "
                    f"{record['mapping_source']}"
                )

                # ------------------------------------------
                # FIR INTELLIGENCE
                # ------------------------------------------

                st.subheader(
                    "📁 FIR Intelligence"
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "FIR Evidence",
                    int(record["fir_evidence_count"])
                )

                col2.metric(
                    "FIR Relationships",
                    int(record["fir_relationship_count"])
                )

                col3.metric(
                    "Risk Score",
                    round(
                        float(record["fir_risk_score"]),
                        2
                    )
                )

                col4.metric(
                    "Risk Level",
                    record["fir_risk_level"]
                )

                # ------------------------------------------
                # CDR INTELLIGENCE
                # ------------------------------------------

                st.subheader(
                    "📞 CDR Intelligence"
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total Calls",
                    int(record["cdr_total_calls"])
                )

                col2.metric(
                    "Unique Contacts",
                    int(record["cdr_unique_contacts"])
                )

                col3.metric(
                    "Outgoing Calls",
                    int(record["cdr_outgoing_calls"])
                )

                col4.metric(
                    "Incoming Calls",
                    int(record["cdr_incoming_calls"])
                )

                st.metric(
                    "CDR Activity Score",
                    round(
                        float(
                            record["cdr_activity_score"]
                        ),
                        2
                    )
                )

                # ------------------------------------------
                # TRACEABILITY
                # ------------------------------------------

                st.subheader(
                    "🔍 Evidence Traceability"
                )

                st.metric(
                    "Traceable FIR Evidence",
                    int(
                        record[
                            "traceable_evidence_count"
                        ]
                    )
                )

                # ------------------------------------------
                # ANALYTICAL DISCLAIMER
                # ------------------------------------------

                st.info(
                    "⚠️ Analytical aid only: "
                    "the FIR and CDR information shown here "
                    "is correlated using the displayed identity "
                    "mapping status. This correlation does not "
                    "establish guilt or ownership."
                )
                # ------------------------------------------
                # CDR COMMUNICATION CONNECTIONS
                # ------------------------------------------

                st.subheader(
                    "📡 CDR Communication Connections"
                )

                cdr_relationship_file = (
                    "output/normalized_cdr_relationships.csv"
                )

                if os.path.exists(cdr_relationship_file):

                    cdr_relationships = pd.read_csv(
                        cdr_relationship_file
                    )

                    subscriber_id = str(
                        record["subscriber_id"]
                    ).strip()

                    required_columns = {
                        "source",
                        "target",
                        "relationship",
                        "record_id",
                        "evidence_type"
                    }

                    if required_columns.issubset(
                        cdr_relationships.columns
                    ):

                        source_matches = (
                            cdr_relationships["source"]
                            .astype(str)
                            .str.strip()
                            .str.lower()
                            == subscriber_id.lower()
                        )

                        target_matches = (
                            cdr_relationships["target"]
                            .astype(str)
                            .str.strip()
                            .str.lower()
                            == subscriber_id.lower()
                        )

                        cdr_connections = (
                            cdr_relationships[
                                source_matches
                                | target_matches
                            ]
                            .copy()
                        )

                        if not cdr_connections.empty:

                            display_columns = [
                                "source",
                                "target",
                                "relationship",
                                "record_id",
                                "evidence_type"
                            ]

                            cdr_connections = (
                                cdr_connections[
                                    display_columns
                                ]
                                .head(50)
                            )

                            st.dataframe(
                                cdr_connections,
                                use_container_width=True,
                                hide_index=True
                            )

                            st.caption(
                                "Showing up to 50 communication "
                                "relationships linked to the "
                                "mapped CDR subscriber."
                            )

                        else:

                            st.info(
                                "No communication connections "
                                "found for this subscriber."
                            )

                    else:

                        st.warning(
                            "CDR relationship file has an "
                            "unexpected schema."
                        )

                else:

                    st.warning(
                        "CDR relationship data is not available."
                    )

            else:

                st.info(
                    "No FIR + CDR correlation found for "
                    f"{selected_correlation_entity}."
                )

except Exception as correlation_error:

    st.error(
        "FIR + CDR Correlation error: "
        f"{correlation_error}"
    )      
# ============================================================
# CRIMINAL NETWORK VISUALIZATION
# ============================================================

st.divider()

st.header("🌐 Criminal Network Visualization")

network_file = os.path.join(
    OUTPUT_FOLDER,
    "criminal_network.html"
)

if os.path.exists(network_file):

    st.success(
        "Interactive criminal network loaded successfully."
    )

    st.caption(
        "Use the network to explore relationships between "
        "entities identified from FIR evidence."
    )

    try:

        with open(
            network_file,
            "r",
            encoding="utf-8"
        ) as f:

            html_data = f.read()

        components.html(
            html_data,
            height=800,
            scrolling=True
        )

    except Exception as e:

        st.error(
            f"Unable to load network visualization: {e}"
        )

else:

    st.warning(
        "Network visualization file not found. "
        "Run the network construction and visualization pipeline first."
    )
# ==========================================
# TRANSACTION INTELLIGENCE
# ==========================================

st.header("💳 Transaction Intelligence")

try:

    transaction_intelligence_file = (
        "output/transaction_intelligence.csv"
    )

    if not os.path.exists(
        transaction_intelligence_file
    ):

        st.info(
            "ℹ️ Transaction intelligence data is not available yet. "
            "Upload and process a transaction CSV to activate this module."
        )

    else:

        transaction_df = pd.read_csv(
            transaction_intelligence_file
        )

        if transaction_df.empty:

            st.info(
                "ℹ️ Transaction intelligence data is currently empty."
            )

        else:

            # --------------------------------------------------
            # TRANSACTION ENTITY SELECTION
            # --------------------------------------------------

            transaction_entities = sorted(
                transaction_df["entity"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            if transaction_entities:

                selected_transaction_entity = st.selectbox(
                    "Select Transaction Entity",
                    transaction_entities
                )

                selected_transaction = transaction_df[
                    transaction_df["entity"]
                    == selected_transaction_entity
                ]

                # --------------------------------------------------
                # TRANSACTION METRICS
                # --------------------------------------------------

                if not selected_transaction.empty:

                    row = selected_transaction.iloc[0]

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "💳 Transactions",
                        int(
                            row.get(
                                "transaction_count",
                                0
                            )
                        )
                    )

                    col2.metric(
                        "👥 Unique Contacts",
                        int(
                            row.get(
                                "unique_contacts",
                                0
                            )
                        )
                    )

                    col3.metric(
                        "📤 Outgoing",
                        int(
                            row.get(
                                "outgoing_transactions",
                                0
                            )
                        )
                    )

                    col4.metric(
                        "📥 Incoming",
                        int(
                            row.get(
                                "incoming_transactions",
                                0
                            )
                        )
                    )

                    st.metric(
                        "💰 Total Transaction Value",
                        round(
                            float(
                                row.get(
                                    "total_transaction_value",
                                    0
                                )
                            ),
                            2
                        )
                    )

                    st.metric(
                        "📊 Transaction Activity Score",
                        round(
                            float(
                                row.get(
                                    "transaction_activity_score",
                                    0
                                )
                            ),
                            2
                        )
                    )

            else:

                st.info(
                    "ℹ️ No transaction entities were found."
                )

except Exception as e:

    st.error(
        f"❌ Unable to load transaction intelligence: {e}"
    )
# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Smart India Hackathon Project | "
    "Criminal Intelligence Network Analysis"
)