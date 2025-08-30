# app.py — NANI ASSOCIATES (fixed robust login migration)
# Run: pip install streamlit pandas
#      streamlit run app.py

import os, io, csv, zipfile, hashlib, binascii, traceback, shutil
from datetime import datetime, date, timedelta

import sqlite3
import pandas as pd
import streamlit as st

# ---------------- Configuration ----------------
DB_PATH = "nani_associates.db"
BACKUP_DIR = "backups"
ADMIN_USERNAME = "NANIASSOCIATES"
ADMIN_PASSWORD = "Chinni@gmail.com"  # will be migrated to hash on first login
APP_TITLE = "NANI ASSOCIATES"

# Default service list (name-only, with optional govt amount)
DEFAULT_SERVICES = [
    ("NEW PAN CARD", 107),
    ("CORRECTION PAN CARD", 107),
    ("TAN", 77),
    ("ETDS", 59),
    ("ETDS 100 FILES ABOVE", None),
    ("NEW PASSPORT", 1550),
    ("MINOR PASSPORT", 1050),
    ("RENEWAL PASSPORT", 1550),
    ("DIGITAL SIGNATURE", 1500),
    ("NEW AADHAR", 100),
    ("MOBILE NUMBER LINK", 100),
    ("BIO MATRIC", 150),
    ("ADDRESS CHANGE WITH PROOF", 100),
    ("ADDRESS CHANGE WITHOUT PROOF", 150),
    ("NAME CHANGE WITH PROOF", 100),
    ("NAME CHANGE WITHOUT PROOF", 150),
    ("DATE OF BIRTH CHANGE WITH PROOF", 150),
    ("DATE OF BIRTH CHANGE WITHOUT PROOF", 900),
    ("BIRTH CERTIFICATE FOR CUSTOMER", 3000),
    ("BIRTH CERTIFICATE FOR AGENTS", 3000),
    ("NEW VOTER", 0),
    ("CORRECTION VOTER CARD", 0),
    ("MSME CERTIFICATE", 0),
    ("OTHER SERVICES", None),
]

# ---------------- Helpers: hashing & rerun ----------------
def gen_salt():
    return binascii.hexlify(os.urandom(16)).decode()

def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_hash(password, salt, stored_hash):
    return hash_password(password, salt) == stored_hash

def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except Exception:
            st.warning("Please refresh the page manually.")

