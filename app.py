import streamlit as st
import sqlite3
import hashlib
import os
import shutil
import datetime
import pandas as pd

# ------------------- DATABASE SETUP -------------------
conn = sqlite3.connect("nani.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Admin table
def setup_admin_user():
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    conn.commit()
    # insert default admin if not exists
    c.execute("SELECT COUNT(*) as cnt FROM users")
    if c.fetchone()[0] == 0:
        pwd_hash = hashlib.sha256("Chinni@gmail.com".encode()).hexdigest()
        c.execute("INSERT INTO users(username, password_hash) VALUES(?,?)",
                  ("NANIASSOCIATES", pwd_hash))
        conn.commit()

# Services table with your master data
def setup_services_table():
    c.execute('''CREATE TABLE IF NOT EXISTS services
                 (service_name TEXT PRIMARY KEY,
                  govt_amount REAL)''')
    conn.commit()
    c.execute("SELECT COUNT(*) as cnt FROM services")
    if c.fetchone()[0] == 0:
        default_services = [
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
            ("DATE OF BIRTH CHANGE WITHOUT POOF", 900),
            ("BIRTH CERTIFICATE FOR CUSTOMER", 3000),
            ("BIRTH CERTIFICATE FOR AGENTS", 3000),
            ("NEW VOTER", 0),
            ("CORRECTION VOTER CARD", 0),
            ("MSME CERTIFICATE", 0),
            ("OTHER SERVICES", None),
        ]
        c.executemany("INSERT INTO services(service_name, govt_amount) VALUES (?,?)", default_services)
        conn.commit()

# Applications table
def setup_applications_table():
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_name TEXT,
                  agent_name TEXT,
                  service_name TEXT,
                  govt_amount REAL,
                  charged_amount REAL,
                  payment_received REAL,
                  payment_pending REAL,
                  profit REAL,
                  created_at TEXT,
                  note TEXT)''')
    conn.commit()

# Expenses table
def setup_expenses_table():
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  expense_name TEXT,
                  amount REAL,
                  created_at TEXT,
                  note TEXT)''')
    conn.commit()

# Suppliers ledger
def setup_suppliers_table():
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  supplier_name TEXT,
                  amount_paid REAL,
                  amount_pending REAL,
                  created_at TEXT,
                  note TEXT)''')
    conn.commit()

# Run setup
setup_admin_user()
setup_services_table()
setup_applications_table()
setup_expenses_table()
setup_suppliers_table()

# ------------------- BACKUP SYSTEM -------------------
def auto_backup():
    today = datetime.date.today().strftime("%Y-%m-%d")
    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f"{today}_nani.db")
    if not os.path.exists(backup_file):
        shutil.copy("nani.db", backup_file)

auto_backup()

# ------------------- LOGIN -------------------
def login(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    row = c.execute("SELECT * FROM users WHERE username=? AND password_hash=?",
                    (username, pwd_hash)).fetchone()
    return row is not None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("NANI ASSOCIATES - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(u, p):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid login")
    st.stop()

# ------------------- MAIN APP -------------------
menu = st.sidebar.selectbox("Menu", [
    "Dashboard", "Service Entry", "Expenses", "Suppliers Ledger", "Reports", "Backup"
])

# Fetch services for dropdown
services = pd.read_sql_query("SELECT service_name, govt_amount FROM services ORDER BY service_name", conn)

# Dashboard
if menu == "Dashboard":
    st.title("📊 Dashboard")
    apps = pd.read_sql_query("SELECT * FROM applications", conn)
    exps = pd.read_sql_query("SELECT * FROM expenses", conn)
    cash_in = apps["payment_received"].sum() if not apps.empty else 0
    cash_out = exps["amount"].sum() if not exps.empty else 0
    profit = apps["profit"].sum() if not apps.empty else 0
    st.metric("Cash In Hand", f"{cash_in - cash_out:.2f}")
    st.metric("Cash at Bank", f"{cash_in:.2f}")
    st.metric("Total Profit", f"{profit:.2f}")

# Service Entry
elif menu == "Service Entry":
    st.title("📝 Service Entry")
    cname = st.text_input("Customer / Agent Name")
    sname = st.selectbox("Service", services["service_name"])
    govt_amt = services.loc[services["service_name"] == sname, "govt_amount"].values[0]
    charged = st.number_input("Charged Amount", min_value=0.0, step=1.0)
    rec = st.number_input("Payment Received", min_value=0.0, step=1.0)
    pending = charged - rec
    profit = charged - (govt_amt if govt_amt else 0)
    note = st.text_area("Notes")
    if st.button("Save Service"):
        created_at = datetime.date.today().isoformat()
        c.execute('''INSERT INTO applications(customer_name, agent_name, service_name, govt_amount,
                     charged_amount, payment_received, payment_pending, profit, created_at, note)
                     VALUES (?,?,?,?,?,?,?,?,?,?)''',
                  (cname, cname, sname, govt_amt, charged, rec, pending, profit, created_at, note))
        conn.commit()
        st.success("Service saved ✅")

# Expenses
elif menu == "Expenses":
    st.title("💸 Expenses Entry")
    ename = st.text_input("Expense Name")
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    note = st.text_area("Notes")
    if st.button("Save Expense"):
        created_at = datetime.date.today().isoformat()
        c.execute("INSERT INTO expenses(expense_name, amount, created_at, note) VALUES (?,?,?,?)",
                  (ename, amount, created_at, note))
        conn.commit()
        st.success("Expense saved ✅")

# Suppliers Ledger
elif menu == "Suppliers Ledger":
    st.title("📒 Suppliers / Agents Ledger")
    sname = st.text_input("Supplier / Agent Name")
    paid = st.number_input("Amount Paid", min_value=0.0, step=1.0)
    pending = st.number_input("Pending Amount", min_value=0.0, step=1.0)
    note = st.text_area("Notes")
    if st.button("Save Supplier Entry"):
        created_at = datetime.date.today().isoformat()
        c.execute("INSERT INTO suppliers(supplier_name, amount_paid, amount_pending, created_at, note) VALUES (?,?,?,?,?)",
                  (sname, paid, pending, created_at, note))
        conn.commit()
        st.success("Supplier entry saved ✅")

# Reports
elif menu == "Reports":
    st.title("📑 Reports")
    start = st.date_input("Start Date", datetime.date.today())
    end = st.date_input("End Date", datetime.date.today())
    df = pd.read_sql_query("SELECT * FROM applications", conn)
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
        mask = (df["created_at"] >= pd.to_datetime(start)) & (df["created_at"] <= pd.to_datetime(end))
        st.dataframe(df.loc[mask])

# Backup
elif menu == "Backup":
    st.title("💾 Database Backup")
    with open("nani.db", "rb") as f:
        st.download_button("Download Current Database", f, file_name="nani.db")
    st.info("Automatic daily backups are saved inside /backup folder")
