# app.py
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
from io import BytesIO

# -------------------------
# Config / Credentials
# -------------------------
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# CSV file paths
FILES = {
    "services": os.path.join(DATA_FOLDER, "services.csv"),
    "expenses": os.path.join(DATA_FOLDER, "expenses.csv"),
    "transactions": os.path.join(DATA_FOLDER, "transactions.csv"),
    "suppliers": os.path.join(DATA_FOLDER, "suppliers.csv"),
}

# Hardcoded users (3 desktop + 1 mobile)
USER_CREDENTIALS = {
    "admin": "admin123",   # desktop
    "user1": "user123",    # desktop
    "user2": "user234",    # desktop
    "mobile": "mobile123", # mobile
}

# -------------------------
# Utility functions
# -------------------------
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return out.getvalue()

def load_csv(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Ensure expected columns exist
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
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    if not os.path.exists(FILES["services"]):
        save_csv(pd.DataFrame(columns=svc_cols), FILES["services"])
    if not os.path.exists(FILES["expenses"]):
        save_csv(pd.DataFrame(columns=exp_cols), FILES["expenses"])
    if not os.path.exists(FILES["transactions"]):
        save_csv(pd.DataFrame(columns=txn_cols), FILES["transactions"])
    if not os.path.exists(FILES["suppliers"]):
        save_csv(pd.DataFrame(columns=sup_cols), FILES["suppliers"])

def next_id(df):
    if df.empty:
        return 1
    else:
        try:
            return int(df["id"].max()) + 1
        except Exception:
            return len(df) + 1

# -------------------------
# Session state init
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "device" not in st.session_state:
    st.session_state.device = None

ensure_datafiles_exist()

# -------------------------
# Authentication UI
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
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.user = username
                st.session_state.device = "mobile" if username == "mobile" else "desktop"
                st.success(f"Welcome {username} 👋")
                st.rerun()
            else:
                st.error("Invalid username or password")

def logout():
    st.session_state.user = None
    st.session_state.device = None
    st.success("Logged out")
    st.rerun()

# -------------------------
# SERVICES: add / edit / delete
# -------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user = st.session_state.user

    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","notes"]
    df = load_csv(FILES["services"], svc_cols)

    with st.form("svc_add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today(), key="svc_date")
            customer = st.text_input("Customer / Agent", key="svc_customer")
            service_type = st.selectbox("Service Type", [
                "NEW PAN CARD", "CORRECTION PAN CARD", "NEW PASSPORT", "RENEWAL PASSPORT",
                "DIGITAL SIGNATURE", "VOTER ID", "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
                "ADDRESS CHANGE IN AADHAR CARD", "DATE OF BIRTH CHANGE IN AADHAR CARD",
                "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
            ], key="svc_type")
        with c2:
            no_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1, key="svc_apps")
            govt_per = st.number_input("Government Amount (per app)", min_value=0.0, value=0.0, key="svc_govt_per")
            paid_per = st.number_input("Paid Amount (per app)", min_value=0.0, value=0.0, key="svc_paid_per")
            notes = st.text_input("Notes (optional)", key="svc_notes")
        add = st.form_submit_button("➕ Add Service")
        if add:
            if not customer:
                st.error("Enter customer / agent name")
            else:
                total_govt = round(no_apps * govt_per, 2)
                total_paid = round(no_apps * paid_per, 2)
                profit = round(total_paid - total_govt, 2)
                nid = next_id(df)
                new_row = {
                    "id": nid,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "user": user,
                    "customer": customer,
                    "service_type": service_type,
                    "num_apps": int(no_apps),
                    "govt_amt": total_govt,
                    "paid_amt": total_paid,
                    "profit_amt": profit,
                    "notes": notes
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["services"])
                st.success("Service added ✅")
                st.rerun()

    st.markdown("---")
    st.subheader("Your Services (most recent first)")
    df_user = df[df["user"] == user].sort_values("date", ascending=False)
    if df_user.empty:
        st.info("No services yet")
    else:
        st.dataframe(df_user, use_container_width=True)

        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            try:
                min_id = int(df_user["id"].min())
                max_id = int(df_user["id"].max())
                sel_id = int(st.number_input("Enter Service ID to Edit/Delete", min_value=min_id, max_value=max_id, step=1, key="svc_sel_id"))
            except Exception:
                sel_id = None
        with col2:
            if st.button("✏️ Edit Service", key="svc_edit_btn"):
                if sel_id is None:
                    st.error("No valid ID selected")
                else:
                    rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                    if rec.empty:
                        st.error("Record not found or not yours")
                    else:
                        r = rec.iloc[0]
                        with st.form(f"svc_edit_form_{sel_id}", clear_on_submit=False):
                            e_date = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_svc_date_{sel_id}")
                            e_customer = st.text_input("Customer / Agent", value=r["customer"], key=f"edit_svc_customer_{sel_id}")
                            e_service_type = st.selectbox("Service Type", [
                                "NEW PAN CARD", "CORRECTION PAN CARD", "NEW PASSPORT", "RENEWAL PASSPORT",
                                "DIGITAL SIGNATURE", "VOTER ID", "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
                                "ADDRESS CHANGE IN AADHAR CARD", "DATE OF BIRTH CHANGE IN AADHAR CARD",
                                "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
                            ], index=0, key=f"edit_svc_type_{sel_id}")
                            e_no_apps = st.number_input("No. of Applications", min_value=1, value=int(r["num_apps"]), step=1, key=f"edit_svc_apps_{sel_id}")
                            e_govt = st.number_input("Total Govt Amount (total)", min_value=0.0, value=float(r["govt_amt"]), key=f"edit_svc_govt_{sel_id}")
                            e_paid = st.number_input("Total Paid Amount (total)", min_value=0.0, value=float(r["paid_amt"]), key=f"edit_svc_paid_{sel_id}")
                            e_notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_svc_notes_{sel_id}")
                            save = st.form_submit_button("Save Changes")
                            if save:
                                profit_new = round(float(e_paid) - float(e_govt), 2)
                                df.loc[(df["id"] == sel_id) & (df["user"] == user), ["date","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","notes"]] = [
                                    e_date.strftime("%Y-%m-%d"), e_customer, e_service_type, int(e_no_apps), round(float(e_govt),2), round(float(e_paid),2), profit_new, e_notes
                                ]
                                save_csv(df, FILES["services"])
                                st.success("Service updated ✅")
                                st.rerun()
        with col3:
            if st.button("🗑️ Delete Service", key="svc_del_btn"):
                if sel_id is None:
                    st.error("No ID selected")
                else:
                    rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                    if rec.empty:
                        st.error("Record not found or not yours")
                    else:
                        df = df[df["id"] != sel_id]
                        save_csv(df, FILES["services"])
                        st.success("Service deleted ✅")
                        st.rerun()

        st.download_button("⬇️ Download Services CSV (You)", df_to_csv_bytes(df_user), f"services_{user}.csv", key=f"dl_svc_{user}_csv")
        st.download_button("⬇️ Download Services Excel (You)", df_to_excel_bytes(df_user, "Services"), f"services_{user}.xlsx", key=f"dl_svc_{user}_xlsx")

# -------------------------
# EXPENSES: add / edit / delete
# -------------------------
def expense_entry_page():
    st.header("💰 Expense Entry")
    user = st.session_state.user
    exp_cols = ["id","date","user","category","amount","notes"]
    df = load_csv(FILES["expenses"], exp_cols)

    with st.form("exp_add_form", clear_on_submit=True):
        e_date = st.date_input("Date", value=date.today(), key="exp_date")
        category = st.selectbox("Expense Category", ["Salaries","Office Rent","Power Bill","Water Bill","Stationery","Furniture Repair","Printing Bill","Food","Other"], key="exp_cat")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, key="exp_amount")
        notes = st.text_input("Notes (optional)", key="exp_notes")
        add = st.form_submit_button("➕ Add Expense")
        if add:
            if amount <= 0:
                st.error("Amount must be > 0")
            else:
                nid = next_id(df)
                df = pd.concat([df, pd.DataFrame([{
                    "id": nid,
                    "date": e_date.strftime("%Y-%m-%d"),
                    "user": user,
                    "category": category,
                    "amount": round(float(amount),2),
                    "notes": notes
                }])], ignore_index=True)
                save_csv(df, FILES["expenses"])
                st.success("Expense added ✅")
                st.rerun()

    st.markdown("---")
    st.subheader("Your Expenses")
    df_user = df[df["user"] == user].sort_values("date", ascending=False)
    if df_user.empty:
        st.info("No expenses yet")
    else:
        st.dataframe(df_user, use_container_width=True)
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            try:
                min_id = int(df_user["id"].min())
                max_id = int(df_user["id"].max())
                sel_id = int(st.number_input("Enter Expense ID to Edit/Delete", min_value=min_id, max_value=max_id, step=1, key="exp_sel_id"))
            except Exception:
                sel_id = None
        with col2:
            if st.button("✏️ Edit Expense", key="exp_edit_btn"):
                if sel_id is None:
                    st.error("No ID selected")
                else:
                    rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                    if rec.empty:
                        st.error("Record not found or not yours")
                    else:
                        r = rec.iloc[0]
                        with st.form(f"exp_edit_form_{sel_id}", clear_on_submit=False):
                            d = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_exp_date_{sel_id}")
                            cat = st.selectbox("Category", ["Salaries","Office Rent","Power Bill","Water Bill","Stationery","Furniture Repair","Printing Bill","Food","Other"], key=f"edit_exp_cat_{sel_id}")
                            amt = st.number_input("Amount (₹)", min_value=0.0, value=float(r["amount"]), key=f"edit_exp_amt_{sel_id}")
                            notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_exp_notes_{sel_id}")
                            save = st.form_submit_button("Save Expense")
                            if save:
                                df.loc[(df["id"] == sel_id) & (df["user"] == user), ["date","category","amount","notes"]] = [d.strftime("%Y-%m-%d"), cat, round(float(amt),2), notes]
                                save_csv(df, FILES["expenses"])
                                st.success("Expense updated ✅")
                                st.rerun()
        with col3:
            if st.button("🗑️ Delete Expense", key="exp_del_btn"):
                if sel_id is None:
                    st.error("No ID selected")
                else:
                    rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                    if rec.empty:
                        st.error("Record not found or not yours")
                    else:
                        df = df[df["id"] != sel_id]
                        save_csv(df, FILES["expenses"])
                        st.success("Expense deleted ✅")
                        st.rerun()
        st.download_button("⬇️ Download Expenses CSV (You)", df_to_csv_bytes(df_user), f"expenses_{user}.csv", key=f"dl_exp_{user}_csv")
        st.download_button("⬇️ Download Expenses Excel (You)", df_to_excel_bytes(df_user, "Expenses"), f"expenses_{user}.xlsx", key=f"dl_exp_{user}_xlsx")