# ---------------- DB bootstrap ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Users: username is the key (no numeric IDs)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            password_salt TEXT,
            password TEXT
        )
    """)

    # Create admin if missing (plain password for migration on first login)
    c.execute("SELECT username FROM users WHERE username=?", (ADMIN_USERNAME,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users(username, password) VALUES (?,?)", (ADMIN_USERNAME, ADMIN_PASSWORD))

    # Services: name-only, unique
    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            service_name TEXT PRIMARY KEY,
            govt_amount REAL
        )
    """)

    # Suppliers (agents included here): name-only unique
    c.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_name TEXT PRIMARY KEY,
            contact TEXT,
            type TEXT
        )
    """)

    # Applications: no ID, use hidden rowid for edits/deletes
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            customer_name TEXT,
            agent_name TEXT,
            service_name TEXT,
            govt_amount REAL,
            charged_amount REAL,
            payment_received REAL,
            payment_pending REAL,
            profit REAL,
            payment_method TEXT,
            created_at TEXT,
            note TEXT
        )
    """)

    # Ledger: per supplier (credit/debit)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            supplier_name TEXT,
            amount REAL,
            credit_or_debit TEXT,
            note TEXT,
            date TEXT
        )
    """)

    # Expenses
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            category TEXT,
            amount REAL,
            date TEXT,
            note TEXT
        )
    """)

    # Cash book (manual adjustments if you want)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cash_book (
            type TEXT,
            amount REAL,
            date TEXT,
            note TEXT
        )
    """)

    # Opening balances (CASH/BANK)
    c.execute("""
        CREATE TABLE IF NOT EXISTS opening_balances (
            type TEXT,
            amount REAL,
            set_date TEXT
        )
    """)

    # Preload default services if empty
    c.execute("SELECT COUNT(*) AS n FROM services")
    if c.fetchone()["n"] == 0:
        for name, amt in DEFAULT_SERVICES:
            try:
                c.execute("INSERT INTO services(service_name, govt_amount) VALUES(?,?)", (name, amt))
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()

# ---------------- Login: robust migration & verify ----------------
def migrate_or_verify_login(username, password):
    """
    Robust login:
    - If hashed columns exist and are populated -> verify via hash
    - Else if plain password column exists and matches -> migrate to hashed columns (if possible) and return True
    - Otherwise return False
    The function carefully checks presence of keys and catches exceptions.
    """
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if not row:
            return False

        # check available columns safely
        keys = []
        try:
            # sqlite3.Row supports keys()
            keys = list(row.keys())
        except Exception:
            pass

        # If password_hash column exists and has a value, verify via hash
        if "password_hash" in keys and row["password_hash"]:
            # ensure salt exists (if not, fail safe)
            salt = row["password_salt"] if "password_salt" in keys and row["password_salt"] else ""
            ok = False
            try:
                ok = verify_hash(password, salt, row["password_hash"])
            except Exception:
                ok = False
            return ok

        # Else fallback: check plain password column
        if "password" in keys and row["password"]:
            if row["password"] == password:
                # Attempt to migrate: only if the columns exist (they do in init_db)
                try:
                    salt = gen_salt()
                    phash = hash_password(password, salt)
                    # update hashed columns and clear plaintext password
                    c.execute("UPDATE users SET password_hash=?, password_salt=?, password=NULL WHERE username=?", (phash, salt, username))
                    conn.commit()
                except Exception:
                    # migration failed, but login allowed
                    pass
                return True

        # No valid auth method
        return False
    except Exception as e:
        print("migrate_or_verify_login error:", e)
        traceback.print_exc()
        return False
    finally:
        conn.close()

# ---------------- Backups ----------------
def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

def auto_daily_backup():
    """Create a dated copy of the DB once per day into backups/"""
    try:
        ensure_dir(BACKUP_DIR)
        today = date.today().isoformat()
        dst = os.path.join(BACKUP_DIR, f"{today}_nani_associates.db")
        if not os.path.exists(dst) and os.path.exists(DB_PATH):
            shutil.copyfile(DB_PATH, dst)
            return dst
    except Exception as e:
        print("Auto-backup failed:", e)
    return None

def get_db_bytes():
    with open(DB_PATH, "rb") as f:
        return f.read()

# ---------------- App start ----------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
init_db()
auto_file = auto_daily_backup()

# ---------------- Login ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(f"{APP_TITLE} — Admin Login")
    with st.form("login"):
        u = st.text_input("Username", value=ADMIN_USERNAME)
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Login")
    if ok:
        if migrate_or_verify_login(u, p):
            st.session_state.logged_in = True
            safe_rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# ---------------- Open DB for main UI ----------------
conn = get_conn()
c = conn.cursor()

# Sidebar
menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Service Master", "Service Entry", "Suppliers & Ledger", "Expenses", "Cash Book", "Reports", "Settings", "Logout"]
)

# Utility: Quick ranges
def quick_range(kind: str):
    t = date.today()
    if kind == "Today":
        return t, t
    if kind == "This Week":
        start = t - timedelta(days=t.weekday())
        return start, t
    if kind == "This Month":
        start = t.replace(day=1)
        return start, t
    if kind == "Last 7 Days":
        return t - timedelta(days=6), t
    return t, t

# ---------------- Dashboard ----------------
if menu == "Dashboard":
    st.title("Dashboard")

    with st.expander("Filters", expanded=True):
        col1, col2, col3 = st.columns([1,1,2])
        quick = col1.selectbox("Quick", ["Today", "This Week", "This Month", "Last 7 Days", "Custom"], index=0)
        if quick == "Custom":
            from_d = col1.date_input("From", value=date.today() - timedelta(days=7))
            to_d = col2.date_input("To", value=date.today())
        else:
            from_d, to_d = quick_range(quick)
        # Service & Name filters
        services = pd.read_sql_query("SELECT service_name FROM services ORDER BY service_name", conn)["service_name"].tolist()
        sel_service = col3.selectbox("Service", ["All"] + services)
        text_filter = st.text_input("Customer / Agent (optional)")

    # Load data
    apps = pd.read_sql_query(
        "SELECT rowid, * FROM applications WHERE date(created_at) BETWEEN ? AND ?",
        conn, params=(from_d.isoformat(), to_d.isoformat())
    )
    if sel_service != "All":
        apps = apps[apps["service_name"] == sel_service]
    if text_filter:
        mask = (
            apps["customer_name"].fillna("").str.contains(text_filter, case=False) |
            apps["agent_name"].fillna("").str.contains(text_filter, case=False)
        )
        apps = apps[mask]

    expenses = pd.read_sql_query(
        "SELECT rowid, * FROM expenses WHERE date(date) BETWEEN ? AND ?",
        conn, params=(from_d.isoformat(), to_d.isoformat())
    )
    ledger = pd.read_sql_query(
        "SELECT rowid, * FROM ledger WHERE date(date) BETWEEN ? AND ?",
        conn, params=(from_d.isoformat(), to_d.isoformat())
    )
    cash_book = pd.read_sql_query(
        "SELECT rowid, * FROM cash_book WHERE date(date) BETWEEN ? AND ?",
        conn, params=(from_d.isoformat(), to_d.isoformat())
    )
    openings = pd.read_sql_query("SELECT * FROM opening_balances", conn)

    # Metrics
    total_income = apps["payment_received"].sum() if not apps.empty else 0.0
    total_expenses = expenses["amount"].sum() if not expenses.empty else 0.0
    total_profit = apps["profit"].sum() if not apps.empty else 0.0

    apps_cash = apps[apps["payment_method"] == "CASH"]["payment_received"].sum() if not apps.empty else 0.0
    apps_bank = apps[apps["payment_method"] == "BANK"]["payment_received"].sum() if not apps.empty else 0.0

    open_cash = openings[openings["type"] == "CASH"]["amount"].sum() if not openings.empty else 0.0
    open_bank = openings[openings["type"] == "BANK"]["amount"].sum() if not openings.empty else 0.0

    cb_cash = cash_book[cash_book["type"] == "CASH"]["amount"].sum() if not cash_book.empty else 0.0
    cb_bank = cash_book[cash_book["type"] == "BANK"]["amount"].sum() if not cash_book.empty else 0.0

    ledger_debits = ledger[ledger["credit_or_debit"] == "D"]["amount"].sum() if not ledger.empty else 0.0
    ledger_credits = ledger[ledger["credit_or_debit"] == "C"]["amount"].sum() if not ledger.empty else 0.0

    cash_in_hand = open_cash + apps_cash + cb_cash + ledger_credits - (total_expenses + ledger_debits)
    cash_at_bank = open_bank + apps_bank + cb_bank

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Applications", 0 if apps.empty else len(apps))
    c2.metric("Income (received)", f"{total_income:.2f}")
    c3.metric("Expenses", f"{total_expenses:.2f}")
    c4.metric("Profit (from applications)", f"{total_profit:.2f}")

    st.info(f"Cash in Hand: {cash_in_hand:.2f}   |   Cash at Bank: {cash_at_bank:.2f}")

    # Quick trend (income vs expenses by date)
    try:
        inc = apps.groupby(apps["created_at"].str[:10])["payment_received"].sum().rename("income") if not apps.empty else pd.Series(dtype=float)
        ex = expenses.groupby("date")["amount"].sum().rename("expense") if not expenses.empty else pd.Series(dtype=float)
        trend = pd.concat([inc, ex], axis=1).fillna(0)
        if not trend.empty:
            st.line_chart(trend)
    except Exception:
        pass

    st.subheader("Applications")
    st.dataframe(apps.sort_values("created_at", ascending=False).reset_index(drop=True))

    st.subheader("Expenses")
    st.dataframe(expenses)

    st.subheader("Supplier Ledger")
    st.dataframe(ledger)

# ---------------- Service Master ----------------
elif menu == "Service Master":
    st.title("Service Master (Name-only)")
    svc_df = pd.read_sql_query("SELECT service_name, govt_amount FROM services ORDER BY service_name", conn)
    st.dataframe(svc_df)

    st.subheader("Add Service")
    with st.form("svc_add"):
        sname = st.text_input("Service Name").strip()
        gamt = st.number_input("Govt Amount (leave 0 if not set)", value=0.0)
        add = st.form_submit_button("Add")
    if add:
        if not sname:
            st.error("Service name is required.")
        else:
            try:
                c.execute("INSERT INTO services(service_name, govt_amount) VALUES(?,?)", (sname, None if gamt == 0 else float(gamt)))
                conn.commit()
                st.success("Service added.")
                safe_rerun()
            except sqlite3.IntegrityError:
                st.error("Duplicate service name. Not added.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.subheader("Edit / Delete Service")
    all_services = pd.read_sql_query("SELECT service_name, govt_amount FROM services ORDER BY service_name", conn)
    if not all_services.empty:
        pick = st.selectbox("Select", all_services["service_name"].tolist())
        row = all_services[all_services["service_name"] == pick].iloc[0]
        with st.form("svc_edit"):
            new_name = st.text_input("Service Name", value=row["service_name"])
            new_amt = st.number_input("Govt Amount (0 for None)", value=float(row["govt_amount"] if pd.notna(row["govt_amount"]) else 0.0))
            action = st.selectbox("Action", ["Update", "Delete"])
            go = st.form_submit_button("Execute")
        if go:
            try:
                if action == "Update":
                    # If name changed, ensure no conflict
                    if new_name != pick:
                        c.execute("SELECT 1 FROM services WHERE service_name=?", (new_name,))
                        if c.fetchone():
                            st.error("Another service with this name already exists.")
                        else:
                            # Update references in applications too
                            c.execute("UPDATE applications SET service_name=? WHERE service_name=?", (new_name, pick))
                            c.execute("UPDATE services SET service_name=?, govt_amount=? WHERE service_name=?",
                                      (new_name, None if new_amt == 0 else float(new_amt), pick))
                            conn.commit()
                            st.success("Updated.")
                            safe_rerun()
                    else:
                        c.execute("UPDATE services SET govt_amount=? WHERE service_name=?",
                                  (None if new_amt == 0 else float(new_amt), pick))
                        conn.commit()
                        st.success("Updated.")
                        safe_rerun()
                else:
                    c.execute("DELETE FROM services WHERE service_name=?", (pick,))
                    conn.commit()
                    st.success("Deleted.")
                    safe_rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("No services yet.")

# ---------------- Service Entry ----------------
elif menu == "Service Entry":
    st.title("Service Entry")

    services = pd.read_sql_query("SELECT service_name, govt_amount FROM services ORDER BY service_name", conn)
    if services.empty:
        st.warning("Add services in Service Master first.")
    else:
        s = st.selectbox("Service", services["service_name"].tolist())
        srow = services[services["service_name"] == s].iloc[0]
        gov = None if pd.isna(srow["govt_amount"]) else float(srow["govt_amount"])
        st.info(f"Govt Amount: {gov if gov is not None else 'MANUAL'}")

        with st.form("app_add"):
            cname = st.text_input("Customer / Applicant Name")
            agent = st.text_input("Supplier / Agent Name (optional)")
            charged = st.number_input("Charged Amount", value=float(gov) if gov else 0.0)
            received = st.number_input("Payment Received", value=0.0)
            pmethod = st.selectbox("Payment Method", ["CASH", "BANK"])
            pending = charged - received
            profit = charged - (gov if gov else 0.0)
            note = st.text_area("Note")
            save = st.form_submit_button("Save")
        if save:
            try:
                now = datetime.now().isoformat()
                c.execute("""INSERT INTO applications(customer_name, agent_name, service_name, govt_amount, charged_amount,
                             payment_received, payment_pending, profit, payment_method, created_at, note)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                          (cname, agent, s, gov, charged, received, pending, profit, pmethod, now, note))
                conn.commit()
                st.success("Application saved.")
            except Exception as e:
                st.error(f"Could not save: {e}")

        st.markdown("---")
        st.subheader("Recent Applications")
        rec = pd.read_sql_query("SELECT rowid, * FROM applications ORDER BY created_at DESC LIMIT 200", conn)
        st.dataframe(rec)

        st.subheader("Edit / Delete Application")
        if not rec.empty:
            sel = st.selectbox(
                "Pick a record",
                [f"{int(r['rowid'])} | {r['created_at']} | {r['customer_name']} | {r['service_name']}" for _, r in rec.iterrows()]
            )
            rowid = int(sel.split("|")[0].strip())
            row = pd.read_sql_query("SELECT rowid, * FROM applications WHERE rowid=?", conn, params=(rowid,)).iloc[0]
            with st.form("app_edit"):
                nc = st.text_input("Customer / Applicant Name", value=row["customer_name"])
                na = st.text_input("Supplier / Agent Name", value=row["agent_name"] or "")
                ns = st.selectbox("Service", services["service_name"].tolist(), index=services["service_name"].tolist().index(row["service_name"]))
                gov2 = services[services["service_name"] == ns]["govt_amount"].iloc[0]
                gov2 = None if pd.isna(gov2) else float(gov2)
                st.caption(f"Govt Amount for '{ns}': {gov2 if gov2 is not None else 'MANUAL'}")
                ncharged = st.number_input("Charged Amount", value=float(row["charged_amount"]))
                nreceived = st.number_input("Payment Received", value=float(row["payment_received"]))
                npm = st.selectbox("Payment Method", ["CASH", "BANK"], index=0 if row["payment_method"] == "CASH" else 1)
                npend = ncharged - nreceived
                nprof = ncharged - (gov2 if gov2 else 0.0)
                nnote = st.text_area("Note", value=row["note"] or "")
                action = st.selectbox("Action", ["Update", "Delete"])
                go = st.form_submit_button("Execute")
            if go:
                try:
                    if action == "Update":
                        c.execute("""UPDATE applications SET customer_name=?, agent_name=?, service_name=?, govt_amount=?,
                                     charged_amount=?, payment_received=?, payment_pending=?, profit=?, payment_method=?, note=?
                                     WHERE rowid=?""",
                                  (nc, na, ns, gov2, ncharged, nreceived, npend, nprof, npm, nnote, rowid))
                        conn.commit()
                        st.success("Updated.")
                        safe_rerun()
                    else:
                        c.execute("DELETE FROM applications WHERE rowid=?", (rowid,))
                        conn.commit()
                        st.success("Deleted.")
                        safe_rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No applications yet.")

