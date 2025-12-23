# app.py
# Streamlit Master Dashboard – STRICT status logic (Government MIS safe)
# FIXED: Manual "COMPLETED" typing + Google CSV delay + caching issues

import streamlit as st
import pandas as pd
import re
import unicodedata

# --------------------------------------------------
# FORCE NO CACHING (VERY IMPORTANT)
# --------------------------------------------------
st.markdown(
    "<meta http-equiv='Cache-Control' content='no-cache, no-store, must-revalidate'>",
    unsafe_allow_html=True
)

st.set_page_config(page_title="Officer Task Status Dashboard", layout="wide")

st.title("📊 Master Dashboard – Officer Weekly Task Status")
st.caption("Latest-week only • Strict Pending/Completed logic • Auto-updates weekly")

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
OFFICER_SHEETS = {
    "ADC G": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "174981592"),
    "ADC D": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "537074213"),
    "ADC (UD)": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "846764018"),
    "ADC K": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "1476602908"),
    "ADC J": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "18822170"),
    "ACG": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "1291568180"),
    "CMFO": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "1227420096"),
    "SDM East": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "33416154"),
    "SDM West": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "52989510"),
    "SDM Raikot": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "1833732603"),
    "SDM Samrala": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "190794459"),
    "SDM Khanna": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "2054147547"),
    "SDM Jagraon": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "278920499"),
    "SDM Payal": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "778489712"),
    "DRO": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "501565659"),
    "RTA": ("1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok", "1563439729"),
}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def load_sheet_csv(spreadsheet_id: str, gid: str) -> pd.DataFrame:
    """Load Google Sheet tab as CSV (public access)."""
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(url, header=None)


def find_latest_status_column(df: pd.DataFrame) -> int:
    """Find rightmost Status column (latest week)."""
    status_cols = []
    for col in range(df.shape[1]):
        header_scan = df.iloc[:15, col].astype(str).str.lower()
        if header_scan.str.contains("status").any():
            status_cols.append(col)

    if not status_cols:
        raise ValueError("No Status column found")

    return max(status_cols)


def clean_status(cell_value: str) -> str:
    """
    ULTRA-STRICT normalization:
    - Removes ALL unicode spaces & invisible chars
    - Case insensitive
    """
    if pd.isna(cell_value):
        return ""

    s = unicodedata.normalize("NFKD", str(cell_value))
    s = "".join(ch for ch in s if ch.isalnum())
    return s.lower()


def summarize_status(df: pd.DataFrame, status_col: int):
    """
    STRICT LOGIC:
    - Exact 'completed' → Complete
    - Anything else → Incomplete
    """

    # Identify task rows via Sr. No. in first 5 columns
    sr_no_mask = (
        df.iloc[:, :5]
        .apply(lambda col: pd.to_numeric(col, errors="coerce").notna())
        .any(axis=1)
    )

    task_rows = df[sr_no_mask]

    status_series = task_rows.iloc[:, status_col].apply(clean_status)

    completed_count = (status_series == "completed").sum()
    incomplete_count = (status_series != "completed").sum()

    if incomplete_count > 0:
        overall_status = "Incomplete"
    elif completed_count > 0:
        overall_status = "Complete"
    else:
        overall_status = "No Update"

    return overall_status, int(incomplete_count), int(completed_count)

# --------------------------------------------------
# AGGREGATION
# --------------------------------------------------
rows = []

with st.spinner("Fetching latest data from Google Sheets..."):
    for officer, (sid, gid) in OFFICER_SHEETS.items():
        try:
            df = load_sheet_csv(sid, gid)
            status_col = find_latest_status_column(df)
            overall, incomplete, complete = summarize_status(df, status_col)

            rows.append({
                "Officer Name": officer,
                "Overall Status": overall,
                "No. of Tasks Incomplete": incomplete,
                "No. of Tasks Completed": complete,
            })
        except Exception:
            rows.append({
                "Officer Name": officer,
                "Overall Status": "Error",
                "No. of Tasks Incomplete": None,
                "No. of Tasks Completed": None,
            })

summary_df = pd.DataFrame(rows)

# --------------------------------------------------
# DASHBOARD UI
# --------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Officer-wise Status (Latest Week Only)")
    st.dataframe(summary_df, use_container_width=True)

with col2:
    st.subheader("📈 Incomplete Tasks by Officer")
    chart_df = summary_df.dropna(subset=["No. of Tasks Incomplete"])
    st.bar_chart(chart_df.set_index("Officer Name")["No. of Tasks Incomplete"])

# Manual refresh button
if st.button("🔄 Refresh Latest Data"):
    st.rerun()

st.markdown("---")
st.info(
    "Rule applied: ONLY exact 'completed' (case-insensitive, spaces removed) is treated as completed. "
    "Anything else → Incomplete. "
    "Latest week is auto-detected using the rightmost Status column."
)
