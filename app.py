# app.py - NANI ASSOCIATES (updated: password hashing, opening balances, daily auto-backup)
# Run: pip install streamlit pandas
#       streamlit run app.py

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import os, csv, io, zipfile, traceback, hashlib, binascii

# ---------------- CONFIG ----------------
DB_PATH = "nani_associates.db"
BACKUP_FOLDER = "backups"
LAST_BACKUP_TRACK = ".last_backup_date"
ADMIN_USERNAME = "NANIASSOCIATES"
ADMIN_PASSWORD = "Chinni@gmail.com"  # initial value (will be migrated to hashed on first correct login)

# Default services
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

# ----------------- UTIL: hashing -----------------
def gen_salt():
    return binascii.hexlify(os.urandom(16)).decode()

def hash_password(password, salt):
    # sha256(salt + password)
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_hash(password, salt, stored_hash):
    return hash_password(password, salt) == stored_hash

# ---------------- DB backup & restore helper ----------------
def backup_and_restore_table(cursor, table_name, expected_columns, create_sql):
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = [r[1] for r in cursor.fetchall()]
            if existing_cols != expected_columns:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    backup_file = f"{table_name}_backup.csv"
                    with open(backup_file, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow(existing_cols)
                        w.writerows(rows)
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(create_sql)
        # attempt restore
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
                    except Exception:
                        # skip incompatible rows
                        pass
                # don't remove backup_file; keep for manual check
    except Exception as e:
        print("backup_and_restore_table error:", e)
        traceback.print_exc()

# ---------------- DB init ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()

    # users: keep old plain 'password' column for compatibility, add 'password_hash' and 'salt' columns if needed
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        password_hash TEXT,
        password_salt TEXT
    )''')
    # ensure admin user exists (if not present)
    c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
    row = c.fetchone()
    if row is None:
        # insert with plain password first (will be migrated to hash on login)
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
    opening_expected = ["id","type","amount","set_date"]
    opening_create = '''
    CREATE TABLE IF NOT EXISTS opening_balances(
        id INTEGER PRIMARY KEY,
        type TEXT,
        amount REAL,
        set_date TEXT
    )
    '''

    # backup & restore for each table
    backup_and_restore_table(c, "applications", applications_expected, applications_create)
    backup_and_restore_table(c, "expenses", expenses_expected, expenses_create)
    backup_and_restore_table(c, "suppliers", suppliers_expected, suppliers_create)
    backup_and_restore_table(c, "ledger", ledger_expected, ledger_create)
    backup_and_restore_table(c, "services", services_expected, services_create)
    backup_and_restore_table(c, "cash_book", cash_expected, cash_create)
    backup_and_restore_table(c, "opening_balances", opening_expected, opening_create)

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

# ---------------- DB helpers ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_user_to_hash_if_needed(username, password_plain):
    """If user exists with plain password and it matches given password_plain, migrate to hashed storage."""
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    # if user already has hash, verify it
    if row["password_hash"]:
        ok = verify_hash(password_plain, row["password_salt"], row["password_hash"])
        conn.close()
        return ok
    # else, compare plain password
    if row["password"] == password_plain:
        salt = gen_salt()
        phash = hash_password(password_plain, salt)
        c.execute("UPDATE users SET password_hash=?, password_salt=?, password=NULL WHERE username=?", (phash, salt, username))
        conn.commit(); conn.close()
        return True
    conn.close()
    return False

def verify_login(username, password):
    """Verify user either by hashed password or by plain password (migrates plain to hash)."""
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    if row["password_hash"]:
        return verify_hash(password, row["password_salt"], row["password_hash"])
    # migrate if plain matches
    return migrate_user_to_hash_if_needed(username, password)

# ---------------- backup utilities ----------------
def make_backup_zip_bytes():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(DB_PATH):
            z.write(DB_PATH, arcname=os.path.basename(DB_PATH))
        for fname in os.listdir("."):
            if fname.endswith("_backup.csv"):
                z.write(fname, arcname=fname)
    mem.seek(0)
    return mem.getvalue()

def auto_daily_backup():
    """Create a backup ZIP once per calendar day when the app starts (if not already created today)."""
    try:
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)
        today_str = date.today().isoformat()
        track = LAST_BACKUP_TRACK
        prev = None
        if os.path.exists(track):
            with open(track, "r", encoding="utf-8") as f:
                prev = f.read().strip()
        if prev != today_str:
            # create backup and save to backups folder
            blob = make_backup_zip_bytes()
            fname = os.path.join(BACKUP_FOLDER, f"nani_backup_{today_str}.zip")
            with open(fname, "wb") as f:
                f.write(blob)
            with open(track, "w", encoding="utf-8") as f:
                f.write(today_str)
            print(f"[auto backup] created {fname}")
            return fname
    except Exception as e:
        print("auto_daily_backup error:", e)
    return None

# ---------------- INITIALIZE ----------------
st.set_page_config(page_title="NANI ASSOCIATES", layout="wide")
init_db()
# run auto backup (best-effort)
auto_backup_file = auto_daily_backup()

# ---------------- UI: Login ----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("NANI ASSOCIATES - Admin Login")
    with st.form("login_form"):
        ui = st.text_input("Username", value=ADMIN_USERNAME)
        pw = st.text_input("Password", type="password")
        ok = st.form_submit_button("Login")
    if ok:
        if verify_login(ui, pw):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------------- open DB ----------------
conn = get_conn()
c = conn.cursor()

# Build services safely (avoid //)
services_rows = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
service_labels = []
service_map = {}
for r in services_rows:
    parts = [p for p in (r["main_category"], r["sub_category"], r["product_name"]) if p and str(p).strip() != ""]
    label = " / ".join(parts)
    if not label:
        label = f"Service {r['id']}"
    service_labels.append(label)
    service_map[label] = r

# Sidebar fixed menu
menu_items = ["Dashboard", "Services Master", "Service Entry", "Suppliers & Ledger", "Expenses", "Cash Book", "Reports", "Settings", "Logout"]
choice = st.sidebar.selectbox("Menu", menu_items)

# helper date ranges
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
    st.markdown("Quick range and filters")
    col1, col2 = st.columns([2,1])
    with col1:
        quick = st.selectbox("Quick range", ["Today","This Week","This Month","Custom"], index=0)
    if quick != "Custom":
        from_date, to_date = quick_range(quick)
    else:
        from_date = st.date_input("From", value=date.today() - timedelta(days=7))
        to_date = st.date_input("To", value=date.today())
    svc_filter = st.selectbox("Service (All)", ["All"] + service_labels)
    name_filter = st.text_input("Customer / Agent (optional)")

    # gather data
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

    # opening balances
    ob = pd.read_sql_query("SELECT * FROM opening_balances", conn)
    opening_cash = ob[ob['type']=='CASH']['amount'].sum() if not ob.empty else 0.0
    opening_bank = ob[ob['type']=='BANK']['amount'].sum() if not ob.empty else 0.0

    cash_in_hand = opening_cash + apps_cash + cb_cash + ledger_credits - (total_expenses + ledger_debits)
    cash_at_bank = opening_bank + apps_bank + cb_bank

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Applications", len(apps_df))
    col_b.metric("Income (received)", f"{total_income:.2f}")
    col_c.metric("Expenses", f"{total_expenses:.2f}")
    col_d.metric("Profit (calc)", f"{(total_income - total_expenses - ledger_debits + ledger_credits):.2f}")

    st.markdown("### Cash balances (AUTO)")
    ca, cb = st.columns(2)
    ca.info(f"Cash in Hand: {cash_in_hand:.2f}  (Opening: {opening_cash:.2f}, From apps(cash): {apps_cash:.2f})")
    cb.info(f"Cash at Bank: {cash_at_bank:.2f}  (Opening: {opening_bank:.2f}, From apps(bank): {apps_bank:.2f})")

    st.markdown("---")
    # small trend chart - income vs expenses by date
    if not apps_df.empty or not exp_df.empty:
        inc = apps_df.groupby(apps_df['created_at'].str[:10])['payment_received'].sum().rename('income')
        ex = exp_df.groupby(exp_df['date'])['amount'].sum().rename('expense')
        trend = pd.concat([inc, ex], axis=1).fillna(0)
        if not trend.empty:
            st.line_chart(trend)

    st.subheader("Applications")
    st.dataframe(apps_df.sort_values("created_at", ascending=False).reset_index(drop=True))

    st.subheader("Expenses")
    st.dataframe(exp_df)

    st.subheader("Supplier Ledger")
    st.dataframe(ledger_df)

    st.subheader("Cash Book (manual adjustments)")
    st.dataframe(cash_df)

# ---------------- SERVICES MASTER ----------------
elif choice == "Services Master":
    st.title("Services Master (Add / Edit / Delete)")
    svc_df = pd.read_sql_query("SELECT * FROM services ORDER BY main_category, sub_category, product_name", conn)
    st.dataframe(svc_df)

    with st.form("add_service"):
        st.subheader("Add Service")
        mcat = st.text_input("Main Category", value="SERVICE")
        scat = st.text_input("Sub Category", value="")
        pname = st.text_input("Product Name")
        gamt = st.number_input("Govt Amount (0 = None)", value=0.0)
        add = st.form_submit_button("Add Service")
    if add:
        try:
            val = None if gamt == 0 else float(gamt)
            c.execute("INSERT INTO services(main_category, sub_category, product_name, govt_amount) VALUES (?,?,?,?)", (mcat, scat, pname, val))
            conn.commit(); st.success("Service added"); st.experimental_rerun()
        except Exception as e:
            st.error("Could not add service: " + str(e))

    st.subheader("Edit / Delete Service")
    services = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
    if services:
        map_edit = {f"{s['id']} - {s['main_category']} / {s['sub_category']} / {s['product_name']}": s['id'] for s in services}
        sel = st.selectbox("Select service", list(map_edit.keys()))
        sid = map_edit[sel]
        rec = c.execute("SELECT * FROM services WHERE id=?", (sid,)).fetchone()
        with st.form("edit_service"):
            nm = st.text_input("Main Category", value=rec['main_category'])
            ns = st.text_input("Sub Category", value=rec['sub_category'])
            npn = st.text_input("Product Name", value=rec['product_name'])
            ng = st.number_input("Govt Amount (0 = None)", value=rec['govt_amount'] if rec['govt_amount'] is not None else 0.0)
            action = st.selectbox("Action", ["Update","Delete"])
            go = st.form_submit_button("Execute")
        if go:
            try:
                if action == "Update":
                    ngv = None if ng == 0 else float(ng)
                    c.execute("UPDATE services SET main_category=?, sub_category=?, product_name=?, govt_amount=? WHERE id=?", (nm, ns, npn, ngv, sid))
                    conn.commit(); st.success("Updated"); st.experimental_rerun()
                else:
                    c.execute("DELETE FROM services WHERE id=?", (sid,))
                    conn.commit(); st.success("Deleted"); st.experimental_rerun()
            except Exception as e:
                st.error("Error: " + str(e))
    else:
        st.info("No services available")

# ---------------- SERVICE ENTRY ----------------
elif choice == "Service Entry":
    st.title("Service Entry (Create Application)")
    services = c.execute("SELECT * FROM services ORDER BY main_category, sub_category, product_name").fetchall()
    if not services:
        st.warning("Add services first in Services Master")
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
        st.info(f"Govt Amount (auto): {gov if gov is not None else 'MANUAL'}")
        with st.form("app_add"):
            cname = st.text_input("Customer / Agent Name")
            charged = st.number_input("Charged Amount", value=float(gov) if gov else 0.0)
            received = st.number_input("Payment Received", value=0.0)
            pmethod = st.selectbox("Payment Method", ["CASH","BANK"])
            pending = charged - received
            profit = charged - (gov if gov else 0.0)
            agent = st.text_input("Supplier / Agent (optional)")
            note = st.text_area("Note")
            save = st.form_submit_button("Save Application")
        if save:
            try:
                now = datetime.now().isoformat()
                c.execute('''INSERT INTO applications(customer_name, service_id, service_name, govt_amount, charged_amount,
                             payment_received, payment_pending, profit, payment_method, agent_name, created_at, note)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (cname, srow['id'], srow['product_name'], gov, charged, received, pending, profit, pmethod, agent, now, note))
                conn.commit(); st.success("Saved")
            except Exception as e:
                st.error("Could not save: " + str(e))
        st.markdown("### Recent for this service")
        dfsvc = pd.read_sql_query("SELECT * FROM applications WHERE service_id=? ORDER BY created_at DESC", conn, params=(srow['id'],))
        st.dataframe(dfsvc)

        # edit/delete (global)
        st.markdown("### Edit / Delete Application")
        apps = c.execute("SELECT * FROM applications ORDER BY created_at DESC").fetchall()
        if apps:
            app_map = {f"{a['id']} - {a['customer_name']} / {a['service_name']} / {a['created_at']}": a['id'] for a in apps}
            selapp = st.selectbox("Select application", list(app_map.keys()))
            aid = app_map[selapp]
            row = c.execute("SELECT * FROM applications WHERE id=?", (aid,)).fetchone()
            with st.form("app_edit"):
                nc = st.text_input("Customer Name", value=row['customer_name'])
                ncg = st.number_input("Charged Amount", value=row['charged_amount'])
                nr = st.number_input("Payment Received", value=row['payment_received'])
                npm = st.selectbox("Payment Method", ["CASH","BANK"], index=0 if row['payment_method']=="CASH" else 1)
                npend = ncg - nr
                nprof = ncg - (row['govt_amount'] if row['govt_amount'] else 0.0)
                nag = st.text_input("Agent", value=row['agent_name'] if row['agent_name'] else "")
                nnote = st.text_area("Note", value=row['note'] if row['note'] else "")
                act = st.selectbox("Action", ["Update","Delete"])
                go = st.form_submit_button("Execute")
            if go:
                try:
                    if act == "Update":
                        c.execute("""UPDATE applications SET customer_name=?, charged_amount=?, payment_received=?, payment_pending=?, profit=?, payment_method=?, agent_name=?, note=?
                                     WHERE id=?""", (nc, ncg, nr, npend, nprof, npm, nag, nnote, aid))
                        conn.commit(); st.success("Updated"); st.experimental_rerun()
                    else:
                        c.execute("DELETE FROM applications WHERE id=?", (aid,))
                        conn.commit(); st.success("Deleted"); st.experimental_rerun()
                except Exception as e:
                    st.error("Error: " + str(e))
        else:
            st.info("No applications yet")

