# app.py
# Streamlit Master Dashboard + Star-Mark Summary Table

import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Officer Task Status Dashboard", layout="wide")

st.title("📊 Master Dashboard – Officer Task Status")
st.caption("Weekly status from officer sheets + Star-mark task summary")

# --------------------------------------------------
# CONFIGURATION – OFFICER WEEKLY SHEETS
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
# STAR MARK SHEET CONFIG
# --------------------------------------------------
STAR_MARK_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/"
    "export?format=csv&gid=213021534"
)

# --------------------------------------------------
# HELPERS – WEEKLY STATUS
# --------------------------------------------------
def load_sheet_csv(spreadsheet_id: str, gid: str) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(url, header=None)

def find_latest_status_column(df: pd.DataFrame) -> int:
    status_cols = []
    for col in range(df.shape[1]):
        col_values = df.iloc[:10, col].astype(str).str.lower()
        if col_values.str.contains("status").any():
            status_cols.append(col)
    return max(status_cols)

def summarize_status(df: pd.DataFrame, status_col: int):
    status_series = df.iloc[10:, status_col].astype(str).str.lower()
    incomplete = status_series.str.contains("pending|incomplete").sum()
    complete = status_series.str.contains("complete|completed").sum()
    overall = "Incomplete" if incomplete > 0 else "Complete"
    return overall, incomplete, complete

# --------------------------------------------------
# LOAD WEEKLY OFFICER DATA
# --------------------------------------------------
rows = []

with st.spinner("Fetching latest weekly officer data..."):
    for officer, (sid, gid) in OFFICER_SHEETS.items():
        try:
            df = load_sheet_csv(sid, gid)
            col = find_latest_status_column(df)
            overall, inc, comp = summarize_status(df, col)
            rows.append({
                "Officer Name": officer,
                "Overall Status": overall,
                "No. of Tasks Incomplete": inc,
                "No. of Tasks Completed": comp
            })
        except:
            rows.append({
                "Officer Name": officer,
                "Overall Status": "Error",
                "No. of Tasks Incomplete": None,
                "No. of Tasks Completed": None
            })

weekly_df = pd.DataFrame(rows)

# --------------------------------------------------
# LOAD STAR MARK DATA
# --------------------------------------------------
star_df = pd.read_csv(STAR_MARK_SHEET_URL)

star_df.columns = star_df.columns.str.strip()
star_df["Date"] = pd.to_datetime(star_df["Date"], dayfirst=True, errors="coerce")
star_df["Status"] = star_df["Status"].astype(str).str.lower()

last_7_days = datetime.now() - timedelta(days=7)

completed_7 = star_df[
    (star_df["Status"] == "completed") &
    (star_df["Date"] >= last_7_days)
]

completed_summary = completed_7.groupby("Marked to Officer").size().reset_index(
    name="Completed (Last 7 Days)"
)

pending_summary = star_df[
    star_df["Status"] != "completed"
].groupby("Marked to Officer").size().reset_index(
    name="Pending Tasks"
)

star_summary = pd.merge(
    completed_summary,
    pending_summary,
    on="Marked to Officer",
    how="outer"
).fillna(0)

# --------------------------------------------------
# DASHBOARD UI (SIDE-BY-SIDE TABLES)
# --------------------------------------------------
col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("📋 Officer-wise Weekly Status (Latest Week)")
    st.dataframe(weekly_df, use_container_width=True)

with col2:
    st.subheader("⭐ Star-Mark Officer Summary")
    st.dataframe(star_summary, use_container_width=True)

st.markdown("---")
st.info(
    "Left table shows **latest weekly status** from individual officer sheets. "
    "Right table shows **Star-mark task performance** (completed in last 7 days & pending)."
)
