import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import hashlib

# ----------------------- CONFIG -----------------------
DB_PATH = 'nani_associates.db'
ADMIN_USERNAME = 'NANIASSOCIATES'
ADMIN_PASSWORD = 'Chinni@gmail.com'  # change if needed

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

# ----------------------- DB HELPERS -----------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    # services
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY,
            name TEXT,
            govt_amount REAL
        )
    ''')
    # customers/applications
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            customer_name TEXT,
            customer_mobile TEXT,
            service_id INTEGER,
            service_name TEXT,
            govt_amount REAL,
            charged_amount REAL,
            status TEXT,
            payment_received REAL,
            payment_pending REAL,
            supplier_id INTEGER,
            created_at TEXT,
            note TEXT
        )
    ''')
    # suppliers/agents
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            mobile TEXT,
            type TEXT
        )
    ''')
    # supplier ledger
    c.execute('''
        CREATE TABLE IF NOT EXISTS supplier_ledger (
            id INTEGER PRIMARY KEY,
            supplier_id INTEGER,
            amount REAL,
            credit_or_debit TEXT,
            note TEXT,
            date TEXT
        )
    ''')
    # expenses
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            category TEXT,
            amount REAL,
            date TEXT,
            note TEXT
        )
    ''')
    # cash balances
    c.execute('''
        CREATE TABLE IF NOT EXISTS cash_book (
            id INTEGER PRIMARY KEY,
            type TEXT, -- CASH or BANK
            amount REAL,
            date TEXT,
            note TEXT
        )
    ''')
    conn.commit()

    # create default admin user if not exists
    c.execute('SELECT * FROM users WHERE username=?', (ADMIN_USERNAME,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (ADMIN_USERNAME, ADMIN_PASSWORD))

    # preload services
    for name, amt in SERVICES:
        c.execute('SELECT id FROM services WHERE name=?', (name,))
        if c.fetchone() is None:
            c.execute('INSERT INTO services (name, govt_amount) VALUES (?, ?)', (name, amt))
    conn.commit()
    conn.close()

# ----------------------- UTIL -----------------------

def login(username, password):
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    row = c.fetchone()
    conn.close()
    return row is not None

# ----------------------- APP UI -----------------------

st.set_page_config(page_title='NANI ASSOCIATES', layout='wide')

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = ''

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title('NANI ASSOCIATES - Admin Login')
    with st.form('login_form'):
        u = st.text_input('Username')
        p = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Login')
    if submitted:
        if login(u, p):
            st.session_state.logged_in = True
            st.session_state.username = u
            st.experimental_rerun()
        else:
            st.error('Invalid credentials')
    st.info('Use credentials from the sheet. Single admin user - can login from multiple desktops')
    st.stop()

# --- AUTHENTICATED UI ---

conn = get_conn(); c = conn.cursor()
menu = st.sidebar.selectbox('Menu', ['Dashboard', 'New Application', 'Suppliers & Ledger', 'Expenses', 'Services', 'Reports', 'Cash Book', 'Settings', 'Logout'])

# ---------- DASHBOARD ----------
if menu == 'Dashboard':
    st.title('Dashboard - NANI ASSOCIATES')
    col1, col2, col3, col4 = st.columns(4)
    # quick filters
    with st.expander('Filters'):
        d1 = st.date_input('From', value=date.today())
        d2 = st.date_input('To', value=date.today())
        app_type = st.selectbox('Service Type', ['All'] + [s[0] for s in SERVICES])

    # queries
    q = 'SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?'
    params = (d1.isoformat(), d2.isoformat())
    if app_type != 'All':
        q = q.replace('WHERE', 'WHERE service_name=? AND')
        params = (app_type, d1.isoformat(), d2.isoformat())
    apps = pd.read_sql_query(q, conn, params=params)

    total_income = apps['payment_received'].sum() if not apps.empty else 0
    total_pending = apps['payment_pending'].sum() if not apps.empty else 0
    total_apps = len(apps)

    # expenses
    expenses_df = pd.read_sql_query('SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ?', conn, params=(d1.isoformat(), d2.isoformat()))
    total_expenses = expenses_df['amount'].sum() if not expenses_df.empty else 0

    # supplier payments (credits from suppliers)
    supplier_led = pd.read_sql_query('SELECT * FROM supplier_ledger WHERE date(date) BETWEEN ? AND ?', conn, params=(d1.isoformat(), d2.isoformat()))
    supplier_credit = supplier_led[supplier_led['credit_or_debit']=='C']['amount'].sum() if not supplier_led.empty else 0
    supplier_debit = supplier_led[supplier_led['credit_or_debit']=='D']['amount'].sum() if not supplier_led.empty else 0

    profit = total_income - total_expenses - supplier_debit + supplier_credit

    # cash book
    cash_df = pd.read_sql_query('SELECT * FROM cash_book WHERE date(date) BETWEEN ? AND ?', conn, params=(d1.isoformat(), d2.isoformat()))
    cash_in_hand = cash_df[cash_df['type']=='CASH']['amount'].sum() if not cash_df.empty else 0
    cash_at_bank = cash_df[cash_df['type']=='BANK']['amount'].sum() if not cash_df.empty else 0

    col1.metric('Total Applications', total_apps)
    col2.metric('Total Income', f"{total_income:.2f}")
    col3.metric('Total Expenses', f"{total_expenses:.2f}")
    col4.metric('Profit', f"{profit:.2f}")

    st.markdown('---')
    st.subheader('Breakdown')
    left, right = st.columns(2)
    with left:
        st.write('Applications')
        st.dataframe(apps)
    with right:
        st.write('Expenses & Supplier Ledger')
        st.write('Expenses')
        st.dataframe(expenses_df)
        st.write('Supplier Ledger')
        st.dataframe(supplier_led)

# ---------- New Application ----------
elif menu == 'New Application':
    st.title('Add New Application')
    with st.form('app_form'):
        cname = st.text_input('Customer Name')
        cmobile = st.text_input('Customer Mobile')
        service_list = [s[0] for s in SERVICES]
        sname = st.selectbox('Select Service', service_list)
        svc_row = next((x for x in SERVICES if x[0]==sname), None)
        govt = svc_row[1] if svc_row else None
        st.write(f'Govt Amount: {govt}')
        charged = st.number_input('Charged Amount', value=float(govt) if govt else 0.0)
        supplier = st.selectbox('Supplier/Agent (optional)', ['None'] + [r['name'] for r in c.execute('SELECT name FROM suppliers').fetchall()])
        status = st.selectbox('Status', ['Pending', 'Completed'])
        payment_received = st.number_input('Payment Received', value=0.0)
        note = st.text_area('Note')
        submitted = st.form_submit_button('Save Application')
    if submitted:
        created_at = datetime.now().isoformat()
        payment_pending = charged - payment_received
        supplier_id = None
        if supplier != 'None':
            r = c.execute('SELECT id FROM suppliers WHERE name=?', (supplier,)).fetchone()
            if r: supplier_id = r[0]
        c.execute('INSERT INTO applications (customer_name, customer_mobile, service_id, service_name, govt_amount, charged_amount, status, payment_received, payment_pending, supplier_id, created_at, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                 (cname, cmobile, None, sname, govt, charged, status, payment_received, payment_pending, supplier_id, created_at, note))
        conn.commit()
        st.success('Application saved')

# ---------- Suppliers & Ledger ----------
elif menu == 'Suppliers & Ledger':
    st.title('Suppliers (Agents)')
    st.subheader('Add Supplier/Agent')
    with st.form('supplier_form'):
        sname = st.text_input('Supplier Name')
        smobile = st.text_input('Mobile')
        stype = st.selectbox('Type', ['Aadhar Agent', 'Birth Agent', 'Other'])
        submitted = st.form_submit_button('Add Supplier')
    if submitted:
        c.execute('INSERT INTO suppliers (name, mobile, type) VALUES (?,?,?)', (sname, smobile, stype))
        conn.commit()
        st.success('Supplier added')

    st.subheader('Supplier Ledger')
    suppliers = c.execute('SELECT * FROM suppliers').fetchall()
    if suppliers:
        sup_names = [s['name'] for s in suppliers]
        sel = st.selectbox('Select Supplier', sup_names)
        srow = next(s for s in suppliers if s['name']==sel)
        with st.form('ledger_form'):
            amt = st.number_input('Amount')
            cd = st.selectbox('Credit or Debit', ['C', 'D'])
            note = st.text_input('Note')
            dt = st.date_input('Date', value=date.today())
            sub = st.form_submit_button('Add Ledger Entry')
        if sub:
            c.execute('INSERT INTO supplier_ledger (supplier_id, amount, credit_or_debit, note, date) VALUES (?,?,?,?,?)', (srow['id'], amt, cd, note, dt.isoformat()))
            conn.commit()
            st.success('Ledger entry added')
        # show ledger
        ledger_df = pd.read_sql_query('SELECT * FROM supplier_ledger WHERE supplier_id=? ORDER BY date DESC', conn, params=(srow['id'],))
        st.dataframe(ledger_df)
    else:
        st.info('No suppliers yet')

# ---------- Expenses ----------
elif menu == 'Expenses':
    st.title('Add Expense')
    with st.form('exp_form'):
        cat = st.selectbox('Category', ['Office Rent', 'Power Bill', 'Water Bill', 'Computer Repair', 'Machinery Repair', 'Staff Salary', 'Food Expenses', 'Other'])
        amt = st.number_input('Amount')
        dt = st.date_input('Date', value=date.today())
        note = st.text_area('Note')
        sub = st.form_submit_button('Add Expense')
    if sub:
        c.execute('INSERT INTO expenses (category, amount, date, note) VALUES (?,?,?,?)', (cat, amt, dt.isoformat(), note))
        conn.commit()
        st.success('Expense added')

    st.subheader('View Expenses')
    edf = pd.read_sql_query('SELECT * FROM expenses ORDER BY date DESC', conn)
    st.dataframe(edf)

# ---------- Services ----------
elif menu == 'Services':
    st.title('Services')
    services_df = pd.read_sql_query('SELECT * FROM services', conn)
    st.dataframe(services_df)
    with st.form('add_service'):
        sname = st.text_input('Service Name')
        amt = st.number_input('Govt Amount (leave 0 or blank for manual)', value=0.0)
        sub = st.form_submit_button('Add Service')
    if sub:
        c.execute('INSERT INTO services (name, govt_amount) VALUES (?,?)', (sname, None if amt==0 else amt))
        conn.commit()
        st.success('Service added')

# ---------- Reports ----------
elif menu == 'Reports':
    st.title('Reports')
    st.write('Date range reports with filters')
    d1 = st.date_input('From', value=date.today())
    d2 = st.date_input('To', value=date.today())
    service_filter = st.selectbox('Service Filter', ['All'] + [r['name'] for r in c.execute('SELECT name FROM services').fetchall()])
    q = 'SELECT * FROM applications WHERE date(created_at) BETWEEN ? AND ?'
    params = (d1.isoformat(), d2.isoformat())
    if service_filter != 'All':
        q = 'SELECT * FROM applications WHERE service_name=? AND date(created_at) BETWEEN ? AND ?'
        params = (service_filter, d1.isoformat(), d2.isoformat())
    df = pd.read_sql_query(q, conn, params=params)
    st.dataframe(df)
    st.markdown('Download CSV')
    csv = df.to_csv(index=False).encode()
    st.download_button('Download CSV', csv, file_name='applications_report.csv')

# ---------- Cash Book ----------
elif menu == 'Cash Book':
    st.title('Cash Book')
    with st.form('cash_form'):
        t = st.selectbox('Type', ['CASH', 'BANK'])
        amt = st.number_input('Amount')
        dt = st.date_input('Date', value=date.today())
        note = st.text_input('Note')
        sub = st.form_submit_button('Record')
    if sub:
        c.execute('INSERT INTO cash_book (type, amount, date, note) VALUES (?,?,?,?)', (t, amt, dt.isoformat(), note))
        conn.commit()
        st.success('Recorded')
    cb = pd.read_sql_query('SELECT * FROM cash_book ORDER BY date DESC', conn)
    st.dataframe(cb)

# ---------- Settings ----------
elif menu == 'Settings':
    st.title('Settings')
    st.write('Admin username is fixed as provided. To change, edit the DB or this file.')
    st.write(f'Logged in as: {st.session_state.username}')
    if st.button('Reset Database (Caution)'):
        st.warning('This will delete data. Not implemented in UI.')

# ---------- Logout ----------
elif menu == 'Logout':
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.experimental_rerun()

# close connection
conn.close()

# EOF