# ---------------- SUPPLIERS & LEDGER ----------------
elif choice == "Suppliers & Ledger":
    st.title("Suppliers & Ledger")
    with st.form("supp_add"):
        sname = st.text_input("Supplier Name")
        scontact = st.text_input("Contact")
        stype = st.selectbox("Type", ["Aadhar Agent","Birth Agent","Other"])
        add = st.form_submit_button("Add Supplier")
    if add:
        try:
            c.execute("INSERT INTO suppliers(name, contact, type) VALUES (?,?,?)", (sname, scontact, stype))
            conn.commit(); st.success("Added"); st.experimental_rerun()
        except Exception as e:
            st.error("Error: " + str(e))
    supps = c.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    if supps:
        map_s = {f"{s['id']} - {s['name']}": s['id'] for s in supps}
        sel = st.selectbox("Select supplier", list(map_s.keys()))
        sid = map_s[sel]
        with st.form("ledger_add"):
            lamt = st.number_input("Amount")
            lcd = st.selectbox("Credit or Debit", ["D","C"])
            lnote = st.text_input("Note")
            ldate = st.date_input("Date", value=date.today())
            addl = st.form_submit_button("Add Ledger")
        if addl:
            try:
                c.execute("INSERT INTO ledger(supplier_id, amount, credit_or_debit, note, date) VALUES (?,?,?,?,?)", (sid, lamt, lcd, lnote, ldate.isoformat()))
                conn.commit(); st.success("Ledger added"); st.experimental_rerun()
            except Exception as e:
                st.error("Error: " + str(e))
        ledger_df = pd.read_sql_query("SELECT l.*, s.name as supplier_name FROM ledger l LEFT JOIN suppliers s ON l.supplier_id=s.id WHERE supplier_id=? ORDER BY date DESC", conn, params=(sid,))
        st.dataframe(ledger_df)
        credits = ledger_df[ledger_df['credit_or_debit']=='C']['amount'].sum() if not ledger_df.empty else 0.0
        debits = ledger_df[ledger_df['credit_or_debit']=='D']['amount'].sum() if not ledger_df.empty else 0.0
        st.info(f"Supplier Balance (credits - debits): {credits - debits:.2f}")

        # edit/delete ledger entries
        if not ledger_df.empty:
            map_led = {f"{int(l['id'])} - {l['date']} / {l['credit_or_debit']} / {l['amount']}": l['id'] for l in ledger_df.to_dict('records')}
            selled = st.selectbox("Select ledger entry to edit/delete", list(map_led.keys()))
            lid = map_led[selled]
            row = c.execute("SELECT * FROM ledger WHERE id=?", (lid,)).fetchone()
            with st.form("led_edit"):
                lam = st.number_input("Amount", value=row['amount'])
                lcd2 = st.selectbox("Type", ["D","C"], index=0 if row['credit_or_debit']=="D" else 1)
                ln = st.text_input("Note", value=row['note'])
                ld = st.date_input("Date", value=date.fromisoformat(row['date']))
                act = st.selectbox("Action", ["Update","Delete"])
                go = st.form_submit_button("Execute")
            if go:
                try:
                    if act == "Update":
                        c.execute("UPDATE ledger SET amount=?, credit_or_debit=?, note=?, date=? WHERE id=?", (lam, lcd2, ln, ld.isoformat(), lid))
                        conn.commit(); st.success("Updated"); st.experimental_rerun()
                    else:
                        c.execute("DELETE FROM ledger WHERE id=?", (lid,)); conn.commit(); st.success("Deleted"); st.experimental_rerun()
                except Exception as e:
                    st.error("Error: " + str(e))
    else:
        st.info("No suppliers yet")

