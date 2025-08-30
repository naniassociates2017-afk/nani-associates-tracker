# app.py - NANI ASSOCIATES (single-file complete app)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import os, csv, traceback

# ----------------- CONFIG -----------------
DB_PATH = "nani_associates.db"
ADMIN_USERNAME = "NANIASSOCIATES"
ADMIN_PASSWORD = "Chinni@gmail.com"

# Services as tuples: (main_category, sub_category, product_name, govt_amount)
SERVICES = [
    ("SERVICE", "PAN SERVICE", "NEW PAN CARD", 107),
    ("SERVICE", "PAN SERVICE", "CORRECTION PAN CARD", 107),
    ("SERVICE", "PAN SERVICE", "TAN", 77),
    ("SERVICE", "PAN SERVICE", "ETDS", 59),
    ("SERVICE", "PAN SERVICE", "ETDS 100 FILES ABOVE", None),
    ("SERVICE", "PASSPORT", "NEW PASSPORT", 1550),
    ("SERVICE", "PASSPORT", "MINOR PASSPORT", 1050),
    ("SERVICE", "PASSPORT", "RENEWAL PASSPORT", 1550),
    ("SERVICE", "DIGITAL SIGNATURE", "DIGITAL SIGNATURE", 1500),
    ("SERVICE", "AADHAR SERVICE", "NEW AADHAR", 100),
    ("SERVICE", "AADHAR SERVICE", "MOBILE NUMBER LINK", 100),
    ("SERVICE", "AADHAR SERVICE", "BIO MATRIC", 150),
    ("SERVICE", "AADHAR SERVICE", "ADDRESS CHANGE WITH PROOF", 100),
    ("SERVICE", "AADHAR SERVICE", "ADDRESS CHANGE WITHOUT PROOF", 150),
    ("SERVICE", "AADHAR SERVICE", "NAME CHANGE WITH PROOF", 100),
    ("SERVICE", "AADHAR SERVICE", "NAME CHANGE WITHOUT PROOF", 150),
    ("SERVICE", "AADHAR SERVICE", "DATE OF BIRTH CHANGE WITH PROOF", 150),
    ("SERVICE", "AADHAR SERVICE", "DATE OF BIRTH CHANGE WITHOUT PROOF", 900),
    ("SERVICE", "BIRTH CERTIFICATE", "BIRTH CERTIFICATE FOR CUSTOMER", 3000),
    ("SERVICE", "BIRTH CERTIFICATE", "BIRTH CERTIFICATE FOR AGENTS", 3000),
    ("SERVICE", "VOTER SERVICE", "NEW VOTER", 0),
    ("SERVICE", "VOTER SERVICE", "CORRECTION VOTER CARD", 0),
    ("SERVICE", "MSME SRRVICE", "MSME CERTIFICATE", 0),
    ("SERVICE", "OTHER ONLINE SERVICE", "OTHER SERVICES", None)
]

