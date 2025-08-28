# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta
from io import BytesIO

DB_PATH = "data.db"

# --------------------------
# Database helpers
# --------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # users: id, username, password, role, device
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        device TEXT
    );
    """)
    # services
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        customer TEXT,
        service_type TEXT,
        num_apps INTEGER,
        govt_amt REAL,
        paid_amt REAL,
        profit_amt REAL,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    # expenses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        category TEXT,
        amount REAL,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    # transactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        party TEXT,
        service_type TEXT,
        status TEXT,
        amount REAL,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    # suppliers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        supplier_name TEXT,
        service_type TEXT,
        paid_amt REAL,
        pending_amt REAL,
        partial_amt REAL,
        notes TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    conn.commit()
    conn.close()
    seed_users_if_needed()

def seed_users_if_needed():
    # creates the four predefined users if they do not exist
    conn = get_conn()
    cur = conn.cursor()
    predefined = [
        ("user1","pass1","desktop","desktop"),
        ("user2","pass2","desktop","desktop"),
        ("user3","pass3","desktop","desktop"),
        ("mobile","pass4","mobile","android"),
    ]
    for username, password, role, device in predefined:
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO users (username,password,role,device) VALUES (?,?,?,?)",
                        (username, password, role, device))
    conn.commit()
    conn.close()

# --------------------------
# Small utils: read / write
# --------------------------
def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute_sql(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    lastrow = cur.lastrowid
    conn.close()
    return lastrow

# --------------------------
# CSV / Excel export helpers
# --------------------------
def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel_bytes(df, sheet_name="Sheet1"):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return out.getvalue()

# --------------------------
# Session init
# --------------------------
if "initialized" not in st.session_state:
    init_db()
    st.session_state.initialized = True

if "user" not in st.session_state:
    st.session_state.user = None  # will be dict with id,username,role,device

# --------------------------
# Authentication UI
# --------------------------
def login_ui():
    st.title("🔐 NANI ASSOCIATES - Login")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")
        if submitted:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id,username,role,device FROM users WHERE username=? AND password=?", (username, password))
            row = cur.fetchone()
            conn.close()
            if row:
                st.session_state.user = {"id": row[0], "username": row[1], "role": row[2], "device": row[3]}
                st.success(f"Logged in as {row[1]}")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

def logout():
    st.session_state.user = None
    st.success("Logged out")
    st.experimental_rerun()

# --------------------------
# SERVICES CRUD
# --------------------------
def add_service(user_id, date_s, customer, service_type, num_apps, govt_amt_per, paid_amt_per, notes):
    total_govt = float(govt_amt_per) * int(num_apps)
    total_paid = float(paid_amt_per) * int(num_apps)
    profit = total_paid - total_govt
    execute_sql("""
        INSERT INTO services (user_id,date,customer,service_type,num_apps,govt_amt,paid_amt,profit_amt,notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (user_id, date_s, customer, service_type, int(num_apps), round(total_govt,2), round(total_paid,2), round(profit,2), notes))

def update_service(row_id, date_s, customer, service_type, num_apps, total_govt, total_paid, notes):
    profit = float(total_paid) - float(total_govt)
    execute_sql("""
        UPDATE services
        SET date=?, customer=?, service_type=?, num_apps=?, govt_amt=?, paid_amt=?, profit_amt=?, notes=?
        WHERE id=?
    """, (date_s, customer, service_type, int(num_apps), round(float(total_govt),2), round(float(total_paid),2), round(profit,2), notes, int(row_id)))

def delete_service(row_id):
    execute_sql("DELETE FROM services WHERE id=?", (int(row_id),))

# --------------------------
# EXPENSES CRUD
# --------------------------
def add_expense(user_id, date_s, category, amount, notes):
    execute_sql("""
        INSERT INTO expenses (user_id,date,category,amount,notes)
        VALUES (?,?,?,?,?)
    """, (user_id, date_s, category, round(float(amount),2), notes))

def update_expense(row_id, date_s, category, amount, notes):
    execute_sql("""
        UPDATE expenses SET date=?, category=?, amount=?, notes=? WHERE id=?
    """, (date_s, category, round(float(amount),2), notes, int(row_id)))

def delete_expense(row_id):
    execute_sql("DELETE FROM expenses WHERE id=?", (int(row_id),))