# ---------------- Suppliers & Ledger ----------------
elif menu == "Suppliers & Ledger":
    st.title("Suppliers & Ledger")

    st.subheader("Suppliers (name-only)")
    sup_df = pd.read_sql_query("SELECT supplier_name, contact, type FROM suppliers ORDER BY supplier_name", conn)
    st.dataframe(sup_df)

    with st.form("sup_add"):
        sn = st.text_input("Supplier Name").strip()
        sc = st.text_input("Contact")
        stp = st.selectbox("Type", ["Aadhar Agent", "Birth Agent", "Other"])
        add = st.form_submit_button("Add")
    if add:
        if not sn:
            st.error("Supplier name is required.")
        else:
            try:
                c.execute("INSERT INTO suppliers(supplier_name, contact, type) VALUES(?,?,?)", (sn, sc, stp))
                conn.commit()
                st.success("Supplier added.")
                safe_rerun()
            except sqlite3.IntegrityError:
                st.error("Duplicate supplier name. Not added.")
            except Exception as e:
                st.error(f"Error: {e}")

    if not sup_df.empty:
        st.subheader("Edit / Delete Supplier")
        pick = st.selectbox("Select Supplier", pd.read_sql_query("SELECT supplier_name FROM suppliers ORDER BY supplier_name", conn)["supplier_name"].tolist())
        row = pd.read_sql_query("SELECT * FROM suppliers WHERE supplier_name=?", conn, params=(pick,)).iloc[0]
        with st.form("sup_edit"):
            nname = st.text_input("Supplier Name", value=row["supplier_name"])
            ncontact = st.text_input("Contact", value=row["contact"] or "")
            ntype = st.selectbox("Type", ["Aadhar Agent", "Birth Agent", "Other"], index=["Aadhar Agent","Birth Agent","Other"].index(row["type"] or "Other"))
            action = st.selectbox("Action", ["Update", "Delete"])
            go = st.form_submit_button("Execute")
        if go:
            try:
                if action == "Update":
                    if nname != pick:
                        c.execute("SELECT 1 FROM suppliers WHERE supplier_name=?", (nname,))
                        if c.fetchone():
                            st.error("Another supplier with this name already exists.")
                        else:
                            c.execute("UPDATE ledger SET supplier_name=? WHERE supplier_name=?", (nname, pick))
                            c.execute("UPDATE suppliers SET supplier_name=?, contact=?, type=? WHERE supplier_name=?",
                                      (nname, ncontact, ntype, pick))
                            conn.commit()
                            st.success("Updated.")
                            safe_rerun()
                    else:
                        c.execute("UPDATE suppliers SET contact=?, type=? WHERE supplier_name=?", (ncontact, ntype, pick))
                        conn.commit()
                        st.success("Updated.")
                        safe_rerun()
                else:
                    c.execute("DELETE FROM suppliers WHERE supplier_name=?", (pick,))
                    conn.commit()
                    st.success("Deleted.")
                    safe_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("Ledger (per supplier)")

    all_sups = pd.read_sql_query("SELECT supplier_name FROM suppliers ORDER BY supplier_name", conn)["supplier_name"].tolist()
    if all_sups:
        sel_sup = st.selectbox("Supplier", all_sups)
        with st.form("led_add"):
            amt = st.number_input("Amount", min_value=0.0, step=1.0)
            ttype = st.selectbox("Type", ["D","C"])
            note = st.text_input("Note")
            dte = st.date_input("Date", value=date.today())
            addl = st.form_submit_button("Add Entry")
        if addl:
            try:
                c.execute("INSERT INTO ledger(supplier_name, amount, credit_or_debit, note, date) VALUES(?,?,?,?,?)",
                          (sel_sup, amt, ttype, note, dte.isoformat()))
                conn.commit()
                st.success("Ledger entry added.")
                safe_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        ldf = pd.read_sql_query("SELECT rowid, * FROM ledger WHERE supplier_name=? ORDER BY date DESC, rowid DESC", conn, params=(sel_sup,))
        st.dataframe(ldf)

        credits = ldf[ldf["credit_or_debit"]=="C"]["amount"].sum() if not ldf.empty else 0.0
        debits  = ldf[ldf["credit_or_debit"]=="D"]["amount"].sum() if not ldf.empty else 0.0
        st.info(f"Balance (Credits - Debits): {credits - debits:.2f}")

        if not ldf.empty:
            st.subheader("Edit / Delete Ledger Entry")
            pick_led = st.selectbox(
                "Pick a ledger row",
                [f"{int(r['rowid'])} | {r['date']} | {r['credit_or_debit']} | {r['amount']}" for _, r in ldf.iterrows()]
            )
            lid = int(pick_led.split("|")[0].strip())
            r = pd.read_sql_query("SELECT rowid, * FROM ledger WHERE rowid=?", conn, params=(lid,)).iloc[0]
            with st.form("led_edit"):
                namt = st.number_input("Amount", value=float(r["amount"]))
                ntt = st.selectbox("Type", ["D","C"], index=0 if r["credit_or_debit"]=="D" else 1)
                nnt = st.text_input("Note", value=r["note"] or "")
                nd = st.date_input("Date", value=date.fromisoformat(r["date"]))
                act = st.selectbox("Action", ["Update", "Delete"])
                go = st.form_submit_button("Execute")
            if go:
                try:
                    if act == "Update":
                        c.execute("UPDATE ledger SET amount=?, credit_or_debit=?, note=?, date=? WHERE rowid=?",
                                  (namt, ntt, nnt, nd.isoformat(), lid))
                        conn.commit()
                        st.success("Updated.")
                        safe_rerun()
                    else:
                        c.execute("DELETE FROM ledger WHERE rowid=?", (lid,))
                        conn.commit()
                        st.success("Deleted.")
                        safe_rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("Add suppliers first.")