# ---------------- EXPENSES ----------------
elif choice == "Expenses":
    st.title("Expenses")
    with st.form("exp_add"):
        cat = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        add = st.form_submit_button("Add Expense")
    if add:
        try:
            c.execute("INSERT INTO expenses(category, amount, date, note) VALUES (?,?,?,?)", (cat, amt, dt.isoformat(), note))
            conn.commit(); st.success("Added"); st.experimental_rerun()
        except Exception as e:
            st.error("Error: " + str(e))
    edf = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    st.dataframe(edf)
    # edit/delete
    if not edf.empty:
        map_e = {f"{int(e['id'])} - {e['date']} / {e['category']} / {e['amount']}": e['id'] for e in edf.to_dict('records')}
        sel = st.selectbox("Select expense to edit/delete", list(map_e.keys()))
        eid = map_e[sel]
        er = c.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
        with st.form("exp_edit"):
            ecat = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"], index=0)
            eamt = st.number_input("Amount", value=er['amount'])
            edate = st.date_input("Date", value=date.fromisoformat(er['date']))
            enote = st.text_area("Note", value=er['note'] if er['note'] else "")
            action = st.selectbox("Action", ["Update","Delete"])
            go = st.form_submit_button("Execute")
        if go:
            try:
                if action == "Update":
                    c.execute("UPDATE expenses SET category=?, amount=?, date=?, note=? WHERE id=?", (ecat, eamt, edate.isoformat(), enote, eid))
                    conn.commit(); st.success("Updated"); st.experimental_rerun()
                else:
                    c.execute("DELETE FROM expenses WHERE id=?", (eid,)); conn.commit(); st.success("Deleted"); st.experimental_rerun()
            except Exception as e:
                st.error("Error: " + str(e))

