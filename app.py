# appy.py
import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
from io import BytesIO

# -------------------------
# Config / Credentials
# -------------------------
DATA_FOLDER = "data"
BACKUP_FOLDER = "backup"
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

FILES = {
    "services": os.path.join(DATA_FOLDER, "services.csv"),
    "expenses": os.path.join(DATA_FOLDER, "expenses.csv"),
    "transactions": os.path.join(DATA_FOLDER, "transactions.csv"),
    "suppliers": os.path.join(DATA_FOLDER, "suppliers.csv"),
}

USER_CREDENTIALS = {
    "admin": "admin123",
    "user1": "user123",
    "user2": "user234",
    "mobile": "mobile123",
}

PAYMENT_TYPES = ["Cash","UPI","Bank Transfer","Cheque","Other"]
DEFAULT_GOVT_AMT = {
    "NEW PAN CARD": 107.0,
    "CORRECTION PAN CARD": 107.0,
    "NEW PASSPORT": 1500.0,
    "RENEWAL PASSPORT": 1500.0,
    "DIGITAL SIGNATURE": 1400.0,
    "VOTER ID": 0.0,
    "NEW AADHAR CARD": 100.0,
    "NAME CHANGE AADHAR CARD": None,
    "DATE OF BIRTH CHANGE IN AADHAR CARD": None,
    "BIRTH CERTIFICATE": 3000.0,
    "OTHER ONLINE SERVICES": None
}

# -------------------------
# Utility Functions
# -------------------------
def df_to_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return out.getvalue()

def load_csv(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            for c in columns:
                if c not in df.columns:
                    df[c] = ""
            return df[columns]
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def backup_csv(file_path):
    if os.path.exists(file_path):
        fname = os.path.basename(file_path)
        save_csv(load_csv(file_path, []), os.path.join(BACKUP_FOLDER, f"backup_{fname}"))

def ensure_datafiles_exist():
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","payment_type","notes"]
    for key, cols in zip(FILES.keys(), [svc_cols, exp_cols, txn_cols, sup_cols]):
        if not os.path.exists(FILES[key]):
            save_csv(pd.DataFrame(columns=cols), FILES[key])

def next_id(df):
    if df.empty:
        return 1
    try:
        return int(df["id"].max()) + 1
    except Exception:
        return len(df) + 1

def filter_date(df, date_col="date", start=None, end=None):
    df[date_col] = pd.to_datetime(df[date_col])
    if start:
        df = df[df[date_col].dt.date >= start]
    if end:
        df = df[df[date_col].dt.date <= end]
    return df

def color_status(val):
    if val=="Paid": color='background-color: lightgreen'
    elif val=="Pending": color='background-color: #ff9999'
    elif val=="Partial": color='background-color: orange'
    else: color=''
    return color

# -------------------------
# Session State Init
# -------------------------
if "user" not in st.session_state: st.session_state.user = None
if "device" not in st.session_state: st.session_state.device = None
if "customers" not in st.session_state: st.session_state.customers = []

ensure_datafiles_exist()

# -------------------------
# Authentication
# -------------------------
def login_page():
    st.title("🔐 Login - NANI ASSOCIATES")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username]==password:
                st.session_state.user = username
                st.session_state.device = "mobile" if username=="mobile" else "desktop"
                st.success(f"Logged in as {username}")
            else:
                st.error("Invalid username or password")

def logout():
    st.session_state.user = None
    st.session_state.device = None
    st.success("Logged out")

# -------------------------
# Service Entry
# -------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    df = load_csv(FILES["services"], svc_cols)

    # Auto pickup customers
    customers = st.session_state.customers

    with st.form("svc_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            customer = st.selectbox("Customer / Agent", options=customers)
            new_customer = st.text_input("Or add new customer")
            service_type = st.selectbox("Service Type", list(DEFAULT_GOVT_AMT.keys()))
        with c2:
            num_apps = st.number_input("No. of Applications", min_value=1, value=1)
            default_amt = DEFAULT_GOVT_AMT.get(service_type, 0.0)
            govt_amt = st.number_input("Government Amount (per app)", value=default_amt if default_amt else 0.0)
            paid_amt = st.number_input("Paid Amount (per app)", min_value=0.0, value=0.0)
            status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
            payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
            notes = st.text_input("Notes (optional)")

        if st.form_submit_button("➕ Add Service"):
            if new_customer:
                customer = new_customer
                if customer not in customers: st.session_state.customers.append(customer)
            if not customer:
                st.error("Enter customer / agent name")
            else:
                total_govt = round(num_apps*govt_amt,2)
                total_paid = round(num_apps*paid_amt,2)
                profit = round(total_paid-total_govt,2)
                nid = next_id(df)
                new_row = {
                    "id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"customer":customer,
                    "service_type":service_type,"num_apps":int(num_apps),"govt_amt":total_govt,
                    "paid_amt":total_paid,"profit_amt":profit,"status":status,"payment_type":payment_type,"notes":notes
                }
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["services"])
                st.success("Service added ✅")

    # Date filter
    st.markdown("---")
    st.subheader("Search Services by Date")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    df_filtered = filter_date(df, "date", start_date, end_date)
    st.dataframe(df_filtered.style.applymap(color_status, subset=["status"]), use_container_width=True)
    st.download_button("⬇️ Download CSV", df_filtered.to_csv(index=False).encode(), f"services_{user}.csv")
    st.download_button("⬇️ Download Excel", df_to_excel_bytes(df_filtered,"Services"), f"services_{user}.xlsx")

# Similar pages can be created for Expenses, Transactions, Suppliers with date filter, CSV/Excel, payments

# -------------------------
# Main
# -------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES - Tracker", layout="wide")
    if st.session_state.user is None:
        login_page()
        return

    st.sidebar.title("📊 NANI ASSOCIATES")
    st.sidebar.write(f"Logged in as: **{st.session_state.user}** ({st.session_state.device})")
    if st.sidebar.button("Logout"): logout()
    if st.sidebar.button("Backup All Data"):
        for f in FILES.values(): backup_csv(f)
        st.success("Backup completed ✅")

    page = st.sidebar.radio("Menu", ["Service Entry"])
    if page=="Service Entry": service_entry_page()

if __name__=="__main__": main()