# ---------------- Expenses ----------------
elif menu == "Expenses":
    st.title("Expenses")

    with st.form("exp_add"):
        cat = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"])
        amt = st.number_input("Amount", min_value=0.0, step=1.0)
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        add = st.form_submit_button("Add Expense")
    if add:
        try:
            c.execute("INSERT INTO expenses(category, amount, date, note) VALUES(?,?,?,?)", (cat, amt, dt.isoformat(), note))
            conn.commit()
            st.success("Expense added.")
            safe_rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    edf = pd.read_sql_query("SELECT rowid, * FROM expenses ORDER BY date DESC, rowid DESC", conn)
    st.dataframe(edf)

    if not edf.empty:
        st.subheader("Edit / Delete Expense")
        sel = st.selectbox(
            "Pick expense",
            [f"{int(r['rowid'])} | {r['date']} | {r['category']} | {r['amount']}" for _, r in edf.iterrows()]
        )
        rid = int(sel.split("|")[0].strip())
        r = pd.read_sql_query("SELECT rowid, * FROM expenses WHERE rowid=?", conn, params=(rid,)).iloc[0]
        with st.form("exp_edit"):
            ecat = st.selectbox("Category", ["Office Rent","Power Bill","Water Bill","Computer Repair","Machinery Repair","Staff Salary","Food Expenses","Other"], index=0)
            eamt = st.number_input("Amount", value=float(r["amount"]))
            edate = st.date_input("Date", value=date.fromisoformat(r["date"]))
            enote = st.text_area("Note", value=r["note"] or "")
            act = st.selectbox("Action", ["Update","Delete"])
            go = st.form_submit_button("Execute")
        if go:
            try:
                if act == "Update":
                    c.execute("UPDATE expenses SET category=?, amount=?, date=?, note=? WHERE rowid=?", (ecat, eamt, edate.isoformat(), enote, rid))
                    conn.commit()
                    st.success("Updated.")
                    safe_rerun()
                else:
                    c.execute("DELETE FROM expenses WHERE rowid=?", (rid,))
                    conn.commit()
                    st.success("Deleted.")
                    safe_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- Cash Book ----------------
