# app.py - NANI ASSOCIATES
# Single-file Streamlit app with:
# - Admin login (single admin usable on multiple desktops)
# - Dashboard (auto cash/bank calc), Reports
# - Services master (add/edit/delete) with govt amounts
# - Services entry (use service from DB; auto govt amount)
# - Suppliers & Ledger, Expenses, Cash Book
# - Backup + restore safety for all tables (exports CSV if schema mismatch)
# NOTE: credentials stored in DB as plain text (can add hashing later)

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import os, csv, traceback

# ---------------- CONFIG ----------------
DB_PATH = "nani_associates.db"
ADMIN_USERNAME = "NANIASSOCIATES"
ADMIN_PASSWORD = "Chinni@gmail.com"

# Default services to preload if services table is empty
DEFAULT_SERVICES = [
    ("SERVICE","PAN SERVICE","NEW PAN CARD",107),
    ("SERVICE","PAN SERVICE","CORRECTION PAN CARD",107),
    ("SERVICE","PAN SERVICE","TAN",77),
    ("SERVICE","PAN SERVICE","ETDS",59),
    ("SERVICE","PAN SERVICE","ETDS 100 FILES ABOVE",None),
    ("SERVICE","PASSPORT","NEW PASSPORT",1550),
    ("SERVICE","PASSPORT","MINOR PASSPORT",1050),
    ("SERVICE","PASSPORT","RENEWAL PASSPORT",1550),
    ("SERVICE","DIGITAL SIGNATURE","DIGITAL SIGNATURE",1500),
    ("SERVICE","AADHAR SERVICE","NEW AADHAR",100),
    ("SERVICE","AADHAR SERVICE","MOBILE NUMBER LINK",100),
    ("SERVICE","AADHAR SERVICE","BIO MATRIC",150),
    ("SERVICE","AADHAR SERVICE","ADDRESS CHANGE WITH PROOF",100),
    ("SERVICE","AADHAR SERVICE","ADDRESS CHANGE WITHOUT PROOF",150),
    ("SERVICE","AADHAR SERVICE","NAME CHANGE WITH PROOF",100),
    ("SERVICE","AADHAR SERVICE","NAME CHANGE WITHOUT PROOF",150),
    ("SERVICE","AADHAR SERVICE","DATE OF BIRTH CHANGE WITH PROOF",150),
    ("SERVICE","AADHAR SERVICE","DATE OF BIRTH CHANGE WITHOUT PROOF",900),
    ("SERVICE","BIRTH CERTIFICATE","BIRTH CERTIFICATE FOR CUSTOMER",3000),
    ("SERVICE","BIRTH CERTIFICATE","BIRTH CERTIFICATE FOR AGENTS",3000),
    ("SERVICE","VOTER SERVICE","NEW VOTER",0),
    ("SERVICE","VOTER SERVICE","CORRECTION VOTER CARD",0),
    ("SERVICE","MSME SRRVICE","MSME CERTIFICATE",0),
    ("SERVICE","OTHER ONLINE SERVICE","OTHER SERVICES",None)
]

