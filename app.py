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
os.makedirs(DATA_FOLDER, exist_ok=True)

FILES = {
    "services": os.path.join(DATA_FOLDER, "services.csv"),
    "expenses": os.path.join(DATA_FOLDER, "expenses.csv"),
    "transactions": os.path.join(DATA_FOLDER, "transactions.csv"),
    "suppliers": os.path.join(DATA_FOLDER, "suppliers.csv"),
    "customers": os.path.join(DATA_FOLDER, "customers.csv"),
    "parties": os.path.join(DATA_FOLDER, "parties.csv")
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
    "NAME CHANGE AADHAR CARD": 0.0,
    "DATE OF BIRTH CHANGE IN AADHAR CARD": 0.0,
    "AADHAR CARD PRINT": 0.0,
    "BIRTH CERTIFICATE": 3000.0,
    "OTHER ONLINE SERVICES": 0.0
}

# -------------------------
# Utilities
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

def ensure_datafiles_exist():
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","payment_type","notes"]
    cust_cols = ["customer_name"]
    party_cols = ["party_name"]
    for key, cols in zip(FILES.keys(), [svc_cols, exp_cols, txn_cols, sup_cols, cust_cols, party_cols]):
        if not os.path.exists(FILES[key]):
            save_csv(pd.DataFrame(columns=cols), FILES[key])

def next_id(df):
    if df.empty:
        return 1
    try:
        return int(df["id"].max()) + 1
    except Exception:
        return len(df) + 1

def color_status(val):
    if val=="Paid":
        color = 'background-color: lightgreen'
    elif val=="Pending":
        color = 'background-color: #ff9999'
    elif val=="Partial":
        color = 'background-color: orange'
    else:
        color = ''
    return color

def filter_date(df, date_col="date", start_date=None, end_date=None):
    df[date_col] = pd.to_datetime(df[date_col])
    if start_date:
        df = df[df[date_col].dt.date>=start_date]
    if end_date:
        df = df[df[date_col].dt.date<=end_date]
    return df

# -------------------------
# Session State Init
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "device" not in st.session_state:
    st.session_state.device = None

ensure_datafiles_exist()

# -------------------------
# Authentication
# -------------------------
def login_page():
    st.title("🔐 Login - NANI ASSOCIATES")
    st.write("Use one of the predefined accounts:")
    st.markdown("""
    - **admin / admin123** (desktop)  
    - **user1 / user123** (desktop)  
    - **user2 / user234** (desktop)  
    - **mobile / mobile123** (mobile)
    """)
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
    df_customers = load_csv(FILES["customers"], ["customer_name"])
    customer_list = df_customers["customer_name"].dropna().tolist()

    with st.form("svc_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            customer = st.selectbox("Customer / Agent", [""]+customer_list)
            service_type = st.selectbox("Service Type", list(DEFAULT_GOVT_AMT.keys()))
        with c2:
            num_apps = st.number_input("No. of Applications", min_value=1, value=1)
            default_amt = DEFAULT_GOVT_AMT.get(service_type,0.0)
            govt_amt = st.number_input("Government Amount (per app)", value=float(default_amt))
            paid_amt = st.number_input("Paid Amount (per app)", min_value=0.0, value=0.0)
            status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
            payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
            notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Service"):
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
                if customer not in customer_list:
                    df_customers = pd.concat([df_customers,pd.DataFrame([{"customer_name":customer}])], ignore_index=True)
                    save_csv(df_customers, FILES["customers"])
                st.success("Service added ✅")

    st.markdown("---")
    st.subheader("Search / Filter Services")
    start_date = st.date_input("From Date", value=date.today()-timedelta(days=30), key="svc_start")
    end_date = st.date_input("To Date", value=date.today(), key="svc_end")
    search_customer = st.text_input("Customer / Agent Filter", key="svc_search")
    df_filtered = filter_date(df, "date", start_date, end_date)
    if search_customer:
        df_filtered = df_filtered[df_filtered["customer"].str.contains(search_customer, case=False, na=False)]
    st.dataframe(df_filtered.style.applymap(color_status, subset=["status"]), use_container_width=True)
    st.download_button("⬇️ Download CSV", df_filtered.to_csv(index=False).encode(), f"services_{user}.csv")
    st.download_button("⬇️ Download Excel", df_to_excel_bytes(df_filtered,"Services"), f"services_{user}.xlsx")

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
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Menu", [
        "Service Entry",
        # Additional pages (Expenses, Transactions, Suppliers, Dashboard) can be added similarly
    ])
    if page=="Service Entry":
        service_entry_page()

if __name__=="__main__":
    main()