elif menu == "Cash Book":
    st.title("Cash Book (manual adjustments)")
    with st.form("cash_add"):
        t = st.selectbox("Type", ["CASH","BANK"])
        amt = st.number_input("Amount", min_value=0.0, step=1.0)
        dt = st.date_input("Date", value=date.today())
        note = st.text_area("Note")
        add = st.form_submit_button("Record")
    if add:
        try:
            c.execute("INSERT INTO cash_book(type, amount, date, note) VALUES(?,?,?,?)", (t, amt, dt.isoformat(), note))
            conn.commit()
            st.success("Recorded.")
            safe_rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    cb = pd.read_sql_query("SELECT rowid, * FROM cash_book ORDER BY date DESC, rowid DESC", conn)
    st.dataframe(cb)

# ---------------- Reports ----------------
elif menu == "Reports":
    st.title("Reports")

    col1, col2, col3 = st.columns(3)
    f = col1.date_input("From", value=date.today() - timedelta(days=7))
    t = col2.date_input("To", value=date.today())
    services = pd.read_sql_query("SELECT service_name FROM services ORDER BY service_name", conn)["service_name"].tolist()
    sel_service = col3.selectbox("Service", ["All"] + services)

    if sel_service == "All":
        rdf = pd.read_sql_query("SELECT rowid, * FROM applications WHERE date(created_at) BETWEEN ? AND ? ORDER BY created_at DESC",
                                conn, params=(f.isoformat(), t.isoformat()))
    else:
        rdf = pd.read_sql_query("""SELECT rowid, * FROM applications WHERE service_name=? AND date(created_at) BETWEEN ? AND ?
                                   ORDER BY created_at DESC""",
                                conn, params=(sel_service, f.isoformat(), t.isoformat()))
    st.subheader("Applications")
    st.dataframe(rdf)
    st.download_button("Download Applications CSV", rdf.to_csv(index=False).encode(), file_name=f"applications_{f}_{t}.csv")

    edf = pd.read_sql_query("SELECT rowid, * FROM expenses WHERE date(date) BETWEEN ? AND ? ORDER BY date DESC", conn, params=(f.isoformat(), t.isoformat()))
    st.subheader("Expenses")
    st.dataframe(edf)
    st.download_button("Download Expenses CSV", edf.to_csv(index=False).encode(), file_name=f"expenses_{f}_{t}.csv")

    # Pending report
    st.subheader("Pending / Partially Pending Applications")
    pending_df = rdf[rdf["payment_pending"] > 0] if not rdf.empty else pd.DataFrame(columns=rdf.columns if not rdf.empty else [])
    st.dataframe(pending_df)

