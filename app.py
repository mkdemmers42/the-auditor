
import re
import math
import base64

from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image


# ============================================================
# THE AUDITOR - Phase 1 Productivity Engine
# Built around Mike's verified workflow.
# ============================================================

APP_TITLE = "The Auditor"
APP_SUBTITLE = "Phase 1: Productivity Engine"

NON_BILLABLE_PROCEDURES = {
    "Client Non Billable Srvc Must Document",
    "Non-billable Attempted Contact",
}

PROCEDURE_CROSSWALK = {
    "Psychosocial Rehab - Individual": "Psychosocial Rehabilitation",
    "TCM/ICC": "Targeted Case Management",
    "Plan Development, non-physician": "Mental Health Service Plan Developed by Non-Physician",
    "Psychosocial Rehab - Group": "Psychosocial Rehabilitation Group",
    "Psychosocial Rehabilitation Group": "Psychosocial Rehabilitation Group",
}

REQUIRED_SERVICE_COLUMNS = {
    "procedure": "Procedure",       # Column C
    "status": "Status",            # Column J
    "service_units": "ServiceUnits" # Column M
}


# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🕵️",
    layout="wide",
)


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
    }
    
    .stApp {
        font-family: 'Montserrat', sans-serif;
        background:
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(135deg, #06101c 0%, #0d1f36 45%, #14324d 100%);
    
        background-size:
            40px 40px,
            40px 40px,
            cover;
    
        color: #f5f7fb;
    }
    
    .auditor-hero,
    .auditor-hero *,
    .metric-card,
    .metric-card * {
        font-family: 'Montserrat', sans-serif !important;
    }

    .stApp {
        background:
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(135deg, #06101c 0%, #0d1f36 45%, #14324d 100%);
    
        background-size:
            40px 40px,
            40px 40px,
            cover;
    
        color: #f5f7fb;
    }

.auditor-hero {
    background:
        linear-gradient(135deg, rgba(0, 255, 255, 0.10), rgba(255,255,255,0.04)),
        radial-gradient(circle at top left, rgba(64, 224, 255, 0.22), transparent 40%);
    border: 1px solid rgba(115, 230, 255, 0.35);
    border-radius: 24px;
    padding: 1.7rem 2rem;
    margin-bottom: 1.4rem;
    box-shadow:
        0 0 28px rgba(0, 217, 255, 0.18),
        inset 0 0 24px rgba(255, 255, 255, 0.04);
    }
    
    .auditor-badge {
        font-size: 0.78rem;
        letter-spacing: 2.5px;
        color: #7ee7ff;
        font-weight: 800;
        margin-bottom: 0.4rem;
    }

    .auditor-title-row {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .auditor-logo {
        width: 116px;
        height: 116px;
        object-fit: contain;
        filter:
            drop-shadow(0 0 12px rgba(0,255,255,0.55))
            drop-shadow(0 0 28px rgba(0,170,255,0.35));
    }
    
    .auditor-title {
        font-size: 4rem;
        font-weight: 950;
        letter-spacing: 3px;
        color: #ffffff;
        text-shadow:
            0 0 12px rgba(126, 231, 255, 0.85),
            0 0 28px rgba(0, 174, 255, 0.45);
        margin-bottom: 0.2rem;
    }
    
    .auditor-subtitle {
        font-size: 1.05rem;
        color: #c9eaff;
        letter-spacing: 0.5px;
    }

    .auditor-tagline {
    margin-top: 0rem;
    font-size: 1rem;
    font-style: italic;
    letter-spacing: 1px;
    color: #7ee7ff;
    text-shadow:
        0 0 10px rgba(126, 231, 255, 0.45);
    }

    .section-box {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 18px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.25);
    }

.metric-card {
    position: relative;
    background: rgba(15, 24, 45, 0.86);
    border-radius: 22px;
    padding: 1.35rem;
    min-height: 135px;
    text-align: center;
    box-shadow:
        0 0 18px rgba(0, 140, 255, 0.12),
        inset 0 0 18px rgba(255,255,255,0.03);
}

.metric-card-blue {
    border: 1px solid rgba(95, 140, 255, 0.75);
    box-shadow: 0 0 20px rgba(95, 140, 255, 0.28);
}

.metric-card-purple {
    border: 1px solid rgba(150, 110, 255, 0.75);
    box-shadow: 0 0 20px rgba(150, 110, 255, 0.28);
}

.metric-card-green {
    border: 1px solid rgba(85, 220, 150, 0.75);
    box-shadow: 0 0 20px rgba(85, 220, 150, 0.28);
}

.metric-card-orange {
    border: 1px solid rgba(255, 160, 70, 0.75);
    box-shadow: 0 0 20px rgba(255, 160, 70, 0.28);
}

.metric-card-red {
    border: 1px solid rgba(255, 90, 110, 0.75);
    box-shadow: 0 0 20px rgba(255, 90, 110, 0.30);
}

.metric-card-white {
    border: 1px solid rgba(255, 255, 255, 0.78);
    box-shadow: 0 0 20px rgba(255, 255, 255, 0.20);
}

.metric-card-pink {
    border: 1px solid rgba(255, 105, 180, 0.80);
    box-shadow: 0 0 20px rgba(255, 105, 180, 0.30);
}

.metric-icon {
    position: absolute;
    top: 18px;
    right: 22px;
    font-size: 1.35rem;
    opacity: 0.85;
}

.metric-label {
    font-size: 0.90rem;
    color: #e7f2ff;
    margin-top: 0.5rem;
    font-weight: 850;
    letter-spacing: 1.3px;
    text-transform: uppercase;
}

.metric-value {
    font-size: 2.65rem;
    font-weight: 950;
    color: #ffffff;
    line-height: 1.05;
    margin-top: 0.7rem;
}

.metric-note {
    font-size: 0.75rem;
    color: #aebed3;
    margin-top: 0.45rem;
}

    .success-box {
        background: rgba(70, 180, 120, 0.16);
        border: 1px solid rgba(70, 180, 120, 0.40);
        border-radius: 14px;
        padding: 0.85rem;
        color: #e9fff2;
    }

    .warning-box {
        background: rgba(255, 70, 70, 0.14);
        border: 1px solid rgba(255, 90, 90, 0.42);
        border-radius: 14px;
        padding: 0.85rem;
        color: #ffe5e5;
        box-shadow: 0 0 18px rgba(255, 70, 70, 0.14);
    }

    .small-muted {
        color: #b9c9dc;
        font-size: 0.88rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1rem;
    }
    
    label,
    .stText,
    .stNumberInput label,
    .stFileUploader label,
    .stSelectbox label,
    .stMultiSelect label,
    .stExpander,
    .streamlit-expanderHeader {
        color: #dcecff !important;
    }
    
    section[data-testid="stFileUploader"] small {
        color: #9fc7ea !important;
    }
      
    div[data-testid="stFileUploaderDropzone"] * {
        color: #000000 !important;
        font-weight: 600;
    }
       
    section[data-testid="stFileUploader"] {
    background: rgba(7, 20, 38, 0.65);
    border: 1px solid rgba(65, 135, 255, 0.55);
    border-radius: 18px;
    padding: 0.85rem;
    }
    
    div[data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px dashed rgba(120, 200, 255, 0.38) !important;
        border-radius: 14px !important;
    }
    
    section[data-testid="stFileUploader"] button {
        background: #f3f6fb !important;
        color: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.75) !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
    }
    
    section[data-testid="stFileUploader"] button * {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    
    section[data-testid="stFileUploader"] small {
        color: #9dccff !important;
        font-weight: 700 !important;
    }

    button[data-testid="stBaseButton-secondary"] {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #b8c7d9 !important;
    font-weight: 800 !important;
    }
    
    button[data-testid="stBaseButton-secondary"] * {
        color: #000000 !important;
        fill: #000000 !important;
    }

    div[data-testid="stAlert"] {
    color: #dcecff !important;
    }

    .audit-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;

    background:
        linear-gradient(
            135deg,
            rgba(10, 20, 40, 0.92),
            rgba(18, 38, 70, 0.88)
        );

    border: 1px solid rgba(120, 220, 255, 0.22);
    border-radius: 26px;

    padding: 1.5rem 2.5rem;
    margin-bottom: 1.5rem;

    box-shadow:
        0 0 24px rgba(0, 140, 255, 0.10),
        inset 0 0 18px rgba(255,255,255,0.03);
}

.audit-banner-item {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;

    text-shadow:
        0 0 10px rgba(255,255,255,0.12);
}

.audit-table {
    width: 80%;
    margin: auto;
    border-collapse: collapse;
    background: rgba(15, 24, 45, 0.78);
    border: 1px solid rgba(120, 220, 255, 0.28);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 0 24px rgba(0, 140, 255, 0.16);
}

.audit-table th {
    background: rgba(255, 255, 255, 0.10);
    color: #eaf6ff;
    padding: 12px;
    text-align: left;
}

.audit-table td {
    color: #ffffff;
    padding: 12px;
    border-top: 1px solid rgba(255,255,255,0.08);
}
    
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helper Functions
# -----------------------------
def normalize_text(value) -> str:
    """Normalize text for stable matching."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_procedure(value) -> str:
    text = normalize_text(value)
    return PROCEDURE_CROSSWALK.get(text, text)


def extract_number(value) -> float:
    """
    Extracts numeric minutes from values like:
    - 60
    - 60.00
    - "60.00 Minutes"
    """
    if pd.isna(value):
        return 0.0

    text = str(value).replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0

    return float(match.group(0))


def extract_client_id(value) -> str:
    text = normalize_text(value)
    match = re.search(r"\((\d+)\)", text)
    if not match:
        return ""
    return match.group(1)


def minutes_to_units(minutes: float) -> int:
    """
    Medicare-style 15-minute unit conversion verified for The Auditor:
    0-7 = 0
    8-22 = 1
    23-37 = 2
    38-52 = 3
    ...
    218-232 = 15
    233+ = 16
    """
    minutes = extract_number(minutes)

    if minutes <= 7:
        return 0

    if minutes >= 233:
        return 16

    return int(math.floor((minutes - 8) / 15) + 1)


def safe_percent(numerator: float, denominator: float) -> float:
    if denominator in (0, 0.0) or pd.isna(denominator):
        return 0.0
    return (numerator / denominator) * 100


def format_number(value: float) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return "0.00"


def format_percent(value: float) -> str:
    try:
        return f"{float(value):,.2f}%"
    except Exception:
        return "0.00%"

def get_productivity_card_style(value: float) -> tuple[str, str]:
    if value >= 50:
        return "green", "✅"
    elif value >= 45:
        return "orange", "⏸️"
    return "red", "❗"

def get_match_card_style(is_match: bool) -> tuple[str, str]:
    if is_match:
        return "green", "✅"
    return "red", "❗"


def values_match(value_1: float, value_2: float, tolerance: float = 0.01) -> bool:
    return abs(float(value_1) - float(value_2)) <= tolerance


def read_excel(uploaded_file) -> pd.DataFrame:
    """Read the first sheet from an uploaded Excel file."""
    return pd.read_excel(uploaded_file)


def read_county_services_invoiced(uploaded_file) -> pd.DataFrame:
    county_df = pd.read_excel(uploaded_file, header=None)

    clean = pd.DataFrame()

    clean["County Client ID"] = county_df.iloc[:, 3].apply(extract_number).astype(int).astype(str)

    clean["County DOS"] = pd.to_datetime(
    county_df.iloc[:, 14],
    errors="coerce"
).dt.strftime("%Y-%m-%d %H:%M")

    clean["County Procedure"] = county_df.iloc[:, 15].apply(normalize_procedure)

    clean["County Units"] = county_df.iloc[:, 18].apply(extract_number)

    clean["County Minutes"] = county_df.iloc[:, 23].apply(extract_number)

    clean["County Rounded Minutes"] = county_df.iloc[:, 27].apply(extract_number)

    clean["Auditor Expected Units"] = clean["County Minutes"].apply(
        minutes_to_units
    )

    clean["Auditor Expected Rounded Minutes"] = (
        clean["Auditor Expected Units"] * 15
    )

    clean["Rounded Minute Difference"] = (
        clean["County Rounded Minutes"]
        - clean["Auditor Expected Rounded Minutes"]
    )

    clean["Unit Difference"] = (
        clean["County Units"]
        - clean["Auditor Expected Units"]
    )

    return clean


def find_required_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    missing = []
    for display_name in REQUIRED_SERVICE_COLUMNS.values():
        if display_name not in df.columns:
            missing.append(display_name)
    return len(missing) == 0, missing


def calculate_productivity(services_df: pd.DataFrame, hours_worked: float) -> dict:
    """
    Calculates Phase 1 productivity metrics exactly as verified.

    Hours Worked = manual input
    Minutes Worked = Hours Worked x 60

    Minutes Billed:
    - Only Status = Complete
    - Sum ServiceUnits

    Productivity Minutes %:
    - Minutes Billed / Minutes Worked x 100

    Non-Billable Total:
    - Only Procedure in the two verified non-billable procedure names
    - Sum ServiceUnits

    Non-Billable %:
    - Non-Billable Total / Minutes Worked x 100

    Units Billed:
    - Only Status = Complete
    - Convert each ServiceUnits value row-by-row using 15-minute chart
    - Sum units

    Productivity Units %:
    - Rounded minutes from Units Billed / Minutes Worked x 100
    - Rounded minutes = Units Billed x 15
    """
    working = services_df.copy()

    working["_status_clean"] = working["Status"].apply(normalize_text)
    working["_procedure_clean"] = working["Procedure"].apply(normalize_text)
    working["_service_minutes"] = working["ServiceUnits"].apply(extract_number)

    complete_mask = working["_status_clean"].str.casefold() == "complete"

    billable_complete_mask = (
        complete_mask
        & ~working["_procedure_clean"].isin(NON_BILLABLE_PROCEDURES)
    )
    
    completed_services = working.loc[billable_complete_mask].copy()
    minutes_billed = completed_services["_service_minutes"].sum()

    completed_services["_calculated_units"] = completed_services["_service_minutes"].apply(minutes_to_units)
    units_billed = int(completed_services["_calculated_units"].sum())
    rounded_minutes_from_units = units_billed * 15

    non_billable_mask = working["_procedure_clean"].isin(NON_BILLABLE_PROCEDURES)
    non_billable_total = working.loc[non_billable_mask, "_service_minutes"].sum()

    minutes_worked = hours_worked * 60

    return {
        "hours_worked": hours_worked,
        "minutes_worked": minutes_worked,
        "minutes_billed": minutes_billed,
        "productivity_minutes_percent": safe_percent(minutes_billed, minutes_worked),
        "units_billed": units_billed,
        "rounded_minutes_from_units": rounded_minutes_from_units,
        "productivity_units_percent": safe_percent(rounded_minutes_from_units, minutes_worked),
        "non_billable_total": non_billable_total,
        "non_billable_percent": safe_percent(non_billable_total, minutes_worked),
        "completed_services": completed_services,
        "non_billable_rows": working.loc[non_billable_mask].copy(),
        "all_services": working,
    }


def metric_card(label: str, value: str, note: str = "", variant: str = "blue", icon: str = ""):
    st.markdown(
        f"""
        <div class="metric-card metric-card-{variant}">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Header
# -----------------------------
logo = Image.open("auditor_logo.png")
buffered = BytesIO()
logo.save(buffered, format="PNG")
logo_base64 = base64.b64encode(buffered.getvalue()).decode()

st.markdown(
    f"""
    <div class="auditor-hero">
        <div class="auditor-badge">OPERATIONAL INTELLIGENCE DASHBOARD</div>
        <div class="auditor-title-row">
            <img src="data:image/png;base64,{logo_base64}" class="auditor-logo">
            <div class="auditor-title">THE AUDITOR</div>
        </div>
    <div class="auditor-subtitle">
        Productivity • Engagement • Billing Reconciliation • County Audit Review
    </div>

    <div class="auditor-tagline">
        The Proof is in the Pudding.
    </div>
        </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Input Section
# -----------------------------
with st.container():
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.subheader("The Ingredients")

    col1, col2, col3 = st.columns([1, 1.2, 1.2])

    with col1:
        hours_worked = st.number_input(
            "Hours Worked",
            min_value=0.0,
            value=0.0,
            step=0.25,
            help="Manually enter the employee's hours worked for the audit period.",
        )

    with col2:
        services_file = st.file_uploader(
            "Upload: Services (My Office)",
            type=["xlsx"],
            help="Required. This file drives the productivity engine.",
        )

    with col3:
        caseload_file = st.file_uploader(
            "Upload: Caseload",
            type=["xlsx"],
            help="Recommended for the full wrath of The Auditor.",
        )

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Caseload Personality Gate
# -----------------------------
run_productivity_only = False

if services_file is not None and caseload_file is None:
    st.markdown(
        """
        <div class="warning-box">
            <strong>Hold on there BroChatta,</strong> you sure you don't want to experience the entire wrath of <strong>The Auditor</strong>?
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    
    gate_col1, gate_col2, gate_spacer = st.columns([1.25, 1.25, 4.5])

    with gate_col1:
        if st.button("No, just productivity"):
            st.session_state["productivity_only"] = True
        
    with gate_col2:
        if st.button("Yes, unleash The Auditor"):
            st.info("Upload the Caseload file above and The Auditor will be ready to stretch its legs.")

    run_productivity_only = st.session_state.get("productivity_only", False)

    if run_productivity_only:
        st.markdown(
            """
            <div class="warning-box">
                Such a let down, seriously. haha<br>
                Productivity will run, but caseload audit functions will be skipped.
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------
# Validation and Calculation
# -----------------------------
can_run = services_file is not None and hours_worked > 0 and (caseload_file is not None or st.session_state.get("productivity_only", False))

if services_file is None:
    st.info("Upload Services (My Office) to begin.")

elif hours_worked <= 0:
    st.warning("Enter Hours Worked to run productivity calculations.")

elif caseload_file is None and not st.session_state.get("productivity_only", False):
    st.info("Choose whether to upload Caseload or run productivity only.")

elif can_run:
    try:
        detailed_service_file = None
        
        services_df = read_excel(services_file)

        employee_name = normalize_text(services_df.iloc[0, 3])

        services_dates = pd.to_datetime(
            services_df.iloc[:, 1],
            errors="coerce"
        )
        
        audit_start = services_dates.min().strftime("%m/%d/%Y")
        audit_end = services_dates.max().strftime("%m/%d/%Y")
        
        st.markdown(
            f"<div class='audit-banner'>"
            f"<div class='audit-banner-item'>Employee: {employee_name}</div>"
            f"<div class='audit-banner-item'>Audit Period: {audit_start} to {audit_end}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        columns_ok, missing_columns = find_required_columns(services_df)
        if not columns_ok:
            st.error(
                "The Services file is missing required column(s): "
                + ", ".join(missing_columns)
                + ". Expected columns include Procedure, Status, and ServiceUnits."
            )
            st.stop()

        results = calculate_productivity(services_df, hours_worked)

        
        # ============================================================
        # THE PUDDING LOGIC
        # ============================================================

        pudding_results = None
        attempts_only_clients = set()
        no_attempt_clients = set()

        if caseload_file is not None:
            caseload_df = read_excel(caseload_file)
    
            total_caseload = len(caseload_df)
    
            working = services_df.copy()
    
            working["_status_clean"] = working["Status"].apply(normalize_text)
            working["_procedure_clean"] = working["Procedure"].apply(normalize_text)
    
            completed_services_all = working.loc[
                working["_status_clean"].str.casefold() == "complete"
            ].copy()
    
            total_services_rendered = len(completed_services_all)
    
            successful_engagements_df = completed_services_all.loc[
                ~completed_services_all["_procedure_clean"].isin(NON_BILLABLE_PROCEDURES)
            ].copy()
    
            successful_engagements = len(successful_engagements_df)
    
            non_billable_services_df = completed_services_all.loc[
                completed_services_all["_procedure_clean"].isin(NON_BILLABLE_PROCEDURES)
            ].copy()
    
            non_billable_services = len(non_billable_services_df)
    
            successful_clients = set(
                successful_engagements_df["Client Name"].astype(str).str.strip()
            )
    
            non_billable_clients = set(
                non_billable_services_df["Client Name"].astype(str).str.strip()
            )
    
            attempts_only_clients = non_billable_clients - successful_clients
    
            attempts_only_no_engagement = len(attempts_only_clients)
    
            caseload_clients = set(
                caseload_df.iloc[:, 0].astype(str).str.strip()
            )
    
            service_clients = set(
                services_df.iloc[:, 0].astype(str).str.strip()
            )
    
            no_attempt_clients = caseload_clients - service_clients
    
            no_attempts_no_engagement = len(no_attempt_clients)
    
            no_show_cancel_mask = (
                working["_status_clean"].str.contains("no show", case=False, na=False)
                |
                working["_status_clean"].str.contains("cancel", case=False, na=False)
            )
    
            no_show_cancelled = int(no_show_cancel_mask.sum())

            pudding_results = {
                "total_caseload": total_caseload,
                "total_services_rendered": total_services_rendered,
                "successful_engagements": successful_engagements,
                "non_billable_services": non_billable_services,
                "attempts_only_no_engagement": attempts_only_no_engagement,
                "no_attempts_no_engagement": no_attempts_no_engagement,
                "no_show_cancelled": no_show_cancelled,
            }        

        st.markdown(
            """
            <div class="success-box">
                Productivity Engine ran successfully.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # KPI Cards
        st.subheader("The Proof")

        row1 = st.columns(3)
        with row1[0]:
            metric_card(
                "Hours Worked",
                format_number(results["hours_worked"]),
                "Manual user input",
                variant="green",
                icon="⏱️"
            )
        with row1[1]:
            metric_card(
                "Minutes Worked", 
                format_number(results["minutes_worked"]),
                "Hours Worked × 60",
                variant="green",
                icon="⏱️"
            )
        with row1[2]:
            metric_card(
                "Minutes Billed", 
                format_number(results["minutes_billed"]), 
                "Sum of ServiceUnits where Status = Complete",
                variant="purple",
                icon="⏱️"
            )

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

        row2 = st.columns(3)

        prod_minutes_variant, prod_minutes_icon = get_productivity_card_style(
            results["productivity_minutes_percent"]
        )

        with row2[0]:
            metric_card(
                "Productivity Minutes %",
                format_percent(results["productivity_minutes_percent"]),
                "Minutes Billed ÷ Minutes Worked",
                variant=prod_minutes_variant,
                icon=prod_minutes_icon
            )

        with row2[1]:
            metric_card(
                "Units Billed",
                format_number(results["units_billed"]),
                "Each completed row converted using 15-minute chart",
                variant="pink",
                icon="⏱️"
            )

        prod_units_variant, prod_units_icon = get_productivity_card_style(
            results["productivity_units_percent"]
        )

        with row2[2]:
            metric_card(
                "Productivity Units %",
                format_percent(results["productivity_units_percent"]),
                "Rounded unit minutes ÷ Minutes Worked",
                variant=prod_units_variant,
                icon=prod_units_icon
            )

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

        row3 = st.columns(3)
        with row3[0]:
            metric_card(
                "Non-Billable Total", 
                format_number(results["non_billable_total"]), 
                "Two verified non-billable procedures",
                variant="blue",
                icon="🧠"
            )
            
        with row3[1]:
            metric_card(
                "Non-Billable %", 
                format_percent(results["non_billable_percent"]), 
                "Non-Billable Total ÷ Minutes Worked",
                variant="blue",
                icon="🧠"
            )
        with row3[2]:
            metric_card(
                "Rounded Minutes", 
                format_number(results["rounded_minutes_from_units"]), 
                "Stored for Productivity Units %",
                variant="pink",
                icon="🧠"
            )

        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
   
        detailed_service_file = st.file_uploader(
            "To see Documentation Time and Travel Time totals, upload: Staff Service Detail Report - Optional",
            type=["xlsx"],
            help="Upload the Staff Service Detail Report to calculate Documentation and Travel totals.",
            key="staff_service_detail_report_upload",
        ) 
        
        documentation_total = 0.0
        documentation_percent = 0.0
        travel_total = 0.0
        travel_percent = 0.0

        if detailed_service_file is not None:
            sdr_df = read_excel(detailed_service_file)

            total_rows = sdr_df[
                sdr_df.iloc[:, 8].astype(str).str.strip().str.casefold() == "total:"
            ].copy()

            travel_total = total_rows.iloc[:, 9].apply(extract_number).sum()

            documentation_total = total_rows.iloc[:, 10].apply(extract_number).sum()

            documentation_percent = safe_percent(
                documentation_total,
                results["minutes_worked"]
            )

            travel_percent = safe_percent(
                travel_total,
                results["minutes_worked"]
            )

        row4 = st.columns(4)

        with row4[0]:
            metric_card(
                "Documentation Total",
                format_number(documentation_total),
                "From Staff Service Detail Report",
                variant="white",
                icon="📋"
            )

        with row4[1]:
            metric_card(
                "Documentation %",
                format_percent(documentation_percent),
                "Documentation Total ÷ Minutes Worked",
                variant="white",
                icon="📋"
            )

        with row4[2]:
            metric_card(
                "Travel Total",
                format_number(travel_total),
                "From Staff Service Detail Report",
                variant="white",
                icon="🚗"
            )

        with row4[3]:
            metric_card(
                "Travel %",
                format_percent(travel_percent),
                "Travel Total ÷ Minutes Worked",
                variant="white",
                icon="🚗"
            )

        # ============================================================
        # THE PUDDING
        # ============================================================
        
        st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)

        st.markdown("---")
        
        st.subheader("The Pudding")
        
        pudding_row1 = st.columns(4)
        
        with pudding_row1[0]:
            metric_card(
                "Total Caseload",
                format_number(pudding_results["total_caseload"]),
                "Total rows from Caseload file",
                variant="green",
                icon="✅"
            )
        
        with pudding_row1[1]:
            metric_card(
                "Total Services Rendered",
                format_number(pudding_results["total_services_rendered"]),
                "Completed services only",
            )
        
        with pudding_row1[2]:
            metric_card(
                "Successful Engagements",
                format_number(pudding_results["successful_engagements"]),
                "Completed billable services",
                variant="green",
                icon="✅"
            )
        
        with pudding_row1[3]:
            metric_card(
                "Non-Billable Services Rendered",
                format_number(pudding_results["non_billable_services"]),
                "Completed non-billable services",
                variant="orange",
                icon="✅"
            )
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        pudding_row2 = st.columns(3)
        
        with pudding_row2[0]:
            metric_card(
                "Attempts Only / No Engagement",
                format_number(pudding_results["attempts_only_no_engagement"]),
                "Non-billable only clients",
                variant="pink",
                icon="❌"
            )
        
        with pudding_row2[1]:
            metric_card(
                "No Attempts / No Engagement",
                format_number(pudding_results["no_attempts_no_engagement"]),
                "Caseload clients missing from Services",
                variant="red",
                icon="❌"
            )
        
        with pudding_row2[2]:
            metric_card(
                "No Shows / Cancelled Appointments",
                format_number(pudding_results["no_show_cancelled"]),
                "No Shows + Cancel statuses",
                variant="red",
                icon="❌"
            )

        st.markdown("<div style='margin-top: 22px;'></div>", unsafe_allow_html=True)
        
        st.markdown(
    "<h3 style='margin-bottom: -8px;'>The Pudding Lists Details</h3>",
    unsafe_allow_html=True,
)

        st.markdown(
            "<div class='small-muted' style='margin-top: -10px; margin-bottom: 18px;'>Use drop downs to view the lists of clients found for each report details.</div>",
            unsafe_allow_html=True,
        )
        
        proof_col1, proof_col2 = st.columns(2)

        with proof_col1:
            with st.expander("Productivity Procedures - Client List"):
                display_cols = [
                    "Client Name",
                    "DOS",
                    "Procedure",
                    "Status",
                    "ServiceUnits",
                    "_calculated_units",
                ]

                available_display_cols = [
                    c for c in display_cols
                    if c in results["completed_services"].columns
                ]

                st.dataframe(
                    results["completed_services"][available_display_cols],
                    use_container_width=True
                )

        with proof_col2:
            with st.expander("Non-Billable Total - Client List"):
                display_cols = [
                    "Client Name",
                    "DOS",
                    "Procedure",
                    "Status",
                    "ServiceUnits",
                ]

                available_display_cols = [
                    c for c in display_cols
                    if c in results["non_billable_rows"].columns
                ]

                st.dataframe(
                    results["non_billable_rows"][available_display_cols],
                    use_container_width=True
                )        

        attempts_only_df = pd.DataFrame(
            sorted(list(attempts_only_clients)),
            columns=["Client Name"]
        )

        no_attempts_df = pd.DataFrame(
            sorted(list(no_attempt_clients)),
            columns=["Client Name"]
        )

        list_col1, list_col2 = st.columns(2)

        with list_col1:
            with st.expander("Attempts Only / No Engagement - Client List"):
                st.dataframe(attempts_only_df, use_container_width=True)

        with list_col2:
            with st.expander("No Attempts / No Engagement - Client List"):
                st.dataframe(no_attempts_df, use_container_width=True)

                st.download_button(
                    "Download No Attempts / No Engagement CSV",
                    data=no_attempts_df.to_csv(index=False).encode("utf-8"),
                    file_name="no_attempts_no_engagement.csv",
                    mime="text/csv",
                )
        
     
        st.markdown("---")

        st.markdown(
            "<h3 style='color: #ff5c6c; font-weight: 900; margin-bottom: -18px;'>The County Auditor</h3>",
            unsafe_allow_html=True,
        )
      
        county_services_file = st.file_uploader(
            "Upload an Excel version of COUNTY SERVICES INVOICED to compare The Auditor against the man and locate those mistakes.",
            type=["xlsx"],
            help="Upload the County Services Invoiced file to compare county billing against The Auditor.",
            key="county_services_invoiced_upload",
        )

        if county_services_file is not None:
            st.success("County Services Invoiced uploaded successfully.")

            county_clean_df = read_county_services_invoiced(county_services_file)
            auditor_compare_df = results["completed_services"].copy()

            auditor_compare_df["Auditor Client ID"] = auditor_compare_df["Client Name"].apply(extract_client_id)
            auditor_compare_df["Auditor DOS"] = pd.to_datetime(
                auditor_compare_df["DOS"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d %H:%M")
            auditor_compare_df["Auditor Procedure"] = auditor_compare_df["Procedure"].apply(normalize_procedure)
            auditor_compare_df["Auditor Rounded Minutes"] = auditor_compare_df["_calculated_units"] * 15

            auditor_compare_df["Match Key"] = (
                auditor_compare_df["Auditor Client ID"].astype(str)
                + "|"
                + auditor_compare_df["Auditor DOS"].astype(str)
                + "|"
                + auditor_compare_df["Auditor Procedure"].astype(str)
            )

            county_clean_df["Match Key"] = (
                county_clean_df["County Client ID"].astype(str)
                + "|"
                + county_clean_df["County DOS"].astype(str)
                + "|"
                + county_clean_df["County Procedure"].astype(str)
             )

            county_keys = set(county_clean_df["Match Key"])

            county_missing_df = auditor_compare_df[
                ~auditor_compare_df["Match Key"].isin(county_keys)
            ].copy() 

            auditor_keys = set(auditor_compare_df["Match Key"])

            county_extra_df = county_clean_df[
                ~county_clean_df["Match Key"].isin(auditor_keys)
            ].copy()

            auditor_total_rounded_minutes = (
                auditor_compare_df["_calculated_units"].sum() * 15
            )
                
            county_total_rounded_minutes = (
                county_clean_df["County Rounded Minutes"].sum()
            )
                
            rounded_minute_variance = (
                county_total_rounded_minutes
                - auditor_total_rounded_minutes
            )

            county_services_variant, county_services_icon = get_match_card_style(
                len(county_clean_df) == pudding_results["successful_engagements"]
            )
            
            county_minutes_variant, county_minutes_icon = get_match_card_style(
                values_match(
                    county_clean_df["County Rounded Minutes"].sum(),
                    results["rounded_minutes_from_units"]
                )
            )
            
            incorrect_rounded_count = (county_clean_df["Rounded Minute Difference"] != 0).sum()
            incorrect_rounded_variant, incorrect_rounded_icon = get_match_card_style(
                incorrect_rounded_count == 0
            )
            
            unit_variance_total = county_clean_df["Unit Difference"].sum()
            unit_variance_variant, unit_variance_icon = get_match_card_style(
                values_match(unit_variance_total, 0)
            )
            
            missing_services_variant, missing_services_icon = get_match_card_style(
                len(county_missing_df) == 0
            )
            
            extra_services_variant, extra_services_icon = get_match_card_style(
                len(county_extra_df) == 0
            )
            
            county_productivity = safe_percent(
                county_clean_df["County Rounded Minutes"].sum(),
                results["minutes_worked"]
            )
            
            county_productivity_variant, county_productivity_icon = get_match_card_style(
                values_match(
                    county_productivity,
                    results["productivity_units_percent"]
                )
            )

            rounded_variance_variant, rounded_variance_icon = get_match_card_style(
                values_match(rounded_minute_variance, 0)
            )
            
            st.subheader("County File Audited")

            county_math_row = st.columns(4)

            with county_math_row[0]:
                metric_card(
                    "County Services Found",
                    format_number(len(county_clean_df)),
                    "Should match Successful Engagements from The Pudding section",
                    variant=county_services_variant,
                    icon=county_services_icon
                )

            with county_math_row[1]:
                metric_card(
                    "County Rounded Minutes",
                    format_number(county_clean_df["County Rounded Minutes"].sum()),
                    "Should match Rounded Minutes from The Proof section",
                    variant=county_minutes_variant,
                    icon=county_minutes_icon
                )

            with county_math_row[2]:
                metric_card(
                    "Incorrect Rounded Minutes",
                    format_number(incorrect_rounded_count),
                    "Procedures identified as incorrect math/rounding by the County",
                    variant=incorrect_rounded_variant,
                    icon=incorrect_rounded_icon
                )

            with county_math_row[3]:
                metric_card(
                    "County Billed Unit Variance",
                    format_number(unit_variance_total),
                    "Total unit variance found",
                    variant=unit_variance_variant,
                    icon=unit_variance_icon
                )

            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

            county_recon_row = st.columns(3)
            
            with county_recon_row[0]:
                metric_card(
                    "County Missing Services",
                    format_number(len(county_missing_df)),
                    "Total services not counted/billed for by the County",
                    variant=missing_services_variant,
                    icon=missing_services_icon
                )
            
            with county_recon_row[1]:
                metric_card(
                    "County Extra Services",
                    format_number(len(county_extra_df)),
                    "Extra services found in the County file",
                    variant=extra_services_variant,
                    icon=extra_services_icon
                )

            with county_recon_row[2]:
                metric_card(
                    "County Productivity %",
                    format_percent(county_productivity),
                    "County rounded minutes ÷ Minutes Worked",
                    variant=county_productivity_variant,
                    icon=county_productivity_icon
                )

            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

            county_variance_row = st.columns(1)

            with county_variance_row[0]:
                metric_card(
                    "Rounded Minute Variance",
                    format_number(rounded_minute_variance),
                    "Total missing minutes identified by The Auditor and the County",
                    variant=rounded_variance_variant,
                    icon=rounded_variance_icon
                )

            st.markdown("<div style='margin-top: 48px;'></div>", unsafe_allow_html=True)
            
            st.markdown(
                "<h3 style='text-align: center;'>Procedure Comparison: Services vs County Invoiced</h3>",
                unsafe_allow_html=True,
            )

            auditor_proc_summary = (
                auditor_compare_df
                .groupby("Auditor Procedure")
                .size()
                .reset_index(name="Auditor Count")
                .rename(columns={"Auditor Procedure": "Procedure"})
            )

            county_proc_summary = (
                county_clean_df
                .groupby("County Procedure")
                .size()
                .reset_index(name="County Count")
                .rename(columns={"County Procedure": "Procedure"})
            )

            procedure_breakdown = pd.merge(
                auditor_proc_summary,
                county_proc_summary,
                on="Procedure",
                how="outer"
            ).fillna(0)

            procedure_breakdown["Auditor Count"] = procedure_breakdown["Auditor Count"].astype(int)
            procedure_breakdown["County Count"] = procedure_breakdown["County Count"].astype(int)
            procedure_breakdown["Difference"] = (
                procedure_breakdown["County Count"] - procedure_breakdown["Auditor Count"]
            )

            styled_procedure_breakdown = (
                procedure_breakdown
                .style
                .format({
                    "Auditor Count": "{:,.0f}",
                    "County Count": "{:,.0f}",
                    "Difference": "{:+,.0f}",
                })
                .map(
                    lambda value: (
                        "background-color: rgba(85, 220, 150, 0.22); color: #eafff3; font-weight: 800;"
                        if value == 0
                        else "background-color: rgba(255, 90, 110, 0.22); color: #ffe8ec; font-weight: 900;"
                    ),
                    subset=["Difference"]
                )
            )
                       
            st.markdown(
                procedure_breakdown.to_html(index=False, classes="audit-table"),
                unsafe_allow_html=True,
            )

            county_audit_report = pd.concat(
                [
                    pd.DataFrame([
                        {"Finding Type": "Summary", "Detail": "County Missing Services", "Value": len(county_missing_df)},
                        {"Finding Type": "Summary", "Detail": "County Extra Services", "Value": len(county_extra_df)},
                        {"Finding Type": "Summary", "Detail": "Incorrect Rounded Minutes", "Value": (county_clean_df["Rounded Minute Difference"] != 0).sum()},
                        {"Finding Type": "Summary", "Detail": "County Billed Unit Variance", "Value": county_clean_df["Unit Difference"].sum()},
                        {"Finding Type": "Summary", "Detail": "Rounded Minute Variance", "Value": rounded_minute_variance},
                    ]),
                    county_missing_df.assign(**{"Finding Type": "County Missing Services"}),
                    county_extra_df.assign(**{"Finding Type": "County Extra Services"}),
                    county_clean_df[county_clean_df["Rounded Minute Difference"] != 0].assign(**{"Finding Type": "Incorrect Rounded Minutes"}),
                    county_clean_df[county_clean_df["Unit Difference"] != 0].assign(**{"Finding Type": "County Billed Unit Variance"}),
                ],
                ignore_index=True,
                sort=False,
            )
          
            with st.expander("County Missing Services - Detail"):
                st.dataframe(
                    county_missing_df,
                    use_container_width=True
                )
            
            with st.expander("County Extra Services - Detail"):
                st.dataframe(
                    county_extra_df,
                    use_container_width=True
                )           

            with st.expander("County Rounding / Unit Issues"):
                issue_df = county_clean_df[
                    (county_clean_df["Rounded Minute Difference"] != 0)
                    | (county_clean_df["Unit Difference"] != 0)
                ].copy()

                st.dataframe(issue_df, use_container_width=True)

                st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

                st.download_button(
                    "Download County Audit Findings CSV",
                    data=county_audit_report.to_csv(index=False).encode("utf-8"),
                    file_name="county_audit_findings.csv",
                    mime="text/csv",
                )
    
    except Exception as exc:
        st.error("The Auditor hit an issue while reading the file.")
        st.exception(exc)


# -----------------------------
# Verified Logic Reference
# -----------------------------
with st.expander("Verified Phase 1 Logic"):
    st.markdown(
        """
        **Hours Worked** = manual user input  
        **Minutes Worked** = Hours Worked × 60  

        **Minutes Billed** = Sum of `ServiceUnits` where `Status = Complete`  

        **Productivity Minutes %** = Minutes Billed ÷ Minutes Worked × 100  

        **Units Billed** = Each completed row converted individually using the 15-minute Medicare-style unit chart, then summed  

        **Productivity Units %** = Rounded Minutes from Units Billed ÷ Minutes Worked × 100  

        **Non-Billable Total** = Sum of `ServiceUnits` where `Procedure` is:
        - Client Non Billable Srvc Must Document
        - Non-billable Attempted Contact

        **Non-Billable %** = Non-Billable Total ÷ Minutes Worked × 100
        """
    )
