import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta

# ---------------- CONFIG ----------------
DB_PATH = 'nani_associates.db'
ADMIN_USERNAME = 'NANIASSOCIATES'
ADMIN_PASSWORD = 'Chinni@gmail.com'

SERVICES = [
    ("PAN - NEW PAN CARD", 107),
    ("PAN - CORRECTION PAN CARD", 107),
    ("PAN - TAN", 77),
    ("PAN - ETDS", 59),
    ("PASSPORT - NEW PASSPORT", 1550),
    ("PASSPORT - MINOR PASSPORT", 1050),
    ("PASSPORT - RENEWAL PASSPORT", 1550),
    ("DIGITAL SIGNATURE - DIGITAL SIGNATURE", 1500),
    ("AADHAR - NEW AADHAR", 100),
    ("AADHAR - MOBILE NUMBER LINK", 100),
    ("AADHAR - BIO METRIC", 150),
    ("AADHAR - ADDRESS CHANGE WITH PROOF", 100),
    ("AADHAR - ADDRESS CHANGE WITHOUT PROOF", 150),
    ("AADHAR - NAME CHANGE WITH PROOF", 100),
    ("AADHAR - NAME CHANGE WITHOUT PROOF", 150),
    ("AADHAR - DOB CHANGE WITH PROOF", 150),
    ("AADHAR - DOB CHANGE WITHOUT PROOF", 900),
    ("BIRTH CERTIFICATE - FOR CUSTOMER", 3000),
    ("BIRTH CERTIFICATE - FOR AGENTS", 3000),
    ("VOTER - NEW VOTER", 0),
    ("VOTER - CORRECTION VOTER CARD", 0),
    ("MSME - MSME CERTIFICATE", 0),
    ("OTHER - MANUAL SERVICE", None)
]

# ---------------- DB ----------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS services(
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    govt_amount REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS applications(
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT,
                    service_name TEXT,
                    govt_amount REAL,
                    charged_amount REAL,
                    payment_received REAL,
                    payment_pending REAL,
                    profit REAL,
                    agent_name TEXT,
                    created_at TEXT,
                    note TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    amount REAL,
                    date TEXT,
                    note TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS cash_book(
                    id INTEGER PRIMARY KEY,
                    type TEXT,
                    amount REAL,
                    date TEXT,
                    note TEXT)''')

    conn.commit()

    c.execute('SELECT * FROM users WHERE username=?', (ADMIN_USERNAME,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users(username, password) VALUES (?, ?)', (ADMIN_USERNAME, ADMIN_PASSWORD))

    for name, amt in SERVICES:
        c.execute('SELECT id FROM services WHERE name=?', (name,))
        if c.fetchone() is None:
            c.execute('INSERT INTO services(name, govt_amount) VALUES (?, ?)', (name, amt))

    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------

def login(username, password):
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    row = c.fetchone(); conn.close()
    return row is not None

# ---------------- APP ----------------

st.set_page_config(page_title="NANI ASSOCIATES", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Admin Login")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    if submit:
        if login(u, p):
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

conn = get_conn(); c = conn.cursor()
menu = st.sidebar.selectbox("Menu", ["Dashboard"] + [s[0] for s in SERVICES] + ["Expenses", "Cash Book", "Reports", "Logout"])

# ---------------- Dashboard ----------------
if menu == "Dashboard":
    st.title("Dashboard")
    col1, col2, col3 = st.columns(3)
    if st.button("Today"):
        d1, d2 = date.today(), date.today()
    elif st.button("This Week"):
        d1, d2 = date.today() - timedelta(days=date.today().weekday()), date.today()
    elif st.button("This Month"):
        d1, d2 = date.today().replace(day=1), date.today()
    else:
        d1 = st.date_input("From", value=date.today())
        d2 = st.date_input("To", value=date.today())

    apps = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(d1.isoformat(), d2.isoformat()))
    expenses = pd.read_sql_query("SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?", conn, params=(d1.isoformat(), d2.isoformat()))

    total_income = apps['payment_received'].sum() if not apps.empty else 0
    total_expenses = expenses['amount'].sum() if not expenses.empty else 0
    profit = apps['profit'].sum() if not apps.empty else 0

    col1.metric("Total Applications", len(apps))
    col2.metric("Income", f"{total_income:.2f}")
    col3.metric("Profit", f"{profit - total_expenses:.2f}")

    st.dataframe(apps)

# ---------------- Service Entry ----------------
elif menu in [s[0] for s in SERVICES]:
    st.title(menu)
    govt_amt = next((s[1] for s in SERVICES if s[0]==menu), None)
    st.info(f"Govt Amount: {govt_amt}")
    with st.form("service_form"):
        cname = st.text_input("Customer/Agent Name")
        charged = st.number_input("Charged Amount", value=float(govt_amt) if govt_amt else 0.0)
        rec = st.number_input("Payment Received", value=0.0)
        pending = charged - rec
        profit = charged - (govt_amt if govt_amt else 0)
        note = st.text_area("Note")
        submitted = st.form_submit_button("Save")
    if submitted:
        created_at = datetime.now().isoformat()
        c.execute('''INSERT INTO applications(customer_name, service_name, govt_amount, charged_amount, payment_received, payment_pending, profit, agent_name, created_at, note)
                     VALUES (?,?,?,?,?,?,?,?,?,?)''', (cname, menu, govt_amt, charged, rec, pending, profit, cname, created_at, note))
        conn.commit()
        st.success("Application Saved")

    df = pd.read_sql_query("SELECT * FROM applications WHERE service_name=? ORDER BY created_at DESC", conn, params=(menu,))
    st.dataframe(df)

# ---------------- Expenses ----------------
elif menu == "Expenses":
    st.title("Expenses")
    with st.form("exp_form"):
        cat = st.selectbox("Category", ["Office Rent", "Power Bill", "Water Bill", "Computer Repair", "Machinery Repair", "Staff Salary", "Food Expenses", "Other"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_input("Note")
        sub = st.form_submit_button("Add")
    if sub:
        c.execute("INSERT INTO expenses(category, amount, date, note) VALUES (?,?,?,?)", (cat, amt, dt.isoformat(), note))
        conn.commit(); st.success("Expense added")
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    st.dataframe(df)

# ---------------- Cash Book ----------------
elif menu == "Cash Book":
    st.title("Cash Book")
    with st.form("cash_form"):
        t = st.selectbox("Type", ["CASH", "BANK"])
        amt = st.number_input("Amount")
        dt = st.date_input("Date", value=date.today())
        note = st.text_input("Note")
        sub = st.form_submit_button("Record")
    if sub:
        c.execute("INSERT INTO cash_book(type, amount, date, note) VALUES (?,?,?,?)", (t, amt, dt.isoformat(), note))
        conn.commit(); st.success("Recorded")
    cb = pd.read_sql_query("SELECT * FROM cash_book ORDER BY date DESC", conn)
    st.dataframe(cb)

# ---------------- Reports ----------------
elif menu == "Reports":
    st.title("Reports")
    d1 = st.date_input("From", value=date.today())
    d2 = st.date_input("To", value=date.today())
    df = pd.read_sql_query("SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?", conn, params=(d1.isoformat(), d2.isoformat()))
    st.dataframe(df)
    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "report.csv")

# ---------------- Logout ----------------
elif menu == "Logout":
    st.session_state.logged_in = False
    st.experimental_rerun()

conn.close()