# -------------------------
# TRANSACTIONS: add / edit / delete / filter
# -------------------------
def transactions_page():
    st.header("🔄 Agent / Customer Transactions")
    user = st.session_state.user
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    df = load_csv(FILES["transactions"], txn_cols)

    with st.form("txn_add_form", clear_on_submit=True):
        t_date = st.date_input("Date", value=date.today(), key="txn_date")
        party = st.text_input("Customer / Agent", key="txn_party")
        service_type = st.selectbox("Service Type (optional)", ["","NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","NEW AADHAR CARD","OTHER"], key="txn_service")
        status = st.selectbox("Status", ["Paid","Pending","Partial"], key="txn_status")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, key="txn_amount")
        notes = st.text_input("Notes (optional)", key="txn_notes")
        add = st.form_submit_button("➕ Add Transaction")
        if add:
            if not party:
                st.error("Enter Customer/Agent name")
            else:
                nid = next_id(df)
                df = pd.concat([df, pd.DataFrame([{
                    "id": nid,
                    "date": t_date.strftime("%Y-%m-%d"),
                    "user": user,
                    "party": party,
                    "service_type": service_type,
                    "status": status,
                    "amount": round(float(amount),2),
                    "notes": notes
                }])], ignore_index=True)
                save_csv(df, FILES["transactions"])
                st.success("Transaction added ✅")
                st.rerun()

    st.markdown("---")
    st.subheader("Your Transactions")
    df_user = df[df["user"] == user].sort_values("date", ascending=False)
    if df_user.empty:
        st.info("No transactions yet")
    else:
        colA, colB = st.columns([2,1])
        with colA:
            search = st.text_input("Search by Customer/Agent", key="txn_search")
        with colB:
            filter_status = st.selectbox("Filter by Status", ["All","Paid","Pending","Partial"], key="txn_filter")
        df_view = df_user.copy()
        if search:
            df_view = df_view[df_view["party"].str.contains(search, case=False, na=False)]
        if filter_status != "All":
            df_view = df_view[df_view["status"] == filter_status]
        st.dataframe(df_view, use_container_width=True)

        ids = df_view["id"].tolist()
        if ids:
            sel_id = int(st.selectbox("Select Transaction ID to Edit/Delete", ids, key="txn_sel_id"))
        else:
            sel_id = None

        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("✏️ Edit Transaction", key="txn_edit_btn") and sel_id:
                rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    r = rec.iloc[0]
                    with st.form(f"txn_edit_form_{sel_id}", clear_on_submit=False):
                        d = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_txn_date_{sel_id}")
                        party = st.text_input("Customer/Agent", value=r["party"], key=f"edit_txn_party_{sel_id}")
                        service = st.selectbox("Service Type", ["","NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","NEW AADHAR CARD","OTHER"], index=0, key=f"edit_txn_service_{sel_id}")
                        status = st.selectbox("Status", ["Paid","Pending","Partial"], index=["Paid","Pending","Partial"].index(r["status"]) if r["status"] in ["Paid","Pending","Partial"] else 0, key=f"edit_txn_status_{sel_id}")
                        amt = st.number_input("Amount (₹)", min_value=0.0, value=float(r["amount"]), key=f"edit_txn_amt_{sel_id}")
                        notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_txn_notes_{sel_id}")
                        save = st.form_submit_button("Save Transaction")
                        if save:
                            df.loc[(df["id"] == sel_id) & (df["user"] == user), ["date","party","service_type","status","amount","notes"]] = [
                                d.strftime("%Y-%m-%d"), party, service, status, round(float(amt),2), notes
                            ]
                            save_csv(df, FILES["transactions"])
                            st.success("Transaction updated ✅")
                            st.rerun()
        with c2:
            if st.button("🗑️ Delete Transaction", key="txn_del_btn") and sel_id:
                rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    df = df[df["id"] != sel_id]
                    save_csv(df, FILES["transactions"])
                    st.success("Transaction deleted ✅")
                    st.rerun()

        if not df_view.empty:
            st.download_button("⬇️ Download Transactions CSV (view)", df_to_csv_bytes(df_view), f"transactions_view_{user}.csv", key=f"dl_txn_view_{user}_csv")
            st.download_button("⬇️ Download Transactions Excel (view)", df_to_excel_bytes(df_view, "Transactions"), f"transactions_view_{user}.xlsx", key=f"dl_txn_view_{user}_xlsx")