# ---------------- DB backup & restore helper ----------------
def backup_and_restore_table(cursor, table_name, expected_columns, create_sql):
    """
    - If table exists and schema differs, export old data to CSV and drop the table
    - Create table with create_sql
    - If backup CSV exists, attempt to restore rows into new schema (best-effort)
    """
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = [r[1] for r in cursor.fetchall()]
            if existing_cols != expected_columns:
                # Backup rows
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    backup_file = f"{table_name}_backup.csv"
                    with open(backup_file, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(existing_cols)
                        w.writerows(rows)
                    print(f"⚠️ {table_name}: exported old data to {backup_file}")
                cursor.execute(f"DROP TABLE {table_name}")
        # Create new table if not exists
        cursor.execute(create_sql)
        # Attempt restore from backup CSV
        backup_file = f"{table_name}_backup.csv"
        if os.path.exists(backup_file):
            with open(backup_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                restored = 0
                for row in reader:
                    # build values aligned to expected_columns
                    vals = [row.get(col, None) for col in expected_columns]
                    try:
                        placeholders = ",".join("?" * len(expected_columns))
                        cols_join = ",".join(expected_columns)
                        cursor.execute(f"INSERT INTO {table_name}({cols_join}) VALUES ({placeholders})", vals)
                        restored += 1
                    except Exception as e:
                        print(f"⚠️ Could not restore a row into {table_name}: {e}")
                if restored:
                    print(f"✅ Restored {restored} records into {table_name}")
    except Exception as e:
        print("Error during backup_and_restore_table:", e)
        traceback.print_exc()

# ---------------- DB init ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()

    # users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # ensure admin user
    c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users(username, password) VALUES (?,?)", (ADMIN_USERNAME, ADMIN_PASSWORD))

    # expected schemas & create SQL
    applications_expected = ["id","customer_name","service_id","service_name","govt_amount","charged_amount",
                             "payment_received","payment_pending","profit","payment_method","agent_name","created_at","note"]
    applications_create = '''
    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY,
        customer_name TEXT,
        service_id INTEGER,
        service_name TEXT,
        govt_amount REAL,
        charged_amount REAL,
        payment_received REAL,
        payment_pending REAL,
        profit REAL,
        payment_method TEXT,
        agent_name TEXT,
        created_at TEXT,
        note TEXT
    )
    '''

    expenses_expected = ["id","category","amount","date","note"]
    expenses_create = '''
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY,
        category TEXT,
        amount REAL,
        date TEXT,
        note TEXT
    )
    '''

    suppliers_expected = ["id","name","contact","type"]
    suppliers_create = '''
    CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY,
        name TEXT,
        contact TEXT,
        type TEXT
    )
    '''

    ledger_expected = ["id","supplier_id","amount","credit_or_debit","note","date"]
    ledger_create = '''
    CREATE TABLE IF NOT EXISTS ledger(
        id INTEGER PRIMARY KEY,
        supplier_id INTEGER,
        amount REAL,
        credit_or_debit TEXT,
        note TEXT,
        date TEXT
    )
    '''

    services_expected = ["id","main_category","sub_category","product_name","govt_amount"]
    services_create = '''
    CREATE TABLE IF NOT EXISTS services(
        id INTEGER PRIMARY KEY,
        main_category TEXT,
        sub_category TEXT,
        product_name TEXT,
        govt_amount REAL
    )
    '''

    cash_expected = ["id","type","amount","date","note"]
    cash_create = '''
    CREATE TABLE IF NOT EXISTS cash_book(
        id INTEGER PRIMARY KEY,
        type TEXT,
        amount REAL,
        date TEXT,
        note TEXT
    )
    '''

    # run backup & restore for each table
    backup_and_restore_table(c, "applications", applications_expected, applications_create)
    backup_and_restore_table(c, "expenses", expenses_expected, expenses_create)
    backup_and_restore_table(c, "suppliers", suppliers_expected, suppliers_create)
    backup_and_restore_table(c, "ledger", ledger_expected, ledger_create)
    backup_and_restore_table(c, "services", services_expected, services_create)
    backup_and_restore_table(c, "cash_book", cash_expected, cash_create)

    # preload default services if empty
    c.execute("SELECT COUNT(*) FROM services")
    try:
        if c.fetchone()[0] == 0:
            for main, sub, prod, amt in DEFAULT_SERVICES:
                c.execute("INSERT INTO services(main_category, sub_category, product_name, govt_amount) VALUES (?,?,?,?)",
                          (main, sub, prod, amt))
    except:
        pass

    conn.commit()
    conn.close()

# ---------------- UTIL ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def check_login(u, p):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    ok = c.fetchone() is not None
    conn.close()
    return ok

# ---------------- APP UI ----------------
st.set_page_config(page_title="NANI ASSOCIATES", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("NANI ASSOCIATES - Admin Login")
    with st.form("login_form"):
        ui = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    if submit:
        if check_login(ui, pw):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# persistent DB connection for page interactions
conn = get_conn()
c = conn.cursor()

# Build service labels from DB (safe fallback)
services_rows = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
service_labels = []
service_map = {}
for r in services_rows:
    main = r["main_category"] or ""
    sub = r["sub_category"] or ""
    prod = r["product_name"] or ""
    # clean label (avoid double slashes if empty)
    parts = [p for p in [main, sub, prod] if p and str(p).strip() != ""]
    label = " / ".join(parts) if parts else prod or "Unnamed Service"
    service_labels.append(label)
    service_map[label] = r

# Sidebar menu fixed
menu_items = ["Dashboard", "Services Master", "Services (Entry)", "Suppliers & Ledger", "Expenses", "Cash Book", "Reports", "Settings", "Logout"]
choice = st.sidebar.selectbox("Menu", menu_items)

# helper for quick ranges
def quick_range(option):
    today = date.today()
    if option == "Today":
        return today, today
    if option == "This Week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if option == "This Month":
        return today.replace(day=1), today
    return today, today

# ---------------- DASHBOARD ----------------
if choice == "Dashboard":
    st.title("Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        qr = st.radio("Quick range", ("Today","This Week","This Month","Custom"), index=0)
    if qr != "Custom":
        from_date, to_date = quick_range(qr)
    else:
        from_date = st.date_input("From", value=date.today() - timedelta(days=7))
        to_date = st.date_input("To", value=date.today())
    # filters
    svc_filter = st.selectbox("Service (All)", ["All"] + service_labels)
    agent_filter = st.text_input("Customer / Agent Name (optional)")

    # query apps
    if svc_filter == "All":
        apps_df = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))
    else:
        row = service_map[svc_filter]
        apps_df = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? AND date(created_at) BETWEEN ? AND ?", conn, params=(row["id"], from_date.isoformat(), to_date.isoformat()))
    if agent_filter:
        apps_df = apps_df[apps_df['customer_name'].str.contains(agent_filter, case=False, na=False) | apps_df['agent_name'].str.contains(agent_filter, case=False, na=False)]

    exp_df = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))
    ledger_df = pd.read_sql_query("SELECT * FROM ledger WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))
    cashdf = pd.read_sql_query("SELECT * FROM cash_book WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))

    total_income = apps_df['payment_received'].sum() if not apps_df.empty else 0.0
    total_charged = apps_df['charged_amount'].sum() if not apps_df.empty else 0.0
    total_profit_apps = apps_df['profit'].sum() if not apps_df.empty else 0.0
    total_expenses = exp_df['amount'].sum() if not exp_df.empty else 0.0
    ledger_debits = ledger_df[ledger_df['credit_or_debit']=='D']['amount'].sum() if not ledger_df.empty else 0.0
    ledger_credits = ledger_df[ledger_df['credit_or_debit']=='C']['amount'].sum() if not ledger_df.empty else 0.0

    apps_cash = apps_df[apps_df['payment_method']=='CASH']['payment_received'].sum() if not apps_df.empty else 0.0
    apps_bank = apps_df[apps_df['payment_method']=='BANK']['payment_received'].sum() if not apps_df.empty else 0.0
    cb_cash = cashdf[cashdf['type']=='CASH']['amount'].sum() if not cashdf.empty else 0.0
    cb_bank = cashdf[cashdf['type']=='BANK']['amount'].sum() if not cashdf.empty else 0.0

    cash_in_hand = apps_cash + cb_cash + ledger_credits - (total_expenses + ledger_debits)
    cash_at_bank = apps_bank + cb_bank

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Applications", len(apps_df))
    k2.metric("Income (received)", f"{total_income:.2f}")
    k3.metric("Expenses", f"{total_expenses:.2f}")
    k4.metric("Profit (calc)", f"{(total_income - total_expenses - ledger_debits + ledger_credits):.2f}")

    st.markdown("### Cash Balances (AUTO)")
    c1, c2 = st.columns(2)
    c1.info(f"Cash in Hand: {cash_in_hand:.2f}")
    c2.info(f"Cash at Bank: {cash_at_bank:.2f}")

    st.markdown("---")
    st.subheader("Applications")
    st.dataframe(apps_df.sort_values("created_at", ascending=False).reset_index(drop=True))

    st.subheader("Expenses")
    st.dataframe(exp_df)

    st.subheader("Supplier Ledger")
    st.dataframe(ledger_df)

    st.subheader("Cash Book (manual adjustments)")
    st.dataframe(cashdf)

# ---------------- SERVICES MASTER ----------------
elif choice == "Services Master":
    st.title("Services Master (add / edit / delete)")
    # show current services
    svc_df = pd.read_sql_query("SELECT * FROM services ORDER BY main_category, sub_category, product_name", conn)
    st.subheader("Existing Services")
    st.dataframe(svc_df)

    st.subheader("Add New Service")
    with st.form("add_service"):
        main_cat = st.text_input("Main Category", value="SERVICE")
        sub_cat = st.text_input("Sub Category", value="")
        prod_name = st.text_input("Product Name (eg NEW PAN CARD)")
        gov_amt = st.number_input("Govt Amount (leave 0 for manual/None)", value=0.0)
        add_s = st.form_submit_button("Add Service")
    if add_s:
        ga = None if gov_amt == 0 else float(gov_amt)
        try:
            c.execute("INSERT INTO services(main_category, sub_category, product_name, govt_amount) VALUES (?,?,?,?)",
                      (main_cat, sub_cat, prod_name, ga))
            conn.commit()
            st.success("Service added")
            st.experimental_rerun()
        except Exception as e:
            st.error("Could not add service: " + str(e))

    st.subheader("Edit / Delete Service")
    services = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
    if services:
        edit_map = {f"{s['id']} - {s['main_category']} / {s['sub_category']} / {s['product_name']}": s['id'] for s in services}
        sel_label = st.selectbox("Select service to edit", list(edit_map.keys()))
        sel_id = edit_map[sel_label]
        r = c.execute("SELECT * FROM services WHERE id=?", (sel_id,)).fetchone()
        with st.form("edit_service"):
            new_main = st.text_input("Main Category", value=r["main_category"])
            new_sub = st.text_input("Sub Category", value=r["sub_category"])
            new_prod = st.text_input("Product Name", value=r["product_name"])
            new_gov = st.number_input("Govt Amount (0 means None)", value=r["govt_amount"] if r["govt_amount"] is not None else 0.0)
            act = st.selectbox("Action", ["Update", "Delete"])
            ok = st.form_submit_button("Execute")
        if ok:
            try:
                if act == "Update":
                    new_g = None if new_gov == 0 else float(new_gov)
                    c.execute("UPDATE services SET main_category=?, sub_category=?, product_name=?, govt_amount=? WHERE id=?",
                              (new_main, new_sub, new_prod, new_g, sel_id))
                    conn.commit()
                    st.success("Service updated")
                    st.experimental_rerun()
                else:
                    c.execute("DELETE FROM services WHERE id=?", (sel_id,))
                    conn.commit()
                    st.success("Service deleted")
                    st.experimental_rerun()
            except Exception as e:
                st.error("Error: " + str(e))
    else:
        st.info("No services found")

# ---------------- SERVICES ENTRY (use services from DB) ----------------
elif choice == "Services (Entry)":
    st.title("Create Application (choose a service)")
    services = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
    if not services:
        st.warning("No services found. Add services in Services Master first.")
    else:
        options = []
        svc_map = {}
        for s in services:
            parts = [p for p in [s['main_category'], s['sub_category'], s['product_name']] if p and str(p).strip() != ""]
            label = " / ".join(parts)
            options.append(label)
            svc_map[label] = s
        sel = st.selectbox("Select Service", options)
        srow = svc_map[sel]
        govt = srow['govt_amount']
        st.info(f"Govt Amount (auto): {govt if govt is not None else 'MANUAL'}")
        with st.form("app_entry"):
            customer = st.text_input("Customer Name")
            charged = st.number_input("Charged Amount", value=float(govt) if govt else 0.0)
            received = st.number_input("Payment Received", value=0.0)
            payment_method = st.selectbox("Payment Method", ["CASH","BANK"])
            pending = charged - received
            profit = charged - (govt if govt else 0.0)
            agent = st.text_input("Supplier / Agent Name (optional)")
            note = st.text_area("Note")
            submit_app = st.form_submit_button("Save")
        if submit_app:
            created_at = datetime.now().isoformat()
            try:
                c.execute('''INSERT INTO applications(customer_name, service_id, service_name, govt_amount,
                             charged_amount, payment_received, payment_pending, profit, payment_method, agent_name, created_at, note)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (customer, srow['id'], srow['product_name'], govt, charged, received, pending, profit, payment_method, agent, created_at, note))
                conn.commit()
                st.success("Application saved")
            except Exception as e:
                st.error("Error saving application: " + str(e))
        # show recent for this service
        df = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? ORDER BY created_at DESC", conn, params=(srow['id'],))
        st.dataframe(df)

# ---------------- SUPPLIERS & LEDGER ----------------
elif choice == "Suppliers & Ledger":
    st.title("Suppliers & Ledger")
    st.subheader("Add Supplier")
    with st.form("add_supplier"):
        sname = st.text_input("Name")
        scontact = st.text_input("Contact")
        stype = st.selectbox("Type", ["Aadhar Agent","Birth Agent","Other"])
        add_supp = st.form_submit_button("Add")
    if add_supp:
        try:
            c.execute("INSERT INTO suppliers(name, contact, type) VALUES (?,?,?)", (sname, scontact, stype))
            conn.commit()
            st.success("Supplier added")
        except Exception as e:
            st.error("Could not add supplier: " + str(e))

    st.subheader("Add Ledger Entry")
    suppliers = c.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    if suppliers:
        sup_map = {f"{s['id']} - {s['name']}": s['id'] for s in suppliers}
        sel = st.selectbox("Select Supplier", list(sup_map.keys()))
        sup_id = sup_map[sel]
        with st.form("ledger_form"):
            amt = st.number_input("Amount")
            cd = st.selectbox("Credit or Debit", ["D","C"])
            note = st.text_input("Note")
            dt = st.date_input("Date", value=date.today())
            add_ledger = st.form_submit_button("Add Ledger")
        if add_ledger:
            try:
                c.execute("INSERT INTO ledger(supplier_id, amount, credit_or_debit, note, date) VALUES (?,?,?,?,?)",
                          (sup_id, amt, cd, note, dt.isoformat()))
                conn.commit(); st.success("Ledger entry added")
            except Exception as e:
                st.error("Could not add ledger: " + str(e))
        ledger_df = pd.read_sql_query("SELECT l.*, s.name as supplier_name FROM ledger l LEFT JOIN suppliers s ON l.supplier_id=s.id WHERE supplier_id=? ORDER BY date DESC", conn, params=(sup_id,))
        st.dataframe(ledger_df)
    else:
        st.info("No suppliers yet")

# ---------------- EXPENSES ----------------
elif choice == "Expenses":
    st.title("Expenses")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        add_exp = st.form_submit_button("Add Expense")
    if add_exp:
        try:
            c.execute("INSERT INTO expenses(category, amount, date, note) VALUES (?,?,?,?)", (cat, amt, dt.isoformat(), note))
            conn.commit(); st.success("Expense added")
        except Exception as e:
            st.error("Could not add expense: " + str(e))
    edf = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    st.dataframe(edf)

# ---------------- CASH BOOK ----------------
elif choice == "Cash Book":
    st.title("Cash Book - manual adjustments")
    with st.form("cash_form"):
        t = st.selectbox("Type", ["CASH","BANK"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        add_cash = st.form_submit_button("Record")
    if add_cash:
        try:
            c.execute("INSERT INTO cash_book(type, amount, date, note) VALUES (?,?,?,?)", (t, amt, dt.isoformat(), note))
            conn.commit(); st.success("Recorded")
        except Exception as e:
            st.error("Could not record: " + str(e))
    cb = pd.read_sql_query("SELECT * FROM cash_book ORDER BY date DESC", conn)
    st.dataframe(cb)

# ---------------- REPORTS ----------------
elif choice == "Reports":
    st.title("Reports")
    r_from = st.date_input("From", value=date.today() - timedelta(days=7))
    r_to = st.date_input("To", value=date.today())
    sfilter = st.selectbox("Service (All)", ["All"] + service_labels)
    if sfilter == "All":
        df = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(r_from.isoformat(), r_to.isoformat()))
    else:
        row = service_map[sfilter]
        df = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? AND date(created_at) BETWEEN ? AND ?", conn, params=(row['id'], r_from.isoformat(), r_to.isoformat()))
    st.dataframe(df)
    st.download_button("Download Applications CSV", df.to_csv(index=False).encode(), file_name=f"applications_{r_from}_{r_to}.csv")
    exp = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(r_from.isoformat(), r_to.isoformat()))
    st.subheader("Expenses")
    st.dataframe(exp)
    st.download_button("Download Expenses CSV", exp.to_csv(index=False).encode(), file_name=f"expenses_{r_from}_{r_to}.csv")

# ---------------- SETTINGS ----------------
elif choice == "Settings":
    st.title("Settings")
    st.write("Admin:", ADMIN_USERNAME)
    if st.button("Re-run DB init (safe, creates backups if mismatch)"):
        try:
            init_db()
            st.success("init_db() completed. Check for *_backup.csv files if schema mismatched earlier.")
        except Exception as e:
            st.error("Error running init_db(): " + str(e))
    st.markdown("**Services table (preview)**")
    st.dataframe(pd.read_sql_query("SELECT * FROM services ORDER BY main_category, sub_category, product_name", conn))

# ---------------- LOGOUT ----------------
elif choice == "Logout":
    st.session_state.logged_in = False
    st.experimental_rerun()

# Close connection
conn.close()