# --------------------------
# TRANSACTIONS CRUD
# --------------------------
def add_transaction(user_id, date_s, party, service_type, status, amount, notes):
    execute_sql("""
        INSERT INTO transactions (user_id,date,party,service_type,status,amount,notes)
        VALUES (?,?,?,?,?,?,?)
    """, (user_id, date_s, party, service_type, status, round(float(amount),2), notes))

def update_transaction(row_id, date_s, party, service_type, status, amount, notes):
    execute_sql("""
        UPDATE transactions SET date=?, party=?, service_type=?, status=?, amount=?, notes=? WHERE id=?
    """, (date_s, party, service_type, status, round(float(amount),2), notes, int(row_id)))

def delete_transaction(row_id):
    execute_sql("DELETE FROM transactions WHERE id=?", (int(row_id),))

# --------------------------
# SUPPLIERS CRUD
# --------------------------
def add_supplier(user_id, date_s, supplier_name, service_type, paid_amt, pending_amt, partial_amt, notes):
    execute_sql("""
        INSERT INTO suppliers (user_id,date,supplier_name,service_type,paid_amt,pending_amt,partial_amt,notes)
        VALUES (?,?,?,?,?,?,?,?)
    """, (user_id, date_s, supplier_name, service_type, round(float(paid_amt),2), round(float(pending_amt),2), round(float(partial_amt),2), notes))

def update_supplier(row_id, date_s, supplier_name, service_type, paid_amt, pending_amt, partial_amt, notes):
    execute_sql("""
        UPDATE suppliers SET date=?, supplier_name=?, service_type=?, paid_amt=?, pending_amt=?, partial_amt=?, notes=? WHERE id=?
    """, (date_s, supplier_name, service_type, round(float(paid_amt),2), round(float(pending_amt),2), round(float(partial_amt),2), notes, int(row_id)))

def delete_supplier(row_id):
    execute_sql("DELETE FROM suppliers WHERE id=?", (int(row_id),))

