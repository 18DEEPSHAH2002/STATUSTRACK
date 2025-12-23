# app.py
# Streamlit Master Dashboard – FINAL GOVERNMENT SAFE VERSION
# Always reads LATEST WEEK (last column only)

import streamlit as st
import pandas as pd
import re
import unicodedata

st.set_page_config(page_title="Officer Task Status Dashboard", layout="wide")

st.title("📊 Master Dashboard – Officer Weekly Task Status")
st.caption("Latest week only • Pending / Completed counted correctly")

# --------------------------------------------------
# CONFIG
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
}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def load_sheet_csv(spreadsheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(url, header=None)


def clean_status(value):
    if pd.isna(value):
        return ""

    s = str(value)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'[\s\u200b\u200c\u200d\uFEFF]+', '', s)
    return s.lower()


def find_latest_status_column(df: pd.DataFrame) -> int:
    """
    Find the rightmost column that actually contains
    'pending' or 'completed' values.
    """
    for col in range(df.shape[1] - 1, -1, -1):
        col_values = (
            df.iloc[:, col]
            .astype(str)
            .apply(clean_status)
        )
        if col_values.isin(["pending", "completed"]).any():
            return col

    raise ValueError("No valid Status column found")


def summarize_status(df: pd.DataFrame):

    # ✅ Find TRUE latest week status column
    status_col = find_latest_status_column(df)

    task_col_index = 1  # Weekly Target / Subject column

    task_text = df.iloc[:, task_col_index].astype(str).str.strip()

    # Ignore empty + summary rows
    task_mask = (
        task_text.ne("") &
        (~task_text.str.lower().isin(["done/total"]))
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

with st.spinner("Fetching latest week data..."):
    for officer, (sid, gid) in OFFICER_SHEETS.items():
        try:
            df = load_sheet_csv(sid, gid)
            overall, pending, completed = summarize_status(df)

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
# UI
# --------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Officer-wise Status (Latest Week Only)")
    st.dataframe(summary_df, use_container_width=True)

with col2:
    st.subheader("📊 Pending Tasks by Officer")
    chart_df = summary_df.dropna(subset=["No. of Tasks Pending"])
    st.bar_chart(chart_df.set_index("Officer Name")["No. of Tasks Pending"])

st.markdown("---")
st.info(
    "Logic applied:\n"
    "• ONLY last column is treated as Status (latest week)\n"
    "• Pending & Completed counted strictly\n"
    "• Blank cells ignored\n"
    "• Done/Total rows ignored"
)
