
import re
import math
from io import BytesIO

import pandas as pd
import streamlit as st


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
    .stApp {
        background: linear-gradient(135deg, #07111f 0%, #10233d 45%, #183a5a 100%);
        color: #f5f7fb;
    }

    h1, h2, h3, h4 {
        color: #f8fbff;
    }

    .auditor-title {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: 1px;
        margin-bottom: 0.1rem;
    }

    .auditor-subtitle {
        font-size: 1.05rem;
        color: #c9d8ea;
        margin-bottom: 1.5rem;
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
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 18px;
        padding: 1.15rem;
        min-height: 122px;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.24);
    }

    .metric-label {
        font-size: 0.92rem;
        color: #c7d6e8;
        margin-bottom: 0.45rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 850;
        color: #ffffff;
        line-height: 1.1;
    }

    .metric-note {
        font-size: 0.78rem;
        color: #aebed3;
        margin-top: 0.35rem;
    }

    .success-box {
        background: rgba(70, 180, 120, 0.16);
        border: 1px solid rgba(70, 180, 120, 0.40);
        border-radius: 14px;
        padding: 0.85rem;
        color: #e9fff2;
    }

    .warning-box {
        background: rgba(245, 171, 53, 0.16);
        border: 1px solid rgba(245, 171, 53, 0.45);
        border-radius: 14px;
        padding: 0.85rem;
        color: #fff5df;
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


def read_excel(uploaded_file) -> pd.DataFrame:
    """Read the first sheet from an uploaded Excel file."""
    return pd.read_excel(uploaded_file)


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


def metric_card(label: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Header
# -----------------------------
st.markdown(f"<div class='auditor-title'>🕵️ {APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='auditor-subtitle'>{APP_SUBTITLE}</div>", unsafe_allow_html=True)


# -----------------------------
# Input Section
# -----------------------------
with st.container():
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.subheader("Setup")

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

    gate_col1, gate_col2 = st.columns(2)

    with gate_col1:
        if st.button("Yes, unleash The Auditor"):
            st.info("Upload the Caseload file above and The Auditor will be ready to stretch its legs.")

    with gate_col2:
        if st.button("No, just productivity"):
            st.session_state["productivity_only"] = True

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
# Future Options
# -----------------------------
with st.expander("Future Audit Options"):
    county_audit = st.checkbox("Would you like to audit the county?")
    if county_audit:
        county_file = st.file_uploader(
            "Upload: County Productivity",
            type=["xlsx"],
            help="Coming soon. County audit logic is not operational in Phase 1.",
        )
        st.warning("County Audit is under development and will not run in this version.")

    doc_travel = st.checkbox("Would you like to calculate Documentation & Travel totals?")
    if doc_travel:
        sdr_file = st.file_uploader(
            "Upload: SDR",
            type=["xlsx"],
            help="Coming soon. Documentation and Travel logic is not operational in Phase 1.",
        )
        st.warning("Documentation and Travel totals are under development and will not run in this version.")


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
        st.subheader("Productivity Cards")

        row1 = st.columns(3)
        with row1[0]:
            metric_card("Hours Worked", format_number(results["hours_worked"]), "Manual user input")
        with row1[1]:
            metric_card("Minutes Worked", format_number(results["minutes_worked"]), "Hours Worked × 60")
        with row1[2]:
            metric_card("Minutes Billed", format_number(results["minutes_billed"]), "Sum of ServiceUnits where Status = Complete")

        row2 = st.columns(3)
        with row2[0]:
            metric_card("Productivity Minutes %", format_percent(results["productivity_minutes_percent"]), "Minutes Billed ÷ Minutes Worked")
        with row2[1]:
            metric_card("Units Billed", format_number(results["units_billed"]), "Each completed row converted using 15-minute chart")
        with row2[2]:
            metric_card("Productivity Units %", format_percent(results["productivity_units_percent"]), "Rounded unit minutes ÷ Minutes Worked")

        row3 = st.columns(3)
        with row3[0]:
            metric_card("Non-Billable Total", format_number(results["non_billable_total"]), "Two verified non-billable procedures")
        with row3[1]:
            metric_card("Non-Billable %", format_percent(results["non_billable_percent"]), "Non-Billable Total ÷ Minutes Worked")
        with row3[2]:
            metric_card("Rounded Minutes from Units", format_number(results["rounded_minutes_from_units"]), "Stored for Productivity Units %")

        st.info("**To see Documentation time and Travel Times, please upload Staff Service Detail Report.**")
        
        detailed_service_file = st.file_uploader(
            "Upload: Staff Service Detail Report",
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
                "From Staff Service Detail Report"
            )

        with row4[1]:
            metric_card(
                "Documentation %",
                format_percent(documentation_percent),
                "Documentation Total ÷ Minutes Worked"
            )

        with row4[2]:
            metric_card(
                "Travel Total",
                format_number(travel_total),
                "From Staff Service Detail Report"
            )

        with row4[3]:
            metric_card(
                "Travel %",
                format_percent(travel_percent),
                "Travel Total ÷ Minutes Worked"
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
            )
        
        with pudding_row1[3]:
            metric_card(
                "Non-Billable Services Rendered",
                format_number(pudding_results["non_billable_services"]),
                "Completed non-billable services",
            )
        
        pudding_row2 = st.columns(3)
        
        with pudding_row2[0]:
            metric_card(
                "Attempts Only / No Engagement",
                format_number(pudding_results["attempts_only_no_engagement"]),
                "Non-billable only clients",
            )
        
        with pudding_row2[1]:
            metric_card(
                "No Attempts / No Engagement",
                format_number(pudding_results["no_attempts_no_engagement"]),
                "Caseload clients missing from Services",
            )
        
        with pudding_row2[2]:
            metric_card(
                "No Shows / Cancelled Appointments",
                format_number(pudding_results["no_show_cancelled"]),
                "No Shows + Cancel statuses",
            )

        st.subheader("The Pudding Lists")

        attempts_only_df = pd.DataFrame(
            sorted(list(attempts_only_clients)),
            columns=["Client Name"]
        )

        no_attempts_df = pd.DataFrame(
            sorted(list(no_attempt_clients)),
            columns=["Client Name"]
        )

        with st.expander("Attempts Only / No Engagement - Client List"):
            st.dataframe(attempts_only_df, use_container_width=True)

            st.download_button(
                "Download Attempts Only / No Engagement CSV",
                data=attempts_only_df.to_csv(index=False).encode("utf-8"),
                file_name="attempts_only_no_engagement.csv",
                mime="text/csv",
            )

        with st.expander("No Attempts / No Engagement - Client List"):
            st.dataframe(no_attempts_df, use_container_width=True)

            st.download_button(
                "Download No Attempts / No Engagement CSV",
                data=no_attempts_df.to_csv(index=False).encode("utf-8"),
                file_name="no_attempts_no_engagement.csv",
                mime="text/csv",
            )

         

        # Audit Detail
        st.subheader("Audit Detail")
    
        with st.expander("Completed rows used for Minutes Billed and Units Billed"):
            display_cols = ["Client Name", "DOS", "Procedure", "Status", "ServiceUnits", "_calculated_units"]
            available_display_cols = [c for c in display_cols if c in results["completed_services"].columns]
            st.dataframe(results["completed_services"][available_display_cols], use_container_width=True)
    
        with st.expander("Rows used for Non-Billable Total"):
            display_cols = ["Client Name", "DOS", "Procedure", "Status", "ServiceUnits"]
            available_display_cols = [c for c in display_cols if c in results["non_billable_rows"].columns]
            st.dataframe(results["non_billable_rows"][available_display_cols], use_container_width=True)
    
        # Downloadable summary
        summary_df = pd.DataFrame(
                [
                    {"Metric": "Hours Worked", "Value": results["hours_worked"]},
                    {"Metric": "Minutes Worked", "Value": results["minutes_worked"]},
                    {"Metric": "Minutes Billed", "Value": results["minutes_billed"]},
                    {"Metric": "Productivity Minutes %", "Value": results["productivity_minutes_percent"]},
                    {"Metric": "Units Billed", "Value": results["units_billed"]},
                    {"Metric": "Rounded Minutes from Units", "Value": results["rounded_minutes_from_units"]},
                    {"Metric": "Productivity Units %", "Value": results["productivity_units_percent"]},
                    {"Metric": "Non-Billable Total", "Value": results["non_billable_total"]},
                    {"Metric": "Non-Billable %", "Value": results["non_billable_percent"]},
                    {"Metric": "Documentation Total", "Value": "N/A"},
                    {"Metric": "Documentation %", "Value": "N/A"},
                    {"Metric": "Travel Total", "Value": "N/A"},
                    {"Metric": "Travel %", "Value": "N/A"},
                ]
            )
    
        st.download_button(
            "Download Productivity Summary CSV",
            data=summary_df.to_csv(index=False).encode("utf-8"),
            file_name="the_auditor_productivity_summary.csv",
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