# ---------------- DB SAFETY HELPERS ----------------
def backup_and_restore_table(cursor, table_name, expected_columns, create_sql, restore_map=None):
    """
    - Checks if table exists and if schema matches expected_columns.
    - If mismatch: export old rows to {table_name}_backup.csv, drop table.
    - Create table with create_sql.
    - If backup CSV exists, try to restore rows by mapping columns via restore_map (dict oldcol->newcol)
    """
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = [r[1] for r in cursor.fetchall()]
            if existing_cols != expected_columns:
                # Export old rows
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    backup_file = f"{table_name}_backup.csv"
                    with open(backup_file, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(existing_cols)
                        w.writerows(rows)
                    print(f"⚠️ {table_name}: Schema mismatch detected. Exported old data to {backup_file}")
                cursor.execute(f"DROP TABLE {table_name}")
        # Create table
        cursor.execute(create_sql)
        # Restore if backup exists
        backup_file = f"{table_name}_backup.csv"
        if os.path.exists(backup_file):
            with open(backup_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                restored = 0
                for row in reader:
                    # map row to expected_columns
                    vals = []
                    for col in expected_columns:
                        # direct match preferred
                        if col in row:
                            vals.append(row[col])
                        elif restore_map and col in restore_map:
                            oldcol = restore_map[col]
                            vals.append(row.get(oldcol, None))
                        else:
                            vals.append(None)
                    # try to insert
                    try:
                        placeholders = ",".join("?" * len(expected_columns))
                        cols_join = ",".join(expected_columns)
                        cursor.execute(f"INSERT INTO {table_name}({cols_join}) VALUES ({placeholders})", vals)
                        restored += 1
                    except Exception as e:
                        print(f"⚠️ Could not restore a row into {table_name}: {e}")
                if restored:
                    print(f"✅ Restored {restored} records into {table_name} from {backup_file}")
    except Exception as e:
        print("Error in backup_and_restore_table:", e)
        traceback.print_exc()

# ---------------- INITIALIZATION ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()

    # Users table (simple)
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # ensure admin exists
    c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users(username, password) VALUES (?, ?)", (ADMIN_USERNAME, ADMIN_PASSWORD))

    # Applications table expected schema
    app_expected = ["id","customer_name","service_id","service_name","govt_amount","charged_amount",
                    "payment_received","payment_pending","profit","payment_method","agent_name","created_at","note"]
    app_create = '''
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

    # Expenses expected
    exp_expected = ["id","category","amount","date","note"]
    exp_create = '''
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY,
        category TEXT,
        amount REAL,
        date TEXT,
        note TEXT
    )
    '''

    # Suppliers expected
    sup_expected = ["id","name","contact","type"]
    sup_create = '''
    CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY,
        name TEXT,
        contact TEXT,
        type TEXT
    )
    '''

    # Ledger expected
    led_expected = ["id","supplier_id","amount","credit_or_debit","note","date"]
    led_create = '''
    CREATE TABLE IF NOT EXISTS ledger(
        id INTEGER PRIMARY KEY,
        supplier_id INTEGER,
        amount REAL,
        credit_or_debit TEXT,
        note TEXT,
        date TEXT
    )
    '''

    # Services expected (structured)
    svc_expected = ["id","main_category","sub_category","product_name","govt_amount"]
    svc_create = '''
    CREATE TABLE IF NOT EXISTS services(
        id INTEGER PRIMARY KEY,
        main_category TEXT,
        sub_category TEXT,
        product_name TEXT,
        govt_amount REAL
    )
    '''

    # Cash book (manual adjustments/transfers)
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

    # Apply backup + restore for each table
    backup_and_restore_table(c, "applications", app_expected, app_create)
    backup_and_restore_table(c, "expenses", exp_expected, exp_create)
    backup_and_restore_table(c, "suppliers", sup_expected, sup_create)
    backup_and_restore_table(c, "ledger", led_expected, led_create)
    backup_and_restore_table(c, "services", svc_expected, svc_create)
    backup_and_restore_table(c, "cash_book", cash_expected, cash_create)

    # Preload SERVICES into services table if missing
    c.execute("SELECT COUNT(*) as cnt FROM services")
    cnt = c.fetchone()[0]
    if cnt == 0:
        for main, sub, prod, amt in SERVICES:
            try:
                c.execute("INSERT INTO services(main_category, sub_category, product_name, govt_amount) VALUES (?,?,?,?)",
                          (main, sub, prod, amt))
            except:
                pass

    conn.commit()
    conn.close()

# ----------------- UTIL -----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def verify_login(username, password):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    ok = c.fetchone() is not None
    conn.close()
    return ok

# ----------------- APP UI -----------------
st.set_page_config(page_title="NANI ASSOCIATES", layout="wide", initial_sidebar_state="expanded")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("NANI ASSOCIATES - Admin Login")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        if verify_login(username, password):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

conn = get_conn()
c = conn.cursor()

# Build services menu labels
c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name")
services_rows = c.fetchall()
service_labels = []
service_map = {}  # label -> service row
for r in services_rows:
    main = r["main_category"] or ""
    sub = r["sub_category"] or ""
    prod = r["product_name"] or ""
    label = f"{main} / {sub} / {prod}"
    service_labels.append(label)
    service_map[label] = r

# Sidebar menu: Dashboard + each service + suppliers/expenses/ledger/cash/reports/settings/logout
sidebar_items = ["Dashboard"] + service_labels + ["Suppliers & Ledger", "Expenses", "Cash Book", "Reports", "Settings", "Logout"]
choice = st.sidebar.selectbox("Menu", sidebar_items)

# Quick date range helper
def get_range_from_quick(q):
    today = date.today()
    if q == "today":
        return today, today
    if q == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if q == "this_month":
        start = today.replace(day=1)
        return start, today
    return today, today

# ---------------- DASHBOARD ----------------
if choice == "Dashboard":
    st.title("Dashboard")
    col_filters = st.columns([1,1,1,2])
    with col_filters[0]:
        if st.button("Today"):
            from_date, to_date = get_range_from_quick("today")
        elif st.button("This Week"):
            from_date, to_date = get_range_from_quick("this_week")
        elif st.button("This Month"):
            from_date, to_date = get_range_from_quick("this_month")
        else:
            from_date = st.date_input("From", value=date.today())
            to_date = st.date_input("To", value=date.today())
    # Additional filters
    with col_filters[1]:
        service_filter = st.selectbox("Service Filter", ["All"] + service_labels)
    with col_filters[2]:
        agent_filter = st.text_input("Customer / Agent Name (optional)")
    # compute metrics
    # Applications in range
    q_apps = "SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?"
    params = (from_date.isoformat(), to_date.isoformat())
    if service_filter != "All":
        srow = service_map[service_filter]
        q_apps = "SELECT * FROM applications WHERE service_id=? AND date(created_at) BETWEEN ? AND ?"
        params = (srow["id"], from_date.isoformat(), to_date.isoformat())
    apps_df = pd.read_sql_query(q_apps, conn, params=params)
    if agent_filter:
        apps_df = apps_df[apps_df['customer_name'].str.contains(agent_filter, case=False, na=False) | apps_df['agent_name'].str.contains(agent_filter, case=False, na=False)]

    # Expenses in range
    exp_df = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))

    # Ledger in range
    led_df = pd.read_sql_query("SELECT * FROM ledger WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))

    # Cash book manual entries
    cb_df = pd.read_sql_query("SELECT * FROM cash_book WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))

    total_income = apps_df['payment_received'].sum() if not apps_df.empty else 0.0
    total_charged = apps_df['charged_amount'].sum() if not apps_df.empty else 0.0
    total_profit_apps = apps_df['profit'].sum() if not apps_df.empty else 0.0
    total_expenses = exp_df['amount'].sum() if not exp_df.empty else 0.0
    ledger_debits = led_df[led_df['credit_or_debit']=='D']['amount'].sum() if not led_df.empty else 0.0  # payments to suppliers
    ledger_credits = led_df[led_df['credit_or_debit']=='C']['amount'].sum() if not led_df.empty else 0.0  # receipts from suppliers

    # Cash in hand & Cash at bank (AUTO-CALCULATED):
    # We'll compute from applications' payment_method tag plus manual cash_book adjustments.
    apps_cash = apps_df[apps_df['payment_method']=='CASH']['payment_received'].sum() if not apps_df.empty else 0.0
    apps_bank = apps_df[apps_df['payment_method']=='BANK']['payment_received'].sum() if not apps_df.empty else 0.0
    # cash_book adjustments:
    cb_cash = cb_df[cb_df['type']=='CASH']['amount'].sum() if not cb_df.empty else 0.0
    cb_bank = cb_df[cb_df['type']=='BANK']['amount'].sum() if not cb_df.empty else 0.0
    # Combine: receipts - outflows (expenses + ledger debits) + ledger credits
    cash_in_hand = apps_cash + cb_cash + ledger_credits - total_expenses - ledger_debits
    cash_at_bank = apps_bank + cb_bank  # bank receives minus transfers (if you record bank expenses in expenses, that affects cash_at_bank via cb entries)

    profit_overall = total_income - total_expenses - ledger_debits + ledger_credits

    # Show metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Applications", len(apps_df))
    k2.metric("Income (received)", f"{total_income:.2f}")
    k3.metric("Expenses", f"{total_expenses:.2f}")
    k4.metric("Profit (calc)", f"{profit_overall:.2f}")
    k5.metric("Profit (apps only)", f"{total_profit_apps:.2f}")

    b1, b2 = st.columns(2)
    with b1:
        st.info(f"Cash in Hand (AUTO): {cash_in_hand:.2f}")
        st.write("Breakdown:")
        st.write(f" - From apps (cash): {apps_cash:.2f}")
        st.write(f" - Ledger credits: {ledger_credits:.2f}")
        st.write(f" - Cash-book adjustments: {cb_cash:.2f}")
        st.write(f" - Outflows (expenses + ledger debits): {total_expenses + ledger_debits:.2f}")
    with b2:
        st.info(f"Cash at Bank (AUTO): {cash_at_bank:.2f}")
        st.write("Breakdown:")
        st.write(f" - From apps (bank): {apps_bank:.2f}")
        st.write(f" - Cash-book bank adjustments: {cb_bank:.2f}")

    st.markdown("---")
    st.subheader("Applications")
    st.dataframe(apps_df.sort_values("created_at", ascending=False))

    st.subheader("Expenses")
    st.dataframe(exp_df)

    st.subheader("Ledger (Suppliers)")
    st.dataframe(led_df)

    st.subheader("Cash Book (manual adjustments)")
    st.dataframe(cb_df)

# ---------------- SERVICE ENTRY (each service as menu)
elif choice in service_labels:
    st.title(choice)
    srow = service_map[choice]
    svc_id = srow["id"]
    govt_amt = srow["govt_amount"]
    st.info(f"Govt Amount (auto): {govt_amt if govt_amt is not None else 'MANUAL'}")
    with st.form("service_entry"):
        cust_name = st.text_input("Customer / Agent Name")
        charged = st.number_input("Charged Amount", value=float(govt_amt) if govt_amt else 0.0)
        payment_received = st.number_input("Payment Received", value=0.0)
        payment_method = st.selectbox("Payment Method", ["CASH", "BANK"])
        pending = charged - payment_received
        profit = charged - (govt_amt if govt_amt else 0.0)
        agent_name = st.text_input("Supplier / Agent Name (optional)")
        note = st.text_area("Note")
        submitted = st.form_submit_button("Save Application")
    if submitted:
        created_at = datetime.now().isoformat()
        try:
            c.execute('''INSERT INTO applications(customer_name, service_id, service_name, govt_amount,
                         charged_amount, payment_received, payment_pending, profit, payment_method, agent_name, created_at, note)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                      (cust_name, svc_id, srow["product_name"], govt_amt, charged, payment_received, pending, profit, payment_method, agent_name, created_at, note))
            conn.commit()
            st.success("Application saved")
        except Exception as e:
            st.error("Error saving application: " + str(e))
    # show recent applications for this service
    df = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? ORDER BY created_at DESC", conn, params=(svc_id,))
    st.dataframe(df)

