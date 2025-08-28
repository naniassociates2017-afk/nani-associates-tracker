# app.py
import streamlit as st
import pandas as pd
import os
from datetime import date
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

# -------------------------
# Utilities
# -------------------------
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

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
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    for key, cols in zip(FILES.keys(), [svc_cols, exp_cols, txn_cols, sup_cols]):
        if not os.path.exists(FILES[key]):
            save_csv(pd.DataFrame(columns=cols), FILES[key])

def next_id(df):
    if df.empty:
        return 1
    else:
        return int(df["id"].max()) + 1

# -------------------------
# Session
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
    st.write("Accounts: admin/user1/user2/mobile")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username]==password:
                st.session_state.user = username
                st.session_state.device = "mobile" if username=="mobile" else "desktop"
                st.success(f"Welcome {username}")
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state.user = None
    st.session_state.device = None
    st.success("Logged out")
    st.rerun()

# -------------------------
# Table Display with Inline Edit/Delete
# -------------------------
def display_table(df, file_path, key_prefix, editable_cols):
    if df.empty:
        st.info("No data available")
        return
    st.dataframe(df)
    for idx, row in df.iterrows():
        with st.expander(f"Edit/Delete Row ID: {row['id']}"):
            updated = {}
            for col in editable_cols:
                updated[col] = st.text_input(col, value=str(row[col]), key=f"{key_prefix}_{col}_{row['id']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save", key=f"save_{key_prefix}_{row['id']}"):
                    for col in editable_cols:
                        df.loc[df["id"]==row["id"], col] = updated[col]
                    save_csv(df, file_path)
                    st.success("Row updated")
                    st.experimental_rerun()
            with col2:
                if st.button("Delete", key=f"del_{key_prefix}_{row['id']}"):
                    df.drop(idx, inplace=True)
                    save_csv(df, file_path)
                    st.success("Row deleted")
                    st.experimental_rerun()