# ---------------- Settings ----------------
elif menu == "Settings":
    st.title("Settings & Maintenance")

    st.subheader("Admin Account")
    st.write("Username:", ADMIN_USERNAME)
    st.caption("Password is stored securely (hashed). If the database had a plain password, it is migrated automatically on first successful login.")

    st.subheader("Opening Balances")
    ob = pd.read_sql_query("SELECT rowid, * FROM opening_balances", conn)
    st.dataframe(ob)
    with st.form("ob_add"):
        typ = st.selectbox("Type", ["CASH","BANK"])
        amt = st.number_input("Amount", min_value=0.0, step=1.0)
        dt = st.date_input("Set Date", value=date.today())
        add = st.form_submit_button("Add Opening Balance")
    if add:
        try:
            c.execute("INSERT INTO opening_balances(type, amount, set_date) VALUES(?,?,?)", (typ, amt, dt.isoformat()))
            conn.commit()
            st.success("Opening balance added.")
            safe_rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("Backups")

    if auto_file:
        st.success(f"Auto daily backup created: {auto_file}")

    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists(DB_PATH):
            st.download_button("Download Current Database (.db)", get_db_bytes(), file_name=os.path.basename(DB_PATH))
    with col2:
        if st.button("Create & Download ZIP Backup"):
            try:
                mem = io.BytesIO()
                with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
                    if os.path.exists(DB_PATH):
                        z.write(DB_PATH, arcname=os.path.basename(DB_PATH))
                    for fname in os.listdir("."):
                        if fname.endswith("_backup.csv"):
                            z.write(fname, arcname=fname)
                mem.seek(0)
                st.download_button("Download ZIP Backup", mem.read(), file_name=f"nani_backup_{date.today().isoformat()}.zip")
            except Exception as e:
                st.error(f"Backup failed: {e}")

# ---------------- Logout ----------------
elif menu == "Logout":
    st.session_state.logged_in = False
    safe_rerun()

# Close DB at end
conn.close()