# --------------------------
# UI Pages
# --------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user_id = st.session_state.user["id"]
    cols = st.columns(2)
    with cols[0]:
        entry_date = st.date_input("Date", value=date.today(), key="svc_date")
        customer = st.text_input("Customer / Agent", key="svc_customer")
        service_type = st.selectbox("Service Type", [
            "NEW PAN CARD", "CORRECTION PAN CARD",
            "NEW PASSPORT", "RENEWAL PASSPORT",
            "DIGITAL SIGNATURE", "VOTER ID",
            "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
            "ADDRESS CHANGE IN AADHAR CARD", "DOB CHANGE IN AADHAR CARD",
            "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
        ], key="svc_type")
    with cols[1]:
        num_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1, key="svc_num_apps")
        govt_amt_per = st.number_input("Government Amount (per app)", min_value=0.0, value=0.0, key="svc_govt_per")
        paid_amt_per = st.number_input("Paid Amount (per app)", min_value=0.0, value=0.0, key="svc_paid_per")
        notes = st.text_input("Notes (optional)", key="svc_notes")

    total_govt = govt_amt_per * num_apps
    total_paid = paid_amt_per * num_apps
    profit = total_paid - total_govt
    st.metric("Total Govt (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid (₹)", f"{total_paid:,.2f}")
    st.metric("Profit (₹)", f"{profit:,.2f}")

    if st.button("➕ Add Service", key="add_service_btn"):
        if not customer:
            st.error("Please enter Customer/Agent name")
        else:
            add_service(user_id, entry_date.strftime("%Y-%m-%d"), customer, service_type, num_apps, govt_amt_per, paid_amt_per, notes)
            st.success("Service added")
            st.experimental_rerun()

    st.markdown("---")
    # Show user's services
    df = query_df("SELECT id,date,customer,service_type,num_apps,govt_amt,paid_amt,profit_amt,notes FROM services WHERE user_id=? ORDER BY date DESC", (user_id,))
    st.subheader("Your Services")
    if df.empty:
        st.info("No services yet")
    else:
        st.dataframe(df, use_container_width=True)

        # Edit / Delete controls
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            sel_id = int(st.number_input("Enter Service ID to Edit/Delete", min_value=int(df['id'].min()), max_value=int(df['id'].max()), step=1, key="svc_sel_id"))
        with col2:
            if st.button("✏️ Edit Service", key="svc_edit_btn"):
                record = query_df("SELECT * FROM services WHERE id=? AND user_id=?", (sel_id, user_id))
                if record.empty:
                    st.error("Record not found or not yours")
                else:
                    r = record.iloc[0]
                    with st.form(f"svc_edit_form_{sel_id}", clear_on_submit=False):
                        e_date = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_svc_date_{sel_id}")
                        e_customer = st.text_input("Customer/Agent", value=r["customer"], key=f"edit_svc_customer_{sel_id}")
                        e_service_type = st.selectbox("Service Type", [
                            "NEW PAN CARD", "CORRECTION PAN CARD",
                            "NEW PASSPORT", "RENEWAL PASSPORT",
                            "DIGITAL SIGNATURE", "VOTER ID",
                            "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
                            "ADDRESS CHANGE IN AADHAR CARD", "DOB CHANGE IN AADHAR CARD",
                            "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
                        ], index=0, key=f"edit_svc_type_{sel_id}")
                        e_num_apps = st.number_input("No. of Applications", min_value=1, value=int(r["num_apps"]), key=f"edit_svc_apps_{sel_id}")
                        e_govt = st.number_input("Total Govt Amount (total)", min_value=0.0, value=float(r["govt_amt"]), key=f"edit_svc_govt_{sel_id}")
                        e_paid = st.number_input("Total Paid Amount (total)", min_value=0.0, value=float(r["paid_amt"]), key=f"edit_svc_paid_{sel_id}")
                        e_notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_svc_notes_{sel_id}")
                        save = st.form_submit_button("Save Changes")
                        if save:
                            update_service(sel_id, e_date.strftime("%Y-%m-%d"), e_customer, e_service_type, e_num_apps, e_govt, e_paid, e_notes)
                            st.success("Service updated")
                            st.rerun()
        with col3:
            if st.button("🗑️ Delete Service", key="svc_del_btn"):
                # double-check ownership
                record = query_df("SELECT id FROM services WHERE id=? AND user_id=?", (sel_id,user_id))
                if record.empty:
                    st.error("Record not found or not yours")
                else:
                    delete_service(sel_id)
                    st.success("Service deleted")
                    st.rerun()

        # export
        csv_bytes = df_to_csv_bytes(df)
        excel_bytes = df_to_excel_bytes(df, "Services")
        st.download_button("⬇️ Download Services CSV", csv_bytes, "services.csv", key="dl_svc_csv")
        st.download_button("⬇️ Download Services Excel", excel_bytes, "services.xlsx", key="dl_svc_xlsx")

def expense_entry_page():
    st.header("💸 Expense Entry")
    user_id = st.session_state.user["id"]
    with st.form("expense_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today(), key="exp_date")
        category = st.selectbox("Expense Category", ["Salaries","Office Rent","Power Bill","Water Bill","Stationery","Furniture Repair","Printing Bill","Food","Other"], key="exp_cat")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, key="exp_amount")
        notes = st.text_input("Notes (optional)", key="exp_notes")
        submit = st.form_submit_button("Add Expense")
        if submit:
            if amount <= 0:
                st.error("Amount must be greater than 0")
            else:
                add_expense(user_id, entry_date.strftime("%Y-%m-%d"), category, amount, notes)
                st.success("Expense added")
                st.experimental_rerun()

    df = query_df("SELECT id,date,category,amount,notes FROM expenses WHERE user_id=? ORDER BY date DESC", (user_id,))
    st.subheader("Your Expenses")
    if df.empty:
        st.info("No expenses yet")
    else:
        st.dataframe(df, use_container_width=True)
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            sel_id = int(st.number_input("Enter Expense ID to Edit/Delete", min_value=int(df['id'].min()), max_value=int(df['id'].max()), step=1, key="exp_sel_id"))
        with col2:
            if st.button("✏️ Edit Expense", key="exp_edit_btn"):
                rec = query_df("SELECT * FROM expenses WHERE id=? AND user_id=?", (sel_id, user_id))
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    r = rec.iloc[0]
                    with st.form(f"exp_edit_form_{sel_id}", clear_on_submit=False):
                        d = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_exp_date_{sel_id}")
                        cat = st.selectbox("Category", ["Salaries","Office Rent","Power Bill","Water Bill","Stationery","Furniture Repair","Printing Bill","Food","Other"], key=f"edit_exp_cat_{sel_id}")
                        amt = st.number_input("Amount", min_value=0.0, value=float(r["amount"]), key=f"edit_exp_amt_{sel_id}")
                        notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_exp_notes_{sel_id}")
                        save = st.form_submit_button("Save")
                        if save:
                            update_expense(sel_id, d.strftime("%Y-%m-%d"), cat, amt, notes)
                            st.success("Expense updated")
                            st.rerun()
        with col3:
            if st.button("🗑️ Delete Expense", key="exp_del_btn"):
                rec = query_df("SELECT id FROM expenses WHERE id=? AND user_id=?", (sel_id,user_id))
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    delete_expense(sel_id)
                    st.success("Expense deleted")
                    st.rerun()

        st.download_button("⬇️ Download Expenses CSV", df_to_csv_bytes(df), "expenses.csv", key="dl_exp_csv")
        st.download_button("⬇️ Download Expenses Excel", df_to_excel_bytes(df, "Expenses"), "expenses.xlsx", key="dl_exp_xlsx")

