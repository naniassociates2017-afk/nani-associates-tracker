# app.py
import streamlit as st
import pandas as pd
import os
from datetime import date

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

# -------------------------
# Utility functions
# -------------------------
def load_csv(file_path, columns):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        for c in columns:
            if c not in df.columns:
                df[c] = ""
        return df[columns]
    return pd.DataFrame(columns=columns)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def ensure_datafiles_exist():
    svc_cols = ["id","date","user","customer","service_type","status","num_apps","govt_amt","paid_amt","profit_amt","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    for key, cols in zip(FILES.keys(), [svc_cols, exp_cols, txn_cols, sup_cols]):
        if not os.path.exists(FILES[key]):
            save_csv(pd.DataFrame(columns=cols), FILES[key])

def next_id(df):
    return 1 if df.empty else int(df["id"].max()) + 1

# -------------------------
# Session state init
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -------------------------
# Authentication
# -------------------------
def login_page():
    st.title("🔐 Login")
    st.write("Predefined accounts: admin/user1/user2/mobile")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.user = username
            st.success(f"Welcome {username}")
        else:
            st.error("Invalid credentials")

def logout():
    st.session_state.user = None
    st.experimental_rerun()

# -------------------------
# Main Pages
# -------------------------
def service_entry():
    st.header("📋 Service Entry")
    df = load_csv(FILES["services"], ["id","date","user","customer","service_type","status","num_apps","govt_amt","paid_amt","profit_amt","notes"])
    with st.form("service_form"):
        customer = st.text_input("Customer")
        service_type = st.selectbox("Service Type", ["Type A", "Type B", "Type C"])
        status = st.selectbox("Payment Status", ["Pending", "Partial", "Paid"])
        num_apps = st.number_input("Number of Applications", min_value=0)
        govt_amt = st.number_input("Govt Amount")
        paid_amt = st.number_input("Paid Amount")
        profit_amt = st.number_input("Profit Amount")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Service")
        if submitted:
            new_id = next_id(df)
            new_row = {"id": new_id,"date": str(date.today()),"user": st.session_state.user,
                       "customer": customer,"service_type": service_type,"status": status,
                       "num_apps": num_apps,"govt_amt": govt_amt,"paid_amt": paid_amt,
                       "profit_amt": profit_amt,"notes": notes}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(df, FILES["services"])
            st.success("Service added!")
    st.dataframe(df)

def transactions_page():
    st.header("💰 Transactions")
    df = load_csv(FILES["transactions"], ["id","date","user","party","service_type","status","amount","notes"])
    with st.form("txn_form"):
        party = st.text_input("Party Name")
        service_type = st.selectbox("Service Type", ["Type A", "Type B", "Type C"])
        status = st.selectbox("Payment Status", ["Pending", "Partial", "Paid"])
        amount = st.number_input("Amount")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            new_id = next_id(df)
            new_row = {"id": new_id,"date": str(date.today()),"user": st.session_state.user,
                       "party": party,"service_type": service_type,"status": status,
                       "amount": amount,"notes": notes}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(df, FILES["transactions"])
            st.success("Transaction added!")
    st.dataframe(df)

# -------------------------
# App Navigation
# -------------------------
if st.session_state.user is None:
    login_page()
else:
    st.sidebar.write(f"Logged in as: {st.session_state.user}")
    page = st.sidebar.selectbox("Navigate", ["Service Entry", "Transactions", "Logout"])
    if page == "Service Entry":
        service_entry()
    elif page == "Transactions":
        transactions_page()
    elif page == "Logout":
        logout()