# -------------------------
# Pages
# -------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"]
    df = load_csv(FILES["services"], svc_cols)

    with st.form("svc_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            customer = st.text_input("Customer / Agent")
            service_type = st.selectbox("Service Type", ["NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","DIGITAL SIGNATURE","VOTER ID","NEW AADHAR CARD","NAME CHANGE AADHAR CARD","ADDRESS CHANGE AADHAR CARD","DATE OF BIRTH CHANGE AADHAR CARD","AADHAR PRINT","BIRTH CERTIFICATE","OTHER ONLINE SERVICES"])
        with c2:
            no_apps = st.number_input("No. of Applications", min_value=1, value=1)
            govt_per = st.number_input("Govt Amount per app", min_value=0.0)
            paid_per = st.number_input("Paid Amount per app", min_value=0.0)
            status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
            notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Service"):
            if not customer:
                st.error("Enter customer/agent")
            else:
                total_govt = round(no_apps*govt_per,2)
                total_paid = round(no_apps*paid_per,2)
                profit = round(total_paid - total_govt,2)
                nid = next_id(df)
                df = pd.concat([df, pd.DataFrame([{
                    "id": nid,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "user": user,
                    "customer": customer,
                    "service_type": service_type,
                    "num_apps": int(no_apps),
                    "govt_amt": total_govt,
                    "paid_amt": total_paid,
                    "profit_amt": profit,
                    "status": status,
                    "notes": notes
                }])], ignore_index=True)
                save_csv(df, FILES["services"])
                st.success("Service added")
                st.rerun()
    st.subheader("Your Services")
    df_user = df[df["user"]==user].sort_values("date",ascending=False)
    display_table(df_user, FILES["services"], "svc", editable_cols=["customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"])

def transactions_page():
    st.header("🔄 Transactions")
    user = st.session_state.user
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    df = load_csv(FILES["transactions"], txn_cols)

    with st.form("txn_add_form", clear_on_submit=True):
        t_date = st.date_input("Date", value=date.today())
        party = st.text_input("Customer / Agent")
        service_type = st.selectbox("Service Type", ["","NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","NEW AADHAR CARD","OTHER"])
        status = st.selectbox("Status", ["Paid","Pending","Partial"])
        amount = st.number_input("Amount", min_value=0.0)
        notes = st.text_input("Notes")
        if st.form_submit_button("➕ Add Transaction"):
            if not party:
                st.error("Enter party name")
            else:
                nid = next_id(df)
                df = pd.concat([df,pd.DataFrame([{
                    "id":nid,
                    "date":t_date.strftime("%Y-%m-%d"),
                    "user":user,
                    "party":party,
                    "service_type":service_type,
                    "status":status,
                    "amount":round(amount,2),
                    "notes":notes
                }])],ignore_index=True)
                save_csv(df, FILES["transactions"])
                st.success("Transaction added")
                st.rerun()
    st.subheader("Your Transactions")
    df_user = df[df["user"]==user].sort_values("date",ascending=False)
    display_table(df_user, FILES["transactions"], "txn", editable_cols=["party","service_type","status","amount","notes"])

def expenses_page():
    st.header("💸 Expenses")
    user = st.session_state.user
    exp_cols = ["id","date","user","category","amount","notes"]
    df = load_csv(FILES["expenses"], exp_cols)

    with st.form("exp_add_form", clear_on_submit=True):
        e_date = st.date_input("Date", value=date.today())
        category = st.text_input("Category")
        amount = st.number_input("Amount", min_value=0.0)
        notes = st.text_input("Notes")
        if st.form_submit_button("➕ Add Expense"):
            if not category:
                st.error("Enter category")
            else:
                nid = next_id(df)
                df = pd.concat([df,pd.DataFrame([{
                    "id":nid,
                    "date":e_date.strftime("%Y-%m-%d"),
                    "user":user,
                    "category":category,
                    "amount":round(amount,2),
                    "notes":notes
                }])],ignore_index=True)
                save_csv(df, FILES["expenses"])
                st.success("Expense added")
                st.rerun()
    st.subheader("Your Expenses")
    df_user = df[df["user"]==user].sort_values("date",ascending=False)
    display_table(df_user, FILES["expenses"], "exp", editable_cols=["category","amount","notes"])

def suppliers_page():
    st.header("🏢 Suppliers")
    user = st.session_state.user
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    df = load_csv(FILES["suppliers"], sup_cols)

    with st.form("sup_add_form", clear_on_submit=True):
        s_date = st.date_input("Date", value=date.today())
        supplier_name = st.text_input("Supplier Name")
        service_type = st.text_input("Service Type")
        paid_amt = st.number_input("Paid Amount", min_value=0.0)
        pending_amt = st.number_input("Pending Amount", min_value=0.0)
        partial_amt = st.number_input("Partial Amount", min_value=0.0)
        notes = st.text_input("Notes")
        if st.form_submit_button("➕ Add Supplier"):
            if not supplier_name:
                st.error("Enter supplier name")
            else:
                nid = next_id(df)
                df = pd.concat([df,pd.DataFrame([{
                    "id":nid,
                    "date":s_date.strftime("%Y-%m-%d"),
                    "user":user,
                    "supplier_name":supplier_name,
                    "service_type":service_type,
                    "paid_amt":round(paid_amt,2),
                    "pending_amt":round(pending_amt,2),
                    "partial_amt":round(partial_amt,2),
                    "notes":notes
                }])],ignore_index=True)
                save_csv(df, FILES["suppliers"])
                st.success("Supplier added")
                st.rerun()
    st.subheader("Your Suppliers")
    df_user = df[df["user"]==user].sort_values("date",ascending=False)
    display_table(df_user, FILES["suppliers"], "sup", editable_cols=["supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"])

# -------------------------
# Dashboard
# -------------------------
def dashboard_page():
    st.header("📊 Dashboard")
    user = st.session_state.user

    # Load all data
    df_svc = load_csv(FILES["services"], ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"])
    df_txn = load_csv(FILES["transactions"], ["id","date","user","party","service_type","status","amount","notes"])
    df_exp = load_csv(FILES["expenses"], ["id","date","user","category","amount","notes"])
    df_sup = load_csv(FILES["suppliers"], ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"])

    df_svc_user = df_svc[df_svc["user"]==user]
    df_txn_user = df_txn[df_txn["user"]==user]
    df_exp_user = df_exp[df_exp["user"]==user]
    df_sup_user = df_sup[df_sup["user"]==user]

    st.subheader("Service Summary")
    if not df_svc_user.empty:
        total_govt = df_svc_user["govt_amt"].sum()
        total_paid = df_svc_user["paid_amt"].sum()
        total_profit = df_svc_user["profit_amt"].sum()
        st.metric("Total Govt Amt", f"{total_govt}")
        st.metric("Total Paid Amt", f"{total_paid}")
        st.metric("Total Profit", f"{total_profit}")
        st.dataframe(df_svc_user.groupby("status")["id"].count().rename("Count").reset_index())
    else:
        st.info("No service data")

    st.subheader("Transactions Summary")
    if not df_txn_user.empty:
        st.dataframe(df_txn_user.groupby("status")["amount"].sum().reset_index())
    else:
        st.info("No transactions")

    st.subheader("Expenses Summary")
    if not df_exp_user.empty:
        st.dataframe(df_exp_user.groupby("category")["amount"].sum().reset_index())
    else:
        st.info("No expenses")

    st.subheader("Suppliers Summary")
    if not df_sup_user.empty:
        st.dataframe(df_sup_user.groupby("service_type")[["paid_amt","pending_amt","partial_amt"]].sum().reset_index())
    else:
        st.info("No suppliers")

# -------------------------
# Main
# -------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES", layout="wide")
    if st.session_state.user is None:
        login_page()
        return

    st.sidebar.title("📊 NANI ASSOCIATES")
    st.sidebar.write(f"Logged in as: **{st.session_state.user}** ({st.session_state.device})")
    if st.sidebar.button("Logout"):
        logout()
        return

    page = st.sidebar.radio("Menu", ["Dashboard","Service Entry","Transactions","Expenses","Suppliers"], index=0)

    try:
        if page=="Dashboard":
            dashboard_page()
        elif page=="Service Entry":
            service_entry_page()
        elif page=="Transactions":
            transactions_page()
        elif page=="Expenses":
            expenses_page()
        elif page=="Suppliers":
            suppliers_page()
    except Exception as e:
        st.error(f"Unexpected error: {e}")

if __name__=="__main__":
    main()
