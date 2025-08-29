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
    "OTHER ONLINE SERVICES": 0.0,
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
    sup_cols = ["id","date","user","supplier_name","service_type","service_amt","paid_amt","pending_amt","partial_amt","payment_type","notes"]
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

def filter_date(df, date_col="date", period="Daily", start=None, end=None):
    df[date_col] = pd.to_datetime(df[date_col])
    today = date.today()
    if period=="Daily":
        return df[df[date_col].dt.date==today]
    elif period=="Weekly":
        week_ago = today - timedelta(days=7)
        return df[df[date_col].dt.date>=week_ago]
    elif period=="Monthly":
        month_start = today.replace(day=1)
        return df[df[date_col].dt.date>=month_start]
    elif period=="Custom" and start and end:
        return df[(df[date_col].dt.date>=start) & (df[date_col].dt.date<=end)]
    else:
        return df

def color_status(val):
    if val=="Paid":
        return 'background-color: lightgreen'
    elif val=="Pending":
        return 'background-color: #ff9999'
    elif val=="Partial":
        return 'background-color: orange'
    return ''

# -------------------------
# Session State
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
    st.markdown("""
    - **admin / admin123**  
    - **user1 / user123**  
    - **user2 / user234**  
    - **mobile / mobile123**
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
# Service Entry Page
# -------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    df = load_csv(FILES["services"], svc_cols)
    customers = df["customer"].dropna().unique().tolist()

    with st.form("svc_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            customer = st.text_input("Customer / Agent", value="", placeholder="Start typing...")
            service_type = st.selectbox("Service Type", list(DEFAULT_GOVT_AMT.keys()))
        with c2:
            num_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1)
            default_amt = DEFAULT_GOVT_AMT.get(service_type,0.0)
            govt_amt = st.number_input("Government Amount (per app)", min_value=0.0, value=float(default_amt))
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
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"customer":customer,
                           "service_type":service_type,"num_apps":int(num_apps),"govt_amt":total_govt,
                           "paid_amt":total_paid,"profit_amt":profit,"status":status,"payment_type":payment_type,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["services"])
                st.success("Service added ✅")

    st.markdown("---")
    st.subheader("Your Services")
    df_user = df[df["user"]==user].sort_values("date", ascending=False)
    st.dataframe(df_user.style.applymap(color_status, subset=["status"]), use_container_width=True)
    st.download_button("⬇️ Download Services CSV", df_user.to_csv(index=False).encode(), f"services_{user}.csv")
    st.download_button("⬇️ Download Services Excel", df_to_excel_bytes(df_user,"Services"), f"services_{user}.xlsx")

    st.markdown("### 🔍 Customer / Agent History")
    customer_select = st.selectbox("Select Customer / Agent", customers)
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="svc_start")
    end_date = st.date_input("End Date", value=date.today(), key="svc_end")
    if customer_select:
        df_history = df[(df["customer"]==customer_select) & (pd.to_datetime(df["date"]).dt.date>=start_date) & (pd.to_datetime(df["date"]).dt.date<=end_date)]
        st.dataframe(df_history.style.applymap(color_status, subset=["status"]))
        st.download_button("⬇️ Download Customer History CSV", df_history.to_csv(index=False).encode(), f"{customer_select}_history.csv")
        st.download_button("⬇️ Download Customer History Excel", df_to_excel_bytes(df_history,f"{customer_select}_history"), f"{customer_select}_history.xlsx")

# -------------------------
# Expenses Page
# -------------------------
def expenses_entry_page():
    st.header("💵 Expenses Entry")
    user = st.session_state.user
    exp_cols = ["id","date","user","category","amount","notes"]
    df = load_csv(FILES["expenses"], exp_cols)

    with st.form("exp_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        category = st.text_input("Category")
        amount = st.number_input("Amount", min_value=0.0)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Expense"):
            if not category:
                st.error("Enter category")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,
                           "category":category,"amount":amount,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["expenses"])
                st.success("Expense added ✅")

    st.markdown("---")
    st.subheader("Your Expenses")
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="exp_start")
    end_date = st.date_input("End Date", value=date.today(), key="exp_end")
    df_user = df[(df["user"]==user) & (pd.to_datetime(df["date"]).dt.date>=start_date) & (pd.to_datetime(df["date"]).dt.date<=end_date)].sort_values("date", ascending=False)
    st.dataframe(df_user)
    st.download_button("⬇️ Download Expenses CSV", df_user.to_csv(index=False).encode(), f"expenses_{user}.csv")
    st.download_button("⬇️ Download Expenses Excel", df_to_excel_bytes(df_user,"Expenses"), f"expenses_{user}.xlsx")

# -------------------------
# Transactions Page
# -------------------------
def transactions_entry_page():
    st.header("💳 Transactions Entry")
    user = st.session_state.user
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    df = load_csv(FILES["transactions"], txn_cols)

    with st.form("txn_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        party = st.text_input("Party Name")
        service_type = st.text_input("Service Type")
        status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
        amount = st.number_input("Amount", min_value=0.0)
        payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Transaction"):
            if not party or not service_type:
                st.error("Enter party and service type")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,
                           "party":party,"service_type":service_type,"status":status,"amount":amount,
                           "payment_type":payment_type,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["transactions"])
                st.success("Transaction added ✅")

    st.markdown("---")
    st.subheader("Transactions")
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="txn_start")
    end_date = st.date_input("End Date", value=date.today(), key="txn_end")
    df_user = df[(df["user"]==user) & (pd.to_datetime(df["date"]).dt.date>=start_date) & (pd.to_datetime(df["date"]).dt.date<=end_date)].sort_values("date", ascending=False)
    st.dataframe(df_user.style.applymap(color_status, subset=["status"]))
    st.download_button("⬇️ Download Transactions CSV", df_user.to_csv(index=False).encode(), f"transactions_{user}.csv")
    st.download_button("⬇️ Download Transactions Excel", df_to_excel_bytes(df_user,"Transactions"), f"transactions_{user}.xlsx")

# -------------------------
# Suppliers Page (Enhanced)
# -------------------------
def suppliers_entry_page():
    st.header("🏢 Suppliers Entry")
    user = st.session_state.user
    sup_cols = ["id","date","user","supplier_name","service_type","service_amt","paid_amt","pending_amt","partial_amt","payment_type","notes"]
    df = load_csv(FILES["suppliers"], sup_cols)
    suppliers = df["supplier_name"].dropna().unique().tolist()

    with st.form("sup_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        supplier = st.text_input("Supplier Name")
        service_type = st.selectbox("Service Type", list(DEFAULT_GOVT_AMT.keys()))
        service_amt = st.number_input("Total Service Amount", min_value=0.0)
        paid_amt = st.number_input("Paid Amount to Supplier", min_value=0.0)
        pending_amt = round(service_amt - paid_amt, 2)
        partial_amt = st.number_input("Partial Amount (if any)", min_value=0.0, value=0.0)
        payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
        notes = st.text_input("Notes (optional)")

        st.markdown(f"**Calculated Pending Amount:** ₹{pending_amt}")

        if st.form_submit_button("➕ Add Supplier Entry"):
            if not supplier:
                st.error("Enter supplier name")
            else:
                nid = next_id(df)
                new_row = {
                    "id":nid,
                    "date":entry_date.strftime("%Y-%m-%d"),
                    "user":user,
                    "supplier_name":supplier,
                    "service_type":service_type,
                    "service_amt":service_amt,
                    "paid_amt":paid_amt,
                    "pending_amt":pending_amt,
                    "partial_amt":partial_amt,
                    "payment_type":payment_type,
                    "notes":notes
                }
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["suppliers"])
                st.success("Supplier entry added ✅")

    st.markdown("---")
    st.subheader("Suppliers Transactions History")
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="sup_start")
    end_date = st.date_input("End Date", value=date.today(), key="sup_end")
    df_user = df[(df["user"]==user) & 
                 (pd.to_datetime(df["date"]).dt.date>=start_date) & 
                 (pd.to_datetime(df["date"]).dt.date<=end_date)].sort_values("date", ascending=False)
    st.dataframe(df_user)
    st.download_button("⬇️ Download Suppliers CSV", df_user.to_csv(index=False).encode(), f"suppliers_{user}.csv")
    st.download_button("⬇️ Download Suppliers Excel", df_to_excel_bytes(df_user,"Suppliers"), f"suppliers_{user}.xlsx")

    st.markdown("### 🔍 Supplier Wise History")
    supplier_select = st.selectbox("Select Supplier", suppliers)
    if supplier_select:
        df_history = df[df["supplier_name"]==supplier_select].sort_values("date", ascending=False)
        st.dataframe(df_history)
        st.download_button("⬇️ Download Supplier History CSV", df_history.to_csv(index=False).encode(), f"{supplier_select}_history.csv")
        st.download_button("⬇️ Download Supplier History Excel", df_to_excel_bytes(df_history,f"{supplier_select}_history"), f"{supplier_select}_history.xlsx")

# -------------------------
# Dashboard
# -------------------------
def dashboard_summary():
    st.header("📊 Dashboard Summary")
    user = st.session_state.user

    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","service_amt","paid_amt","pending_amt","partial_amt","payment_type","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]

    df_svc = load_csv(FILES["services"], svc_cols)
    df_txn = load_csv(FILES["transactions"], txn_cols)
    df_sup = load_csv(FILES["suppliers"], sup_cols)
    df_exp = load_csv(FILES["expenses"], exp_cols)

    df_svc_user = df_svc[df_svc["user"]==user]
    df_txn_user = df_txn[df_txn["user"]==user]
    df_sup_user = df_sup[df_sup["user"]==user]
    df_exp_user = df_exp[df_exp["user"]==user]

    svc_summary = df_svc_user.groupby("status")["paid_amt"].sum().reindex(["Paid","Pending","Partial"]).fillna(0)
    exp_total = df_exp_user["amount"].sum()
    sup_pending = df_sup_user["pending_amt"].sum()

    st.metric("Total Service Paid", f"₹{df_svc_user['paid_amt'].sum():.2f}")
    st.metric("Total Profit", f"₹{df_svc_user['profit_amt'].sum():.2f}")
    st.metric("Total Expenses", f"₹{exp_total:.2f}")
    st.metric("Total Supplier Pending", f"₹{sup_pending:.2f}")

# -------------------------
# Main App
# -------------------------
def main():
    if not st.session_state.user:
        login_page()
    else:
        menu = ["Dashboard","Service Entry","Transactions","Expenses","Suppliers","Logout"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice=="Dashboard":
            dashboard_summary()
        elif choice=="Service Entry":
            service_entry_page()
        elif choice=="Expenses":
            expenses_entry_page()
        elif choice=="Transactions":
            transactions_entry_page()
        elif choice=="Suppliers":
            suppliers_entry_page()
        elif choice=="Logout":
            logout()

if __name__=="__main__":
    main()