# ---------------- SUPPLIERS & LEDGER ----------------
elif choice == "Suppliers & Ledger":
    st.title("Suppliers & Ledger")
    st.subheader("Add Supplier / Agent")
    with st.form("add_supplier"):
        sname = st.text_input("Name")
        scontact = st.text_input("Contact")
        stype = st.selectbox("Type", ["Aadhar Agent", "Birth Agent", "Other"])
        sub = st.form_submit_button("Add Supplier")
    if sub:
        try:
            c.execute("INSERT INTO suppliers(name, contact, type) VALUES (?,?,?)", (sname, scontact, stype))
            conn.commit(); st.success("Supplier added")
        except Exception as e:
            st.error("Could not add supplier: " + str(e))

    st.subheader("Add Ledger Entry")
    suppliers = c.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    if suppliers:
        sup_map = {f"{s['id']} - {s['name']}": s['id'] for s in suppliers}
        sel = st.selectbox("Select Supplier", list(sup_map.keys()))
        s_id = sup_map[sel]
        with st.form("ledger_form"):
            amt = st.number_input("Amount")
            cd = st.selectbox("Type", ["D", "C"])  # D = Debit (we paid to supplier), C = Credit (supplier paid to us)
            note = st.text_input("Note")
            dt = st.date_input("Date", value=date.today())
            sub2 = st.form_submit_button("Add Ledger Entry")
        if sub2:
            try:
                c.execute("INSERT INTO ledger(supplier_id, amount, credit_or_debit, note, date) VALUES (?,?,?,?,?)",
                          (s_id, amt, cd, note, dt.isoformat()))
                conn.commit(); st.success("Ledger entry added")
            except Exception as e:
                st.error("Could not add ledger: " + str(e))
        # show ledger for supplier
        ledger_df = pd.read_sql_query("SELECT l.*, s.name as supplier_name FROM ledger l LEFT JOIN suppliers s ON l.supplier_id=s.id WHERE supplier_id=? ORDER BY date DESC", conn, params=(s_id,))
        st.dataframe(ledger_df)
    else:
        st.info("No suppliers yet. Add one above.")