# -------------------------
# SUPPLIERS: add / edit / delete
# -------------------------
def suppliers_page():
    st.header("🏭 Suppliers")
    user = st.session_state.user
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    df = load_csv(FILES["suppliers"], sup_cols)

    with st.form("sup_add_form", clear_on_submit=True):
        s_date = st.date_input("Date", value=date.today(), key="sup_date")
        s_name = st.text_input("Supplier Name", key="sup_name")
        s_service = st.text_input("Service Type", key="sup_service")
        s_paid = st.number_input("Paid Amount (₹)", min_value=0.0, value=0.0, key="sup_paid")
        s_pending = st.number_input("Pending Amount (₹)", min_value=0.0, value=0.0, key="sup_pending")
        s_partial = st.number_input("Partial Amount (₹)", min_value=0.0, value=0.0, key="sup_partial")
        s_notes = st.text_input("Notes", key="sup_notes")
        add = st.form_submit_button("➕ Add Supplier")
        if add:
            if not s_name:
                st.error("Enter supplier name")
            else:
                nid = next_id(df)
                df = pd.concat([df, pd.DataFrame([{
                    "id": nid,
                    "date": s_date.strftime("%Y-%m-%d"),
                    "user": user,
                    "supplier_name": s_name,
                    "service_type": s_service,
                    "paid_amt": round(float(s_paid),2),
                    "pending_amt": round(float(s_pending),2),
                    "partial_amt": round(float(s_partial),2),
                    "notes": s_notes
                }])], ignore_index=True)
                save_csv(df, FILES["suppliers"])
                st.success("Supplier added ✅")
                st.rerun()

    st.markdown("---")
    st.subheader("Your Suppliers")
    df_user = df[df["user"] == user].sort_values("date", ascending=False)
    if df_user.empty:
        st.info("No suppliers yet")
    else:
        st.dataframe(df_user, use_container_width=True)
        col1, col2 = st.columns([2,1])
        with col1:
            try:
                min_id = int(df_user["id"].min())
                max_id = int(df_user["id"].max())
                sel_id = int(st.number_input("Select Supplier ID to Edit/Delete", min_value=min_id, max_value=max_id, step=1, key="sup_sel_id"))
            except Exception:
                sel_id = None
        with col2:
            if st.button("✏️ Edit Supplier", key="sup_edit_btn"):
                if sel_id is None:
                    st.error("No ID selected")
                else:
                    rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                    if rec.empty:
                        st.error("Record not found or not yours")
                    else:
                        r = rec.iloc[0]
                        with st.form(f"sup_edit_form_{sel_id}", clear_on_submit=False):
                            d = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_sup_date_{sel_id}")
                            name = st.text_input("Supplier Name", value=r["supplier_name"], key=f"edit_sup_name_{sel_id}")
                            service = st.text_input("Service Type", value=r["service_type"], key=f"edit_sup_service_{sel_id}")
                            paid = st.number_input("Paid Amount (₹)", min_value=0.0, value=float(r["paid_amt"]), key=f"edit_sup_paid_{sel_id}")
                            pending = st.number_input("Pending Amount (₹)", min_value=0.0, value=float(r["pending_amt"]), key=f"edit_sup_pending_{sel_id}")
                            partial = st.number_input("Partial Amount (₹)", min_value=0.0, value=float(r["partial_amt"]), key=f"edit_sup_partial_{sel_id}")
                            notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_sup_notes_{sel_id}")
                            save = st.form_submit_button("Save Supplier")
                            if save:
                                df.loc[(df["id"] == sel_id) & (df["user"] == user), ["date","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]] = [
                                    d.strftime("%Y-%m-%d"), name, service, round(float(paid),2), round(float(pending),2), round(float(partial),2), notes
                                ]
                                save_csv(df, FILES["suppliers"])
                                st.success("Supplier updated ✅")
                                st.rerun()
            if st.button("🗑️ Delete Supplier", key="sup_del_btn"):
                if sel_id is None:
                    st.error("No ID selected")
                else:
                    rec = df[(df["id"] == sel_id) & (df["user"] == user)]
                    if rec.empty:
                        st.error("Not found or not yours")
                    else:
                        df = df[df["id"] != sel_id]
                        save_csv(df, FILES["suppliers"])
                        st.success("Supplier deleted ✅")
                        st.rerun()
        st.download_button("⬇️ Download Suppliers CSV (You)", df_to_csv_bytes(df_user), f"suppliers_{user}.csv", key=f"dl_sup_{user}_csv")
        st.download_button("⬇️ Download Suppliers Excel (You)", df_to_excel_bytes(df_user, "Suppliers"), f"suppliers_{user}.xlsx", key=f"dl_sup_{user}_xlsx")

# -------------------------
# DAILY DATA LOGGER
# -------------------------
def daily_data_logger_page():
    st.header("📅 Daily Data Logger (service-wise totals)")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","notes"]
    df = load_csv(FILES["services"], svc_cols)
    df_user = df[df["user"] == user].copy()
    if df_user.empty:
        st.info("No services recorded")
        return
    sel_date = st.date_input("Pick a date", value=date.today(), key="logger_date")
    date_str = sel_date.strftime("%Y-%m-%d")
    df_day = df_user[df_user["date"] == date_str]
    if df_day.empty:
        st.info("No services on selected date")
        return
    grouped = df_day.groupby("service_type").agg({
        "num_apps":"sum","govt_amt":"sum","paid_amt":"sum","profit_amt":"sum"
    }).reset_index().rename(columns={
        "service_type":"Service Type","num_apps":"No. of Apps","govt_amt":"Total Govt","paid_amt":"Total Paid","profit_amt":"Total Profit"
    })
    st.subheader(f"Service-wise totals for {date_str}")
    st.dataframe(grouped, use_container_width=True)
    totals = grouped[["No. of Apps","Total Govt","Total Paid","Total Profit"]].sum().to_dict()
    st.write("Totals:")
    st.json({k: float(v) for k,v in totals.items()})
    st.download_button("⬇️ Download Daily Summary CSV", df_to_csv_bytes(grouped), f"daily_summary_{date_str}_{user}.csv", key=f"dl_daily_{user}_csv")
    st.download_button("⬇️ Download Daily Summary Excel", df_to_excel_bytes(grouped, "DailySummary"), f"daily_summary_{date_str}_{user}.xlsx", key=f"dl_daily_{user}_xlsx")

# -------------------------
# REPORTS (period filters, charts, export)
# -------------------------
def reports_page():
    st.header("📊 Reports & Profit/Loss")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    df_svc = load_csv(FILES["services"], svc_cols)
    df_exp = load_csv(FILES["expenses"], exp_cols)
    df_svc = df_svc[df_svc["user"] == user]
    df_exp = df_exp[df_exp["user"] == user]

    if df_svc.empty and df_exp.empty:
        st.info("No data to report")
        return

    period = st.selectbox("Select Period", ["Daily","Weekly","Monthly","Custom","All"], key="reports_period")
    today = date.today()
    if period == "Daily":
        start = today; end = today
    elif period == "Weekly":
        start = today - timedelta(days=7); end = today
    elif period == "Monthly":
        start = today - timedelta(days=30); end = today
    elif period == "Custom":
        start = st.date_input("Start Date", value=today - timedelta(days=30), key="rep_custom_start")
        end = st.date_input("End Date", value=today, key="rep_custom_end")
    else:
        start = None; end = None

    def filter_range(df, start_date, end_date, col="date"):
        if df.empty or start_date is None:
            return df
        df2 = df.copy()
        df2[col] = pd.to_datetime(df2[col])
        mask = (df2[col] >= pd.to_datetime(start_date)) & (df2[col] <= pd.to_datetime(end_date))
        return df2[mask]

    svc_f = filter_range(df_svc, start, end)
    exp_f = filter_range(df_exp, start, end)

    agent_filter = st.text_input("Filter by Customer/Agent (optional)", key="rep_agent_filter")
    if agent_filter and not svc_f.empty:
        svc_f = svc_f[svc_f["customer"].str.contains(agent_filter, case=False, na=False)]

    total_govt = float(svc_f["govt_amt"].sum()) if not svc_f.empty else 0.0
    total_paid = float(svc_f["paid_amt"].sum()) if not svc_f.empty else 0.0
    total_profit = float(svc_f["profit_amt"].sum()) if not svc_f.empty else 0.0
    total_expenses = float(exp_f["amount"].sum()) if not exp_f.empty else 0.0
    net_profit = total_profit - total_expenses

    st.metric("Total Govt Amount (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid (₹)", f"{total_paid:,.2f}")
    st.metric("Service Profit (₹)", f"{total_profit:,.2f}")
    st.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    st.metric("Net Profit / Loss (₹)", f"{net_profit:,.2f}")

    st.subheader("Service Details")
    st.dataframe(svc_f, use_container_width=True)
    st.subheader("Expense Details")
    st.dataframe(exp_f, use_container_width=True)

    if not svc_f.empty:
        grp = svc_f.groupby("service_type").agg({"num_apps":"sum","govt_amt":"sum","paid_amt":"sum","profit_amt":"sum"}).reset_index()
        st.subheader("Service-wise Profit")
        st.bar_chart(grp.set_index("service_type")["profit_amt"])

    if not svc_f.empty or not exp_f.empty:
        if not svc_f.empty:
            tmp_s = svc_f.copy()
            tmp_s["Month"] = pd.to_datetime(tmp_s["date"]).dt.to_period("M").astype(str)
            monthly_profit = tmp_s.groupby("Month")["profit_amt"].sum().reset_index()
        else:
            monthly_profit = pd.DataFrame(columns=["Month","profit_amt"])
        if not exp_f.empty:
            tmp_e = exp_f.copy()
            tmp_e["Month"] = pd.to_datetime(tmp_e["date"]).dt.to_period("M").astype(str)
            monthly_exp = tmp_e.groupby("Month")["amount"].sum().reset_index()
        else:
            monthly_exp = pd.DataFrame(columns=["Month","amount"])
        merged = pd.merge(monthly_profit, monthly_exp, on="Month", how="outer").fillna(0).sort_values("Month")
        if not merged.empty:
            merged = merged.rename(columns={"profit_amt":"Profit","amount":"Expenses"})
            st.subheader("Monthly Profit vs Expenses")
            st.line_chart(merged.set_index("Month")[["Profit","Expenses"]])

    if not svc_f.empty:
        st.download_button("⬇️ Download Services Report CSV", df_to_csv_bytes(svc_f), f"services_report_{user}.csv", key=f"dl_rep_svc_{user}_csv")
        st.download_button("⬇️ Download Services Report Excel", df_to_excel_bytes(svc_f, "ServicesReport"), f"services_report_{user}.xlsx", key=f"dl_rep_svc_{user}_xlsx")
    if not exp_f.empty:
        st.download_button("⬇️ Download Expenses Report CSV", df_to_csv_bytes(exp_f), f"expenses_report_{user}.csv", key=f"dl_rep_exp_{user}_csv")
        st.download_button("⬇️ Download Expenses Report Excel", df_to_excel_bytes(exp_f, "ExpensesReport"), f"expenses_report_{user}.xlsx", key=f"dl_rep_exp_{user}_xlsx")

# -------------------------
# BALANCES
# -------------------------
def balances_page():
    st.header("💼 Balances / Summary")
    user = st.session_state.user
    df_svc = load_csv(FILES["services"], ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","notes"])
    df_exp = load_csv(FILES["expenses"], ["id","date","user","category","amount","notes"])
    df_svc = df_svc[df_svc["user"] == user]
    df_exp = df_exp[df_exp["user"] == user]
    total_govt = float(df_svc["govt_amt"].sum()) if not df_svc.empty else 0.0
    total_paid = float(df_svc["paid_amt"].sum()) if not df_svc.empty else 0.0
    total_profit = float(df_svc["profit_amt"].sum()) if not df_svc.empty else 0.0
    total_expenses = float(df_exp["amount"].sum()) if not df_exp.empty else 0.0
    cash_in_hand = total_paid - total_expenses
    st.metric("Total Govt Amount (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid by Customers (₹)", f"{total_paid:,.2f}")
    st.metric("Total Service Profit (₹)", f"{total_profit:,.2f}")
    st.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    st.metric("Cash in Hand (simplified) (₹)", f"{cash_in_hand:,.2f}")

# -------------------------
# Main app navigation
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
        return

    page = st.sidebar.radio("Menu", [
        "Service Entry",
        "Expense Entry",
        "Transactions",
        "Suppliers",
        "Daily Data Logger",
        "Reports",
        "Balances"
    ], index=0)

    try:
        if page == "Service Entry":
            service_entry_page()
        elif page == "Expense Entry":
            expense_entry_page()
        elif page == "Transactions":
            transactions_page()
        elif page == "Suppliers":
            suppliers_page()
        elif page == "Daily Data Logger":
            daily_data_logger_page()
        elif page == "Reports":
            reports_page()
        elif page == "Balances":
            balances_page()
    except Exception as e:
        st.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