# ---------------- CASH BOOK ----------------
elif choice == "Cash Book":
    st.title("Cash Book (manual adjustments)")
    with st.form("cash_add"):
        t = st.selectbox("Type", ["CASH","BANK"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        add = st.form_submit_button("Record")
    if add:
        try:
            c.execute("INSERT INTO cash_book(type, amount, date, note) VALUES (?,?,?,?)", (t, amt, dt.isoformat(), note))
            conn.commit(); st.success("Recorded"); st.experimental_rerun()
        except Exception as e:
            st.error("Error: " + str(e))
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
    st.download_button("Download Applications CSV", rdf.to_csv(index=False).encode(), file_name=f"applications_{rfrom}_{rto}.csv")
    edf = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(rfrom.isoformat(), rto.isoformat()))
    st.subheader("Expenses")
    st.dataframe(edf)
    st.download_button("Download Expenses CSV", edf.to_csv(index=False).encode(), file_name=f"expenses_{rfrom}_{rto}.csv")

# ---------------- SETTINGS ----------------
elif choice == "Settings":
    st.title("Settings & Maintenance")
    st.subheader("Admin account")
    st.write("Username:", ADMIN_USERNAME)
    st.info("Password stored securely with hashing (migrated automatically if old DB had plain text).")
    st.subheader("Opening Balances (one-time or adjust)")
    ob = pd.read_sql_query("SELECT * FROM opening_balances", conn)
    st.write("Existing opening balances (if any):")
    st.dataframe(ob)
    with st.form("opening"):
        typ = st.selectbox("Type", ["CASH","BANK"])
        amt = st.number_input("Amount")
        save = st.form_submit_button("Set / Add Opening Balance")
    if save:
        try:
            c.execute("INSERT INTO opening_balances(type, amount, set_date) VALUES (?,?,?)", (typ, float(amt), date.today().isoformat()))
            conn.commit(); st.success("Opening balance saved"); st.experimental_rerun()
        except Exception as e:
            st.error("Error: " + str(e))

    st.markdown("---")
    st.subheader("Backups")
    st.write("Auto daily backup (on app start) created file (if any):")
    if auto_backup_file:
        st.success(f"Auto backup created: {auto_backup_file}")
        with open(auto_backup_file, "rb") as f:
            st.download_button("Download today's auto backup", f.read(), file_name=os.path.basename(auto_backup_file))
    if st.button("Create on-demand backup ZIP"):
        try:
            blob = make_backup_zip_bytes()
            st.download_button("Download backup ZIP", blob, file_name=f"nani_backup_{date.today().isoformat()}.zip")
        except Exception as e:
            st.error("Could not create backup: " + str(e))
    st.markdown("---")
    st.subheader("Re-run DB init (safe - creates CSV backups if schema mismatch)")
    if st.button("Run init_db()"):
        try:
            init_db()
            st.success("init_db() run (check *_backup.csv files if any schema mismatches occurred).")
        except Exception as e:
            st.error("Error running init_db(): " + str(e))

# ---------------- LOGOUT ----------------
elif choice == "Logout":
    st.session_state.logged_in = False
    st.experimental_rerun()

# Close DB
conn.close()