def transactions_page():
    st.header("🔄 Agent/Customer Transactions")
    user_id = st.session_state.user["id"]
    with st.form("txn_form", clear_on_submit=True):
        txn_date = st.date_input("Date", value=date.today(), key="txn_date")
        party = st.text_input("Customer / Agent Name", key="txn_party")
        service_type = st.selectbox("Service Type (optional)", ["","NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","NEW AADHAR CARD","OTHER"], key="txn_service")
        status = st.selectbox("Status", ["Paid","Pending","Partial"], key="txn_status")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, key="txn_amount")
        notes = st.text_input("Notes (optional)", key="txn_notes")
        add = st.form_submit_button("Add Transaction")
        if add:
            if not party:
                st.error("Enter Customer/Agent")
            else:
                add_transaction(user_id, txn_date.strftime("%Y-%m-%d"), party, service_type, status, amount, notes)
                st.success("Transaction added")
                st.rerun()

    df = query_df("SELECT id,date,party,service_type,status,amount,notes FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,))
    st.subheader("Your Transactions")
    if df.empty:
        st.info("No transactions yet")
    else:
        # filters
        col1, col2 = st.columns([2,1])
        with col1:
            search_name = st.text_input("Search by Customer/Agent", key="txn_search")
        with col2:
            filter_status = st.selectbox("Filter by Status", ["All","Paid","Pending","Partial"], key="txn_filter")
        df_view = df.copy()
        if search_name:
            df_view = df_view[df_view["party"].str.contains(search_name, case=False, na=False)]
        if filter_status != "All":
            df_view = df_view[df_view["status"] == filter_status]
        st.dataframe(df_view, use_container_width=True)

        # Select index to edit/delete
        colA, colB, colC = st.columns([2,1,1])
        with colA:
            # use index of displayed df
            if not df_view.empty:
                idx_list = df_view["id"].tolist()
                sel_index = st.selectbox("Select Transaction ID for Edit/Delete", idx_list, key="txn_sel_id")
            else:
                sel_index = None
        with colB:
            if st.button("✏️ Edit Transaction", key="txn_edit_btn") and sel_index:
                rec = query_df("SELECT * FROM transactions WHERE id=? AND user_id=?", (sel_index,user_id))
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    r = rec.iloc[0]
                    with st.form(f"txn_edit_form_{sel_index}", clear_on_submit=False):
                        d = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_txn_date_{sel_index}")
                        party = st.text_input("Customer/Agent", value=r["party"], key=f"edit_txn_party_{sel_index}")
                        service = st.selectbox("Service Type", ["","NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","NEW AADHAR CARD","OTHER"], index=0, key=f"edit_txn_service_{sel_index}")
                        status = st.selectbox("Status", ["Paid","Pending","Partial"], index=["Paid","Pending","Partial"].index(r["status"]) if r["status"] in ["Paid","Pending","Partial"] else 0, key=f"edit_txn_status_{sel_index}")
                        amt = st.number_input("Amount", min_value=0.0, value=float(r["amount"]), key=f"edit_txn_amt_{sel_index}")
                        notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_txn_notes_{sel_index}")
                        save = st.form_submit_button("Save Transaction")
                        if save:
                            update_transaction(sel_index, d.strftime("%Y-%m-%d"), party, service, status, amt, notes)
                            st.success("Transaction updated")
                            st.rerun()
        with colC:
            if st.button("🗑️ Delete Transaction", key="txn_del_btn") and sel_index:
                rec = query_df("SELECT id FROM transactions WHERE id=? AND user_id=?", (sel_index,user_id))
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    delete_transaction(sel_index)
                    st.success("Transaction deleted")
                    st.rerun()

        # export shown df
        if not df_view.empty:
            st.download_button("⬇️ Download Transactions CSV (view)", df_to_csv_bytes(df_view), "transactions_view.csv", key="dl_txn_view_csv")
            st.download_button("⬇️ Download Transactions Excel (view)", df_to_excel_bytes(df_view, "Transactions"), "transactions_view.xlsx", key="dl_txn_view_xlsx")

def suppliers_page():
    st.header("🏢 Suppliers")
    user_id = st.session_state.user["id"]
    with st.form("sup_form", clear_on_submit=True):
        s_date = st.date_input("Date", value=date.today(), key="sup_date")
        s_name = st.text_input("Supplier Name", key="sup_name")
        s_service = st.text_input("Service Type", key="sup_service")
        s_paid = st.number_input("Paid Amount (₹)", min_value=0.0, value=0.0, key="sup_paid")
        s_pending = st.number_input("Pending Amount (₹)", min_value=0.0, value=0.0, key="sup_pending")
        s_partial = st.number_input("Partial Amount (₹)", min_value=0.0, value=0.0, key="sup_partial")
        s_notes = st.text_input("Notes", key="sup_notes")
        add = st.form_submit_button("Add Supplier")
        if add:
            if not s_name:
                st.error("Enter supplier name")
            else:
                add_supplier(user_id, s_date.strftime("%Y-%m-%d"), s_name, s_service, s_paid, s_pending, s_partial, s_notes)
                st.success("Supplier added")
                st.rerun()

    df = query_df("SELECT id,date,supplier_name,service_type,paid_amt,pending_amt,partial_amt,notes FROM suppliers WHERE user_id=? ORDER BY date DESC", (user_id,))
    st.subheader("Your Suppliers")
    if df.empty:
        st.info("No suppliers yet")
    else:
        st.dataframe(df, use_container_width=True)
        col1, col2 = st.columns([2,1])
        with col1:
            sel_id = int(st.number_input("Select Supplier ID to Edit/Delete", min_value=int(df['id'].min()), max_value=int(df['id'].max()), step=1, key="sup_sel_id"))
        with col2:
            if st.button("✏️ Edit Supplier", key="sup_edit_btn"):
                rec = query_df("SELECT * FROM suppliers WHERE id=? AND user_id=?", (sel_id,user_id))
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    r = rec.iloc[0]
                    with st.form(f"sup_edit_form_{sel_id}", clear_on_submit=False):
                        d = st.date_input("Date", value=pd.to_datetime(r["date"]).date(), key=f"edit_sup_date_{sel_id}")
                        name = st.text_input("Supplier Name", value=r["supplier_name"], key=f"edit_sup_name_{sel_id}")
                        service = st.text_input("Service Type", value=r["service_type"], key=f"edit_sup_service_{sel_id}")
                        paid = st.number_input("Paid Amount", min_value=0.0, value=float(r["paid_amt"]), key=f"edit_sup_paid_{sel_id}")
                        pending = st.number_input("Pending Amount", min_value=0.0, value=float(r["pending_amt"]), key=f"edit_sup_pending_{sel_id}")
                        partial = st.number_input("Partial Amount", min_value=0.0, value=float(r["partial_amt"]), key=f"edit_sup_partial_{sel_id}")
                        notes = st.text_input("Notes", value=r["notes"] or "", key=f"edit_sup_notes_{sel_id}")
                        save = st.form_submit_button("Save Supplier")
                        if save:
                            update_supplier(sel_id, d.strftime("%Y-%m-%d"), name, service, paid, pending, partial, notes)
                            st.success("Supplier updated")
                            st.rerun()
            if st.button("🗑️ Delete Supplier", key="sup_del_btn"):
                rec = query_df("SELECT id FROM suppliers WHERE id=? AND user_id=?", (sel_id,user_id))
                if rec.empty:
                    st.error("Not found or not yours")
                else:
                    delete_supplier(sel_id)
                    st.success("Supplier deleted")
                    st.rerun()

        st.download_button("⬇️ Download Suppliers CSV", df_to_csv_bytes(df), "suppliers.csv", key="dl_sup_csv")
        st.download_button("⬇️ Download Suppliers Excel", df_to_excel_bytes(df, "Suppliers"), "suppliers.xlsx", key="dl_sup_xlsx")

def daily_data_logger_page():
    st.header("📅 Daily Data Logger - Service-wise summary")
    user_id = st.session_state.user["id"]
    df = query_df("SELECT date, service_type, num_apps, govt_amt, paid_amt, profit_amt FROM services WHERE user_id=?", (user_id,))
    if df.empty:
        st.info("No services recorded yet")
        return
    sel_date = st.date_input("Select Date", value=date.today(), key="logger_select_date")
    date_str = sel_date.strftime("%Y-%m-%d")
    df_day = df[df["date"] == date_str]
    if df_day.empty:
        st.info("No services on selected date")
        return
    grouped = df_day.groupby("service_type").agg({
        "num_apps":"sum","govt_amt":"sum","paid_amt":"sum","profit_amt":"sum"
    }).reset_index().rename(columns={
        "service_type":"Service Type","num_apps":"No. of Apps",
        "govt_amt":"Total Govt","paid_amt":"Total Paid","profit_amt":"Total Profit"
    })
    st.subheader(f"Service-wise totals for {date_str}")
    st.dataframe(grouped, use_container_width=True)
    totals = grouped[["No. of Apps","Total Govt","Total Paid","Total Profit"]].sum().to_dict()
    st.write("Totals:")
    st.json({k: float(v) for k,v in totals.items()})
    st.download_button("⬇️ Download Daily Summary CSV", df_to_csv_bytes(grouped), f"daily_summary_{date_str}.csv", key="dl_daily_csv")
    st.download_button("⬇️ Download Daily Summary Excel", df_to_excel_bytes(grouped, "DailySummary"), f"daily_summary_{date_str}.xlsx", key="dl_daily_xlsx")

def reports_page():
    st.header("📊 Reports")
    user_id = st.session_state.user["id"]
    df_services = query_df("SELECT date,customer,service_type,num_apps,govt_amt,paid_amt,profit_amt,notes FROM services WHERE user_id=?", (user_id,))
    df_expenses = query_df("SELECT date,category,amount,notes FROM expenses WHERE user_id=?", (user_id,))

    if df_services.empty and df_expenses.empty:
        st.info("No data to show")
        return

    choice = st.selectbox("Period", ["Daily","Weekly","Monthly","Custom","All"], key="rep_period")
    today = date.today()
    if choice == "Daily":
        start = today
        end = today
    elif choice == "Weekly":
        start = today - timedelta(days=7)
        end = today
    elif choice == "Monthly":
        start = today - timedelta(days=30)
        end = today
    elif choice == "Custom":
        start = st.date_input("Start Date", value=today - timedelta(days=30), key="rep_start")
        end = st.date_input("End Date", value=today, key="rep_end")
    else:
        start = None
        end = None

    def apply_range(df, col="date"):
        if df.empty or start is None:
            return df
        df2 = df.copy()
        df2[col] = pd.to_datetime(df2[col])
        return df2[(df2[col] >= pd.to_datetime(start)) & (df2[col] <= pd.to_datetime(end))]

    svc_f = apply_range(df_services)
    exp_f = apply_range(df_expenses)

    # optional filter by agent/customer
    agent_filter = st.text_input("Filter by Agent/Customer (optional)", key="rep_agent_filter")
    if agent_filter and not svc_f.empty:
        svc_f = svc_f[svc_f["customer"].str.contains(agent_filter, case=False, na=False)]

    total_govt = float(svc_f["govt_amt"].sum()) if not svc_f.empty else 0.0
    total_paid = float(svc_f["paid_amt"].sum()) if not svc_f.empty else 0.0
    total_profit = float(svc_f["profit_amt"].sum()) if not svc_f.empty else 0.0
    total_expenses = float(exp_f["amount"].sum()) if not exp_f.empty else 0.0
    net_profit = total_profit - total_expenses

    st.metric("Total Govt Amount (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid by Customers (₹)", f"{total_paid:,.2f}")
    st.metric("Service Profit (₹)", f"{total_profit:,.2f}")
    st.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    st.metric("Net Profit / Loss (₹)", f"{net_profit:,.2f}")

    st.subheader("Service Records")
    st.dataframe(svc_f, use_container_width=True)
    st.subheader("Expense Records")
    st.dataframe(exp_f, use_container_width=True)

    # charts
    if not svc_f.empty:
        grp = svc_f.groupby("service_type").agg({"num_apps":"sum","govt_amt":"sum","paid_amt":"sum","profit_amt":"sum"}).reset_index()
        st.subheader("Service-wise Profit")
        st.bar_chart(grp.set_index("service_type")["profit_amt"])

    if (not svc_f.empty) or (not exp_f.empty):
        tmp_s = svc_f.copy() if not svc_f.empty else pd.DataFrame(columns=["date","profit_amt"])
        tmp_s["Month"] = pd.to_datetime(tmp_s["date"]).dt.to_period("M").astype(str) if not tmp_s.empty else []
        monthly_profit = tmp_s.groupby("Month")["profit_amt"].sum().reset_index() if not tmp_s.empty else pd.DataFrame(columns=["Month","profit_amt"])
        tmp_e = exp_f.copy() if not exp_f.empty else pd.DataFrame(columns=["date","amount"])
        tmp_e["Month"] = pd.to_datetime(tmp_e["date"]).dt.to_period("M").astype(str) if not tmp_e.empty else []
        monthly_exp = tmp_e.groupby("Month")["amount"].sum().reset_index() if not tmp_e.empty else pd.DataFrame(columns=["Month","amount"])
        merged = pd.merge(monthly_profit, monthly_exp, left_on="Month", right_on="Month", how="outer").fillna(0).sort_values("Month")
        if not merged.empty:
            merged = merged.rename(columns={"profit_amt":"Profit","amount":"Expenses"})
            st.subheader("Monthly Profit vs Expenses")
            st.line_chart(merged.set_index("Month")[["Profit","Expenses"]])

    # exports
    if not svc_f.empty:
        st.download_button("⬇️ Download Services Report CSV", df_to_csv_bytes(svc_f), "report_services.csv", key="dl_rep_svc_csv")
        st.download_button("⬇️ Download Services Report Excel", df_to_excel_bytes(svc_f,"ServicesReport"), "report_services.xlsx", key="dl_rep_svc_xlsx")
    if not exp_f.empty:
        st.download_button("⬇️ Download Expenses Report CSV", df_to_csv_bytes(exp_f), "report_expenses.csv", key="dl_rep_exp_csv")
        st.download_button("⬇️ Download Expenses Report Excel", df_to_excel_bytes(exp_f,"ExpensesReport"), "report_expenses.xlsx", key="dl_rep_exp_xlsx")

def balances_page():
    st.header("💵 Balances")
    user_id = st.session_state.user["id"]
    svc = query_df("SELECT govt_amt,paid_amt,profit_amt FROM services WHERE user_id=?", (user_id,))
    exp = query_df("SELECT amount FROM expenses WHERE user_id=?", (user_id,))
    total_govt = float(svc["govt_amt"].sum()) if not svc.empty else 0.0
    total_paid = float(svc["paid_amt"].sum()) if not svc.empty else 0.0
    total_profit = float(svc["profit_amt"].sum()) if not svc.empty else 0.0
    total_expenses = float(exp["amount"].sum()) if not exp.empty else 0.0
    cash_in_hand = total_paid - total_expenses
    st.metric("Total Govt Amount (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid by Customers (₹)", f"{total_paid:,.2f}")
    st.metric("Total Service Profit (₹)", f"{total_profit:,.2f}")
    st.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    st.metric("Cash in Hand (simplified) (₹)", f"{cash_in_hand:,.2f}")

# --------------------------
# App navigation
# --------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES - Business Tracker", layout="wide")
    if st.session_state.user is None:
        login_ui()
        return

    # Sidebar
    st.sidebar.title("NANI ASSOCIATES")
    st.sidebar.write(f"Logged in as: **{st.session_state.user['username']}** ({st.session_state.user['device']})")
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
    ])

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
