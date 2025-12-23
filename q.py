# streamlit_app.py
# Master Dashboard: Officer-wise Task Status from multiple Google Sheets

import streamlit as st
import pandas as pd


st.set_page_config(page_title="Master Dashboard – Weekly Task Status", layout="wide")
st.title("📊 Master Dashboard – Officer-wise Weekly Task Status")

# =============================
# 1. GOOGLE SHEETS AUTH
# =============================
# Create a service account in Google Cloud Console
# Download service_account.json and keep it secure

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

@st.cache_resource

def get_gspread_client():
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
    return gspread.authorize(creds)

client = get_gspread_client()

# =============================
# 2. OFFICER SHEET CONFIG
# =============================

OFFICER_SHEETS = {
    "ADC G": 174981592,
    "ADC D": 537074213,
    "ADC (UD)": 846764018,
    "ADC K": 1476602908,
    "ADC J": 18822170,
    "ACG": 1291568180,
    "CMFO": 1227420096,
    "SDM East": 33416154,
    "SDM West": 52989510,
    "SDM Raikot": 1833732603,
    "SDM Samrala": 190794459,
    "SDM Khanna": 2054147547,
    "SDM Jagraon": 278920499,
    "SDM Payal": 778489712,
    "DRO": 501565659,
    "RTA": 1563439729
}

SPREADSHEET_ID = "1jspebqSTXgEtYyxYAE47_uRn6RQKFlHQhneuQoGiCok"

# =============================
# 3. CORE LOGIC
# =============================

def extract_latest_status(df: pd.DataFrame):
    """
    Logic:
    - Sheet has repeating blocks of [Weekly Target | Achieved | Meeting | Status]
    - Always take the LAST 'Status' column (latest week)
    - Count Pending vs Completed
    """

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Find all status columns
    status_cols = [c for c in df.columns if "status" in c]

    if not status_cols:
        return 0, "Complete"

    latest_status_col = status_cols[-1]

    # Drop empty rows
    status_series = df[latest_status_col].dropna().astype(str).str.lower()

    incomplete_count = status_series.isin(["pending", "incomplete"]).sum()

    overall_status = "Incomplete" if incomplete_count > 0 else "Complete"

    return incomplete_count, overall_status

# =============================
# 4. BUILD DASHBOARD TABLE
# =============================

def build_dashboard():
    rows = []

    for officer, gid in OFFICER_SHEETS.items():
        try:
            sh = client.open_by_key(SPREADSHEET_ID)
            ws = sh.get_worksheet_by_id(gid)
            data = ws.get_all_records()
            df = pd.DataFrame(data)

            incomplete_count, status = extract_latest_status(df)

            rows.append({
                "Officer Name": officer,
                "Overall Status": status,
                "No. of Tasks Incomplete": incomplete_count
            })

        except Exception as e:
            rows.append({
                "Officer Name": officer,
                "Overall Status": "Error",
                "No. of Tasks Incomplete": 0
            })

    return pd.DataFrame(rows)

# =============================
# 5. RENDER
# =============================

df_dashboard = build_dashboard()

st.subheader("📋 Weekly Status Summary (Latest Week Only)")
st.dataframe(df_dashboard, use_container_width=True)

# =============================
# 6. GRAPH
# =============================

st.subheader("📊 Incomplete Tasks by Officer")

chart_df = df_dashboard.set_index("Officer Name")["No. of Tasks Incomplete"]
st.bar_chart(chart_df)

st.caption("Status logic: If ANY task in latest week is Pending/Incomplete → Officer marked Incomplete")