# ---------------- EXPENSES ----------------
elif choice == "Expenses":
    st.title("Expenses")
    with st.form("expense_form"):
        cat = st.selectbox("Category", ["Office Rent", "Power Bill", "Water Bill", "Computer Repair", "Machinery Repair", "Staff Salary", "Food Expenses", "Other"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        submit = st.form_submit_button("Add Expense")
    if submit:
        try:
            c.execute("INSERT INTO expenses(category, amount, date, note) VALUES (?,?,?,?)", (cat, amt, dt.isoformat(), note))
            conn.commit(); st.success("Expense added")
        except Exception as e:
            st.error("Could not add expense: " + str(e))
    edf = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    st.dataframe(edf)

# ---------------- CASH BOOK (manual adjustments) ----------------
elif choice == "Cash Book":
    st.title("Cash Book (manual adjustments)")
    with st.form("cash_form"):
        t = st.selectbox("Type", ["CASH", "BANK"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note (reason)")
        sub = st.form_submit_button("Record")
    if sub:
        try:
            c.execute("INSERT INTO cash_book(type, amount, date, note) VALUES (?,?,?,?)", (t, amt, dt.isoformat(), note))
            conn.commit(); st.success("Recorded")
        except Exception as e:
            st.error("Could not record cash entry: " + str(e))
    cb = pd.read_sql_query("SELECT * FROM cash_book ORDER BY date DESC", conn)
    st.dataframe(cb)

# ---------------- REPORTS ----------------
elif choice == "Reports":
    st.title("Reports")
    r_from = st.date_input("From", value=date.today() - timedelta(days=7))
    r_to = st.date_input("To", value=date.today())
    r_service = st.selectbox("Service (All for all)", ["All"] + service_labels)
    if r_service == "All":
        df = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(r_from.isoformat(), r_to.isoformat()))
    else:
        sr = service_map[r_service]
        df = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? AND date(created_at) BETWEEN ? AND ?", conn, params=(sr["id"], r_from.isoformat(), r_to.isoformat()))
    st.dataframe(df)
    csv = df.to_csv(index=False).encode()
    st.download_button("Download Applications CSV", csv, file_name=f"applications_{r_from}_{r_to}.csv")
    # Expenses report
    exp = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(r_from.isoformat(), r_to.isoformat()))
    st.subheader("Expenses")
    st.dataframe(exp)
    st.download_button("Download Expenses CSV", exp.to_csv(index=False).encode(), file_name=f"expenses_{r_from}_{r_to}.csv")

# ---------------- SETTINGS ----------------
elif choice == "Settings":
    st.title("Settings")
    st.info("Admin username/password are stored in DB. Change with caution.")
    if st.button("Show current admin username"):
        st.success(f"Admin: {ADMIN_USERNAME}")
    if st.button("Recreate DB schema (safe backup first)"):
        try:
            init_db()
            st.success("init_db() executed (tables created/checked). Check backup CSVs if schema mismatched earlier.")
        except Exception as e:
            st.error("Error running init_db(): " + str(e))
    st.markdown("**Preloaded services**")
    svc_df = pd.read_sql_query("SELECT * FROM services ORDER BY main_category, sub_category, product_name", conn)
    st.dataframe(svc_df)

# ---------------- LOGOUT ----------------
elif choice == "Logout":
    st.session_state.logged_in = False
    st.experimental_rerun()

# close connection cleanly
conn.close()
