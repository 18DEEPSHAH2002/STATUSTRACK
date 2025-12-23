# app.py
# Officer Task Status Dashboard – FINAL STABLE VERSION
# Status header is in ROW 2, tasks detected via Task column

import streamlit as st
import pandas as pd
import unicodedata

# --------------------------------------------------
# FORCE NO CACHING
# --------------------------------------------------
st.markdown(
    "<meta http-equiv='Cache-Control' content='no-cache, no-store, must-revalidate'>",
    unsafe_allow_html=True
)

st.set_page_config(page_title="Officer Task Status Dashboard", layout="wide")

st.title("📊 Master Dashboard – Officer Weekly Task Status")
st.caption("Latest week only • Pending / Completed counted • Blank ignored")

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
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(url, header=None)


def find_latest_status_column(df: pd.DataFrame) -> int:
    """
    Status header is in ROW 2 (index 1).
    Latest week = rightmost column where row 2 == 'Status'
    """
    header_row = 1  # Row 2 in Google Sheet

    for col in range(df.shape[1] - 1, -1, -1):
        cell = str(df.iloc[header_row, col]).strip().lower()
        if cell == "status":
            return col

    raise ValueError("Status column not found in row 2")


def clean_status(value: str) -> str:
    if pd.isna(value):
        return ""

    s = unicodedata.normalize("NFKD", str(value))
    s = "".join(ch for ch in s if ch.isalnum())
    return s.lower()


def summarize_status(df: pd.DataFrame, status_col: int):

    task_col_index = 1  # Weekly Target column

    task_col = df.iloc[:, task_col_index].astype(str).str.strip()

    # ✅ Ignore empty rows AND summary rows like "Done/Total"
    task_mask = (
        task_col.ne("") &
        (~task_col.str.lower().isin(["done/total"]))
    )

    task_rows = df[task_mask]

    status_series = task_rows.iloc[:, status_col].apply(clean_status)

    completed_count = (status_series == "completed").sum()
    pending_count = (status_series == "pending").sum()

    if pending_count > 0:
        overall_status = "Pending"
    elif completed_count > 0:
        overall_status = "Completed"
    else:
        overall_status = "No Update"

    return overall_status, int(pending_count), int(completed_count)

# --------------------------------------------------
# AGGREGATION
# --------------------------------------------------
rows = []

with st.spinner("Fetching latest data from Google Sheets..."):
    for officer, (sid, gid) in OFFICER_SHEETS.items():
        try:
            df = load_sheet_csv(sid, gid)
            status_col = find_latest_status_column(df)
            overall, pending, completed = summarize_status(df, status_col)

            rows.append({
                "Officer Name": officer,
                "Overall Status": overall,
                "No. of Tasks Pending": pending,
                "No. of Tasks Completed": completed,
            })
        except Exception as e:
            rows.append({
                "Officer Name": officer,
                "Overall Status": "Error",
                "No. of Tasks Pending": None,
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
    st.subheader("📈 Pending Tasks by Officer")
    chart_df = summary_df.dropna(subset=["No. of Tasks Pending"])
    st.bar_chart(chart_df.set_index("Officer Name")["No. of Tasks Pending"])

if st.button("🔄 Refresh Latest Data"):
    st.rerun()

st.markdown("---")
st.info(
    "Rules applied: 'COMPLETED' → Completed | 'PENDING' → Pending | Blank ignored. "
    "Latest week detected using the rightmost 'Status' in Row 2."
)
