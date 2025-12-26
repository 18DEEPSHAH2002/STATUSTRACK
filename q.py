# app.py
# Streamlit Master Dashboard + Star-Mark Summary (FIXED)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Officer Task Status Dashboard", layout="wide")

st.title("📊 Master Dashboard – Officer Task Status")
st.caption("Weekly officer status + Star-mark task summary")

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
# STAR MARK SHEET (PUBLIC CSV)
# --------------------------------------------------
STAR_MARK_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "14-idXJHzHKCUQxxaqGZi-6S0G20gvPUhK4G16ci2FwI/"
    "export?format=csv&gid=213021534"
)

# --------------------------------------------------
# UPCOMING COURT CASES SHEET (PUBLIC CSV)
# --------------------------------------------------
COURT_CASE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1VUnD7ySFzIkeZlaq8E5XG8r2xXcos6lhIt62QZEeHKs/"
    "export?format=csv&gid=0"
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
    if not status_cols:
        raise ValueError("No Status column found")
    return max(status_cols)

def summarize_status(df: pd.DataFrame, status_col: int):
    status_series = df.iloc[10:, status_col].astype(str).str.lower()
    incomplete = status_series.str.contains("pending|incomplete").sum()
    complete = status_series.str.contains("complete|completed").sum()
    overall = "Incomplete" if incomplete > 0 else "Complete"
    return overall, incomplete, complete

# --------------------------------------------------
# HELPER – AUTO FIND DATE COLUMN (STAR MARK FIX)
# --------------------------------------------------
def find_date_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if "date" in col.lower():
            return col
    raise ValueError("No Date column found in Star Mark sheet")

# --------------------------------------------------
# LOAD WEEKLY OFFICER DATA
# --------------------------------------------------
weekly_rows = []

with st.spinner("Fetching latest weekly officer data..."):
    for officer, (sid, gid) in OFFICER_SHEETS.items():
        try:
            df = load_sheet_csv(sid, gid)
            status_col = find_latest_status_column(df)
            overall, inc, comp = summarize_status(df, status_col)

            weekly_rows.append({
                "Officer Name": officer,
                "Overall Status": overall,
                "No. of Tasks Incomplete": inc,
                "No. of Tasks Completed": comp,
            })
        except Exception:
            weekly_rows.append({
                "Officer Name": officer,
                "Overall Status": "Error",
                "No. of Tasks Incomplete": None,
                "No. of Tasks Completed": None,
            })

weekly_df = pd.DataFrame(weekly_rows)

# --------------------------------------------------
# LOAD STAR MARK DATA (FIXED & SAFE)
# --------------------------------------------------
star_df = pd.read_csv(STAR_MARK_SHEET_URL)
star_df.columns = star_df.columns.str.strip()

date_col = find_date_column(star_df)

star_df[date_col] = pd.to_datetime(
    star_df[date_col],
    dayfirst=True,
    errors="coerce"
)

star_df["Status"] = star_df["Status"].astype(str).str.lower()
star_df["Marked to Officer"] = star_df["Marked to Officer"].astype(str).str.strip()

last_7_days = datetime.now() - timedelta(days=7)

completed_7 = star_df[
    (star_df["Status"] == "completed") &
    (star_df[date_col] >= last_7_days)
]

completed_summary = (
    completed_7
    .groupby("Marked to Officer")
    .size()
    .reset_index(name="Completed (Last 7 Days)")
)

pending_summary = (
    star_df[star_df["Status"] != "completed"]
    .groupby("Marked to Officer")
    .size()
    .reset_index(name="Pending Tasks")
)

star_summary = pd.merge(
    completed_summary,
    pending_summary,
    on="Marked to Officer",
    how="outer"
).fillna(0)

# --------------------------------------------------
# LOAD UPCOMING COURT CASES DATA (NO LOGIC CHANGE)
# --------------------------------------------------
court_df = pd.read_csv(COURT_CASE_SHEET_URL)
court_df.columns = court_df.columns.str.strip()

court_df = court_df[[
    "Name of the Officer",
    "Upcoming Hearing Date",
    "Name of the Court",
]]

court_df["Upcoming Hearing Date"] = pd.to_datetime(
    court_df["Upcoming Hearing Date"],
    dayfirst=True,
    errors="coerce"
)

court_df = court_df.sort_values("Upcoming Hearing Date")

# --------------------------------------------------
# DASHBOARD UI
# --------------------------------------------------
col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("📋 Officer-wise Weekly Status (Latest Week)")
    st.dataframe(weekly_df, use_container_width=True)

with col2:
    st.subheader("⭐ Star-Mark Officer Summary")
    st.dataframe(star_summary, use_container_width=True)

st.markdown("---")

st.subheader("⚖️ Upcoming Court Cases")
st.dataframe(court_df, use_container_width=True)

st.info(
    "Top tables show **weekly status** and **Star-mark summary**. "
    "The bottom table lists **upcoming court cases** with officer, hearing date, and court name."
)
