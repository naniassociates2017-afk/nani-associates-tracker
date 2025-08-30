# app.py - NANI ASSOCIATES (single-file)
# Run: pip install streamlit pandas
#       streamlit run app.py

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import os, csv, io, zipfile, traceback

# ---------------- CONFIG ----------------
DB_PATH = "nani_associates.db"
ADMIN_USERNAME = "NANIASSOCIATES"
ADMIN_PASSWORD = "Chinni@gmail.com"

# default services to preload if none exist
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

# ---------------- DB safety helper ----------------
def backup_and_restore_table(cursor, table_name, expected_columns, create_sql):
    """If existing table schema differs, export old table to CSV and drop it,
       then create the correct table and attempt best-effort restore from CSV."""
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = [r[1] for r in cursor.fetchall()]
            if existing_cols != expected_columns:
                # backup
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    backup_file = f"{table_name}_backup.csv"
                    with open(backup_file, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(existing_cols)
                        w.writerows(rows)
                    print(f"[backup] {table_name} exported to {backup_file}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        # create table
        cursor.execute(create_sql)
        # restore if backup exists
        backup_file = f"{table_name}_backup.csv"
        if os.path.exists(backup_file):
            with open(backup_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                restored = 0
                for row in reader:
                    vals = [row.get(col, None) for col in expected_columns]
                    try:
                        placeholders = ",".join("?" * len(expected_columns))
                        cols_join = ",".join(expected_columns)
                        cursor.execute(f"INSERT INTO {table_name}({cols_join}) VALUES ({placeholders})", vals)
                        restored += 1
                    except Exception as e:
                        # best-effort: skip rows that fail
                        print("restore skip row:", e)
                if restored:
                    print(f"[restore] {restored} rows restored into {table_name}")
    except Exception as e:
        print("backup_and_restore_table error:", e)
        traceback.print_exc()

# ---------------- DB initialization ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()

    # users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )''')
    # ensure admin
    c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users(username, password) VALUES (?,?)", (ADMIN_USERNAME, ADMIN_PASSWORD))

    # expected schemas & create statements
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

    # apply backup & restore for each table
    backup_and_restore_table(c, "applications", applications_expected, applications_create)
    backup_and_restore_table(c, "expenses", expenses_expected, expenses_create)
    backup_and_restore_table(c, "suppliers", suppliers_expected, suppliers_create)
    backup_and_restore_table(c, "ledger", ledger_expected, ledger_create)
    backup_and_restore_table(c, "services", services_expected, services_create)
    backup_and_restore_table(c, "cash_book", cash_expected, cash_create)

    # preload services if empty
    c.execute("SELECT COUNT(*) FROM services")
    cnt = c.fetchone()[0]
    if cnt == 0:
        for m,s,p,a in DEFAULT_SERVICES:
            try:
                c.execute("INSERT INTO services(main_category, sub_category, product_name, govt_amount) VALUES (?,?,?,?)", (m,s,p,a))
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
    res = c.fetchone() is not None
    conn.close()
    return res

# ---------------- backup download helper ----------------
def make_backup_zip():
    """Create an in-memory ZIP containing the DB and any *_backup.csv files."""
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        # add DB
        if os.path.exists(DB_PATH):
            z.write(DB_PATH, arcname=os.path.basename(DB_PATH))
        # add CSV backups if present
        for fname in os.listdir("."):
            if fname.endswith("_backup.csv"):
                z.write(fname, arcname=fname)
    mem.seek(0)
    return mem.getvalue()

# ---------------- APP UI ----------------
st.set_page_config(page_title="NANI ASSOCIATES", layout="wide")
init_db()

# session login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("NANI ASSOCIATES - Admin Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        s = st.form_submit_button("Login")
    if s:
        if check_login(u, p):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# open DB connection for use
conn = get_conn()
c = conn.cursor()

# Build service labels safely (no //)
services_rows = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
service_labels = []
service_map = {}
for r in services_rows:
    parts = [p for p in (r["main_category"], r["sub_category"], r["product_name"]) if p and str(p).strip() != ""]
    label = " / ".join(parts)
    if label.strip()=="":
        label = f"Service {r['id']}"
    service_labels.append(label)
    service_map[label] = r

# fixed sidebar
menu_items = ["Dashboard", "Services Master", "Service Entry", "Suppliers & Ledger", "Expenses", "Cash Book", "Reports", "Settings", "Logout"]
choice = st.sidebar.selectbox("Menu", menu_items)

# helpers for date ranges
def quick_range(kind):
    today = date.today()
    if kind == "Today":
        return today, today
    if kind == "This Week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if kind == "This Month":
        start = today.replace(day=1)
        return start, today
    return today, today

# ---------------- DASHBOARD ----------------
if choice == "Dashboard":
    st.title("Dashboard")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        quick = st.selectbox("Quick range", ["Today", "This Week", "This Month", "Custom"])
    if quick != "Custom":
        from_date, to_date = quick_range(quick)
    else:
        from_date = st.date_input("From", value=date.today() - timedelta(days=7))
        to_date = st.date_input("To", value=date.today())
    svc_filter = st.selectbox("Service filter", ["All"] + service_labels)
    name_filter = st.text_input("Customer / Agent name (optional)")

    # fetch applications
    if svc_filter == "All":
        apps_df = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))
    else:
        srow = service_map[svc_filter]
        apps_df = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? AND date(created_at) BETWEEN ? AND ?", conn, params=(srow["id"], from_date.isoformat(), to_date.isoformat()))
    if name_filter:
        apps_df = apps_df[apps_df['customer_name'].str.contains(name_filter, case=False, na=False) | apps_df['agent_name'].str.contains(name_filter, case=False, na=False)]

    exp_df = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))
    ledger_df = pd.read_sql_query("SELECT * FROM ledger WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))
    cash_df = pd.read_sql_query("SELECT * FROM cash_book WHERE date(date) BETWEEN ? AND ?", conn, params=(from_date.isoformat(), to_date.isoformat()))

    total_income = apps_df['payment_received'].sum() if not apps_df.empty else 0.0
    total_charged = apps_df['charged_amount'].sum() if not apps_df.empty else 0.0
    total_profit_apps = apps_df['profit'].sum() if not apps_df.empty else 0.0
    total_expenses = exp_df['amount'].sum() if not exp_df.empty else 0.0
    ledger_debits = ledger_df[ledger_df['credit_or_debit']=='D']['amount'].sum() if not ledger_df.empty else 0.0
    ledger_credits = ledger_df[ledger_df['credit_or_debit']=='C']['amount'].sum() if not ledger_df.empty else 0.0

    apps_cash = apps_df[apps_df['payment_method']=='CASH']['payment_received'].sum() if not apps_df.empty else 0.0
    apps_bank = apps_df[apps_df['payment_method']=='BANK']['payment_received'].sum() if not apps_df.empty else 0.0
    cb_cash = cash_df[cash_df['type']=='CASH']['amount'].sum() if not cash_df.empty else 0.0
    cb_bank = cash_df[cash_df['type']=='BANK']['amount'].sum() if not cash_df.empty else 0.0

    cash_in_hand = apps_cash + cb_cash + ledger_credits - (total_expenses + ledger_debits)
    cash_at_bank = apps_bank + cb_bank

    # show metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Applications", len(apps_df))
    m2.metric("Income (received)", f"{total_income:.2f}")
    m3.metric("Expenses", f"{total_expenses:.2f}")
    m4.metric("Profit (calc)", f"{(total_income - total_expenses - ledger_debits + ledger_credits):.2f}")

    st.markdown("### Cash balances (auto-calculated)")
    c1, c2 = st.columns(2)
    c1.info(f"Cash in Hand: {cash_in_hand:.2f}")
    c2.info(f"Cash at Bank: {cash_at_bank:.2f}")

    st.markdown("---")
    st.subheader("Applications")
    st.dataframe(apps_df.sort_values("created_at", ascending=False).reset_index(drop=True))

    st.subheader("Expenses")
    st.dataframe(exp_df)

    st.subheader("Ledger")
    st.dataframe(ledger_df)

    st.subheader("Cash Book")
    st.dataframe(cash_df)

# ---------------- SERVICES MASTER ----------------
elif choice == "Services Master":
    st.title("Services Master")
    st.subheader("Existing services")
    svc_df = pd.read_sql_query("SELECT * FROM services ORDER BY main_category, sub_category, product_name", conn)
    st.dataframe(svc_df)
    st.subheader("Add new service")
    with st.form("svc_add"):
        main_cat = st.text_input("Main Category", value="SERVICE")
        sub_cat = st.text_input("Sub Category", value="")
        prod = st.text_input("Product Name")
        gov = st.number_input("Govt Amount (0 = None)", value=0.0)
        add = st.form_submit_button("Add Service")
    if add:
        try:
            val = None if gov == 0 else float(gov)
            c.execute("INSERT INTO services(main_category, sub_category, product_name, govt_amount) VALUES (?,?,?,?)",
                      (main_cat, sub_cat, prod, val))
            conn.commit()
            st.success("Service added")
            st.experimental_rerun()
        except Exception as e:
            st.error("Could not add service: " + str(e))

    st.subheader("Edit / Delete service")
    services = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
    if services:
        map_edit = {f"{s['id']} - {s['main_category']} / {s['sub_category']} / {s['product_name']}": s['id'] for s in services}
        sel = st.selectbox("Select service", list(map_edit.keys()))
        sid = map_edit[sel]
        rec = c.execute("SELECT * FROM services WHERE id=?", (sid,)).fetchone()
        with st.form("svc_edit"):
            emain = st.text_input("Main Category", value=rec["main_category"])
            esub = st.text_input("Sub Category", value=rec["sub_category"])
            eprod = st.text_input("Product Name", value=rec["product_name"])
            egov = st.number_input("Govt Amount (0 = None)", value=rec["govt_amount"] if rec["govt_amount"] is not None else 0.0)
            action = st.selectbox("Action", ["Update", "Delete"])
            go = st.form_submit_button("Execute")
        if go:
            try:
                if action == "Update":
                    new_g = None if egov == 0 else float(egov)
                    c.execute("UPDATE services SET main_category=?, sub_category=?, product_name=?, govt_amount=? WHERE id=?", (emain, esub, eprod, new_g, sid))
                    conn.commit(); st.success("Service updated"); st.experimental_rerun()
                else:
                    c.execute("DELETE FROM services WHERE id=?", (sid,))
                    conn.commit(); st.success("Service deleted"); st.experimental_rerun()
            except Exception as e:
                st.error("Error: " + str(e))
    else:
        st.info("No services to edit")

# ---------------- SERVICE ENTRY ----------------
elif choice == "Service Entry":
    st.title("Create Application (Service Entry)")
    services = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
    if not services:
        st.warning("No services available. Add services in Services Master first.")
    else:
        opts = []
        svc_map = {}
        for s in services:
            parts = [p for p in (s['main_category'], s['sub_category'], s['product_name']) if p and str(p).strip() != ""]
            label = " / ".join(parts)
            opts.append(label)
            svc_map[label] = s
        sel = st.selectbox("Select Service", opts)
        srow = svc_map[sel]
        gov = srow['govt_amount']
        st.info(f"Govt amount (auto): {gov if gov is not None else 'MANUAL'}")
        with st.form("app_add"):
            cname = st.text_input("Customer Name")
            charged = st.number_input("Charged Amount", value=float(gov) if gov else 0.0)
            received = st.number_input("Payment Received", value=0.0)
            pmethod = st.selectbox("Payment Method", ["CASH","BANK"])
            pending = charged - received
            profit = charged - (gov if gov else 0.0)
            agent = st.text_input("Supplier / Agent (optional)")
            note = st.text_area("Note")
            save_app = st.form_submit_button("Save Application")
        if save_app:
            try:
                created = datetime.now().isoformat()
                c.execute('''INSERT INTO applications(customer_name, service_id, service_name, govt_amount,
                             charged_amount, payment_received, payment_pending, profit, payment_method, agent_name, created_at, note)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (cname, srow['id'], srow['product_name'], gov, charged, received, pending, profit, pmethod, agent, created, note))
                conn.commit(); st.success("Application saved")
            except Exception as e:
                st.error("Error saving application: " + str(e))

        st.markdown("#### Recent applications for this service")
        dfsvc = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? ORDER BY created_at DESC", conn, params=(srow['id'],))
        # edit/delete per application
        st.dataframe(dfsvc)
        st.markdown("**Edit / Delete Application**")
        apps = c.execute("SELECT * FROM applications ORDER BY created_at DESC").fetchall()
        if apps:
            app_map = {f"{a['id']} - {a['customer_name']} / {a['service_name']} / {a['created_at']}": a['id'] for a in apps}
            selapp = st.selectbox("Select application to edit/delete", list(app_map.keys()))
            aid = app_map[selapp]
            row = c.execute("SELECT * FROM applications WHERE id=?", (aid,)).fetchone()
            with st.form("app_edit"):
                ncust = st.text_input("Customer Name", value=row["customer_name"])
                ncharged = st.number_input("Charged Amount", value=row["charged_amount"])
                nreceived = st.number_input("Payment Received", value=row["payment_received"])
                npm = st.selectbox("Payment Method", ["CASH","BANK"], index=0 if row["payment_method"]=="CASH" else 1)
                npending = ncharged - nreceived
                nprofit = ncharged - (row["govt_amount"] if row["govt_amount"] else 0.0)
                nagent = st.text_input("Agent", value=row["agent_name"] if row["agent_name"] else "")
                nnote = st.text_area("Note", value=row["note"] if row["note"] else "")
                act = st.selectbox("Action", ["Update", "Delete"])
                go = st.form_submit_button("Execute")
            if go:
                try:
                    if act == "Update":
                        c.execute("""UPDATE applications SET customer_name=?, charged_amount=?, payment_received=?, payment_pending=?, profit=?, payment_method=?, agent_name=?, note=?
                                     WHERE id=?""", (ncust, ncharged, nreceived, npending, nprofit, npm, nagent, nnote, aid))
                        conn.commit(); st.success("Application updated"); st.experimental_rerun()
                    else:
                        c.execute("DELETE FROM applications WHERE id=?", (aid,))
                        conn.commit(); st.success("Deleted application"); st.experimental_rerun()
                except Exception as e:
                    st.error("Error: " + str(e))
        else:
            st.info("No applications to edit")

# ---------------- SUPPLIERS & LEDGER ----------------
elif choice == "Suppliers & Ledger":
    st.title("Suppliers & Ledger")
    st.subheader("Add Supplier")
    with st.form("supp_add"):
        sname = st.text_input("Name")
        scontact = st.text_input("Contact")
        stype = st.selectbox("Type", ["Aadhar Agent","Birth Agent","Other"])
        add_s = st.form_submit_button("Add Supplier")
    if add_s:
        try:
            c.execute("INSERT INTO suppliers(name, contact, type) VALUES (?,?,?)", (sname, scontact, stype))
            conn.commit(); st.success("Supplier added"); st.experimental_rerun()
        except Exception as e:
            st.error("Could not add supplier: " + str(e))

    st.subheader("Add Ledger Entry")
    supps = c.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    if supps:
        map_s = {f"{s['id']} - {s['name']}": s['id'] for s in supps}
        sel = st.selectbox("Select supplier", list(map_s.keys()))
        sid = map_s[sel]
        with st.form("ledger_add"):
            lamt = st.number_input("Amount")
            lcd = st.selectbox("Credit or Debit", ["D","C"])  # D = we paid (debit), C = received (credit)
            lnote = st.text_input("Note")
            ldate = st.date_input("Date", value=date.today())
            addl = st.form_submit_button("Add Ledger")
        if addl:
            try:
                c.execute("INSERT INTO ledger(supplier_id, amount, credit_or_debit, note, date) VALUES (?,?,?,?,?)", (sid, lamt, lcd, lnote, ldate.isoformat()))
                conn.commit(); st.success("Ledger added"); st.experimental_rerun()
            except Exception as e:
                st.error("Could not add ledger: " + str(e))
        # show ledger and supplier balance
        ledger_df = pd.read_sql_query("SELECT l.*, s.name as supplier_name FROM ledger l LEFT JOIN suppliers s ON l.supplier_id=s.id WHERE supplier_id=? ORDER BY date DESC", conn, params=(sid,))
        st.dataframe(ledger_df)
        # balance: credits minus debits (from supplier perspective: if D - we paid => negative balance)
        credits = ledger_df[ledger_df['credit_or_debit']=='C']['amount'].sum() if not ledger_df.empty else 0.0
        debits = ledger_df[ledger_df['credit_or_debit']=='D']['amount'].sum() if not ledger_df.empty else 0.0
        st.info(f"Supplier Balance (credits - debits): {credits - debits:.2f}")
        # allow edit/delete ledger entries
        st.markdown("#### Edit/Delete Ledger Entry")
        all_led = c.execute("SELECT * FROM ledger WHERE supplier_id=? ORDER BY date DESC", (sid,)).fetchall()
        if all_led:
            map_led = {f"{l['id']} - {l['date']} / {l['credit_or_debit']} / {l['amount']}": l['id'] for l in all_led}
            selled = st.selectbox("Select ledger entry", list(map_led.keys()))
            lid = map_led[selled]
            row = c.execute("SELECT * FROM ledger WHERE id=?", (lid,)).fetchone()
            with st.form("led_edit"):
                lamt2 = st.number_input("Amount", value=row['amount'])
                lcd2 = st.selectbox("Type", ["D","C"], index=0 if row['credit_or_debit']=="D" else 1)
                lnote2 = st.text_input("Note", value=row['note'])
                ldate2 = st.date_input("Date", value=date.fromisoformat(row['date']))
                act2 = st.selectbox("Action", ["Update","Delete"])
                go2 = st.form_submit_button("Execute")
            if go2:
                try:
                    if act2 == "Update":
                        c.execute("UPDATE ledger SET amount=?, credit_or_debit=?, note=?, date=? WHERE id=?", (lamt2, lcd2, lnote2, ldate2.isoformat(), lid))
                        conn.commit(); st.success("Updated"); st.experimental_rerun()
                    else:
                        c.execute("DELETE FROM ledger WHERE id=?", (lid,)); conn.commit(); st.success("Deleted"); st.experimental_rerun()
                except Exception as e:
                    st.error("Error: " + str(e))
        else:
            st.info("No ledger entries for this supplier")
    else:
        st.info("No suppliers yet. Add one above.")

# ---------------- EXPENSES ----------------
elif choice == "Expenses":
    st.title("Expenses")
    with st.form("exp_add"):
        ecat = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"])
        eamt = st.number_input("Amount")
        edate = st.date_input("Date", value=date.today())
        enote = st.text_area("Note")
        add_e = st.form_submit_button("Add Expense")
    if add_e:
        try:
            c.execute("INSERT INTO expenses(category, amount, date, note) VALUES (?,?,?,?)", (ecat, eamt, edate.isoformat(), enote))
            conn.commit(); st.success("Expense added"); st.experimental_rerun()
        except Exception as e:
            st.error("Could not add expense: " + str(e))
    st.subheader("All expenses")
    edf = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    st.dataframe(edf)
    st.markdown("#### Edit / Delete Expense")
    exs = c.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    if exs:
        map_e = {f"{e['id']} - {e['date']} / {e['category']} / {e['amount']}": e['id'] for e in exs}
        sel_e = st.selectbox("Select expense", list(map_e.keys()))
        eid = map_e[sel_e]
        erow = c.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
        with st.form("exp_edit"):
            ecat2 = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"], index=0)
            eamt2 = st.number_input("Amount", value=erow['amount'])
            edate2 = st.date_input("Date", value=date.fromisoformat(erow['date']))
            enote2 = st.text_area("Note", value=erow['note'] if erow['note'] else "")
            acte = st.selectbox("Action", ["Update","Delete"])
            goe = st.form_submit_button("Execute")
        if goe:
            try:
                if acte == "Update":
                    c.execute("UPDATE expenses SET category=?, amount=?, date=?, note=? WHERE id=?", (ecat2, eamt2, edate2.isoformat(), enote2, eid))
                    conn.commit(); st.success("Updated"); st.experimental_rerun()
                else:
                    c.execute("DELETE FROM expenses WHERE id=?", (eid,)); conn.commit(); st.success("Deleted"); st.experimental_rerun()
            except Exception as e:
                st.error("Error: " + str(e))
    else:
        st.info("No expenses yet")

# ---------------- CASH BOOK ----------------
elif choice == "Cash Book":
    st.title("Cash Book (manual adjustments)")
    with st.form("cash_add"):
        ttype = st.selectbox("Type", ["CASH","BANK"])
        camt = st.number_input("Amount")
        cdate = st.date_input("Date", value=date.today())
        cnote = st.text_area("Note")
        addc = st.form_submit_button("Record")
    if addc:
        try:
            c.execute("INSERT INTO cash_book(type, amount, date, note) VALUES (?,?,?,?)", (ttype, camt, cdate.isoformat(), cnote))
            conn.commit(); st.success("Recorded"); st.experimental_rerun()
        except Exception as e:
            st.error("Could not record: " + str(e))
    st.subheader("All cashbook entries")
    cb = pd.read_sql_query("SELECT * FROM cash_book ORDER BY date DESC", conn)
    st.dataframe(cb)

# ---------------- REPORTS ----------------
elif choice == "Reports":
    st.title("Reports")
    rfrom = st.date_input("From", value=date.today() - timedelta(days=7))
    rto = st.date_input("To", value=date.today())
    sfilter = st.selectbox("Service filter", ["All"] + service_labels)
    if sfilter == "All":
        rdf = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(rfrom.isoformat(), rto.isoformat()))
    else:
        s = service_map[sfilter]
        rdf = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? AND date(created_at) BETWEEN ? AND ?", conn, params=(s['id'], rfrom.isoformat(), rto.isoformat()))
    st.dataframe(rdf)
    csv_bytes = rdf.to_csv(index=False).encode()
    st.download_button("Download Applications CSV", csv_bytes, file_name=f"applications_{rfrom}_{rto}.csv")
    expd = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(rfrom.isoformat(), rto.isoformat()))
    st.subheader("Expenses")
    st.dataframe(expd)
    st.download_button("Download Expenses CSV", expd.to_csv(index=False).encode(), file_name=f"expenses_{rfrom}_{rto}.csv")

# ---------------- SETTINGS ----------------
elif choice == "Settings":
    st.title("Settings & Maintenance")
    st.write("Admin user:", ADMIN_USERNAME)
    st.markdown("**Database & backups**")
    if st.button("Create on-demand backup (ZIP)"):
        try:
            blob = make_backup_zip()
            st.download_button("Download backup ZIP", blob, file_name=f"nani_backup_{date.today().isoformat()}.zip")
        except Exception as e:
            st.error("Could not create backup: " + str(e))
    st.write("Note: When schema mismatch occurs, CSV backups are auto-exported in the app folder with names like applications_backup.csv")
    st.markdown("---")
    st.subheader("Re-run DB init (safe)")
    if st.button("Run init_db()"):
        try:
            init_db()
            st.success("init_db() executed (check *_backup.csv files if any schema mismatch occurred).")
        except Exception as e:
            st.error("Error running init_db(): " + str(e))

# ---------------- LOGOUT ----------------
elif choice == "Logout":
    st.session_state.logged_in = False
    # safe rerun
    st.experimental_rerun()

# close DB at end
conn.close()
