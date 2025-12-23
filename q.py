# app.py
# Streamlit Master Dashboard to aggregate weekly task status from multiple Google Sheets

import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="Officer Task Status Dashboard", layout="wide")

st.title("📊 Master Dashboard – Officer Weekly Task Status")
st.caption("Automatically reads the latest week column from each Google Sheet and summarizes task completion.")

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
# Map officer name to (spreadsheet_id, gid)
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
    """Load a Google Sheet tab as CSV using public access."""
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(url, header=None)


def find_latest_status_column(df: pd.DataFrame) -> int:
    """
    Find the column index of the latest 'Status' by scanning header rows.
    Assumes new weeks are appended to the right.
    """
    status_cols = []
    for col in range(df.shape[1]):
        col_values = df.iloc[:10, col].astype(str).str.lower()
        if col_values.str.contains("status").any():
            status_cols.append(col)
    if not status_cols:
        raise ValueError("No Status column found")
    return max(status_cols)


def summarize_status(df: pd.DataFrame, status_col: int):
    """Count completed vs incomplete tasks from a Status column."""
    status_series = df.iloc[10:, status_col].astype(str).str.lower()

    incomplete_mask = status_series.str.contains("pending|incomplete", regex=True)
    complete_mask = status_series.str.contains("complete|completed", regex=True)

    incomplete_count = incomplete_mask.sum()
    complete_count = complete_mask.sum()

    overall_status = "Incomplete" if incomplete_count > 0 else "Complete"

    return overall_status, incomplete_count, complete_count


# --------------------------------------------------
# MAIN AGGREGATION
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
                "No. of Tasks Incomplete": int(incomplete),
                "No. of Tasks Completed": int(complete),
            })
        except Exception as e:
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
    st.subheader("📋 Officer-wise Weekly Status (Latest Week)")
    st.dataframe(summary_df, use_container_width=True)

with col2:
    st.subheader("📈 Incomplete Tasks by Officer")
    chart_df = summary_df.dropna(subset=["No. of Tasks Incomplete"])
    st.bar_chart(chart_df.set_index("Officer Name")["No. of Tasks Incomplete"])

st.markdown("---")
st.info(
    "Logic used: For each officer sheet, the **rightmost Status column** is treated as the latest week. "
    "If **any task is Pending/Incomplete**, the officer's overall status is marked **Incomplete**."
)

