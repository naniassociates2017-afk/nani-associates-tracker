import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------
# LOGIN SYSTEM
# ---------------------------
USER_CREDENTIALS = {"admin": "admin123"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Logged in successfully")
        else:
            st.error("❌ Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""

# ---------------------------
# DATA STORAGE
# ---------------------------
if "services" not in st.session_state:
    st.session_state.services = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "suppliers" not in st.session_state:
    st.session_state.suppliers = []

if "balances" not in st.session_state:
    st.session_state.balances = {"opening": 0, "closing": 0, "cash_in_hand": 0, "cash_at_bank": 0}

# ---------------------------
# APP MAIN MENU
# ---------------------------
def app():
    st.sidebar.title("📌 Menu")
    menu = st.sidebar.radio("Navigate", 
                            ["Service Entry", "Expense Entry", "Reports", 
                             "Daily Data Logger", "Agents/Customers", "Suppliers", 
                             "Balances"])

    st.sidebar.button("Logout", on_click=logout)

    if menu == "Service Entry":
        service_entry()
    elif menu == "Expense Entry":
        expense_entry()
    elif menu == "Reports":
        reports()
    elif menu == "Daily Data Logger":
        daily_data()
    elif menu == "Agents/Customers":
        agents_customers()
    elif menu == "Suppliers":
        suppliers()
    elif menu == "Balances":
        balances()

# ---------------------------
# SERVICE ENTRY
# ---------------------------
def service_entry():
    st.header("📝 Service Entry")

    services_list = [
        "NEW PAN CARD", "CORRECTION PAN CARD", "NEW PASSPORT", "RENEWAL PASSPORT",
        "DIGITAL SIGNATURE", "VOTER ID", "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
        "ADDRESS CHANGE IN AADHAR CARD", "DATE OF BIRTH CHANGE IN AADHAR CARD",
        "AADHAR CARD PRINT", "OTHER ONLINE SERVICES"
    ]

    service_type = st.selectbox("Select Service", services_list)
    govt_amount = st.number_input("Government Amount (₹)", min_value=0)
    paid_amount = st.number_input("Paid by Customer (₹)", min_value=0)
    profit = paid_amount - govt_amount
    st.write(f"💰 Profit: ₹{profit}")

    customer_name = st.text_input("Customer / Agent Name")
    status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"])

    if st.button("Add Service Entry"):
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "service": service_type,
            "govt_amount": govt_amount,
            "paid_amount": paid_amount,
            "profit": profit,
            "customer": customer_name,
            "status": status
        }
        st.session_state.services.append(entry)
        st.success("✅ Service Entry Added!")

    if st.session_state.services:
        df = pd.DataFrame(st.session_state.services)
        st.subheader("📊 Service Records")
        st.dataframe(df)

# ---------------------------
# EXPENSE ENTRY
# ---------------------------
def expense_entry():
    st.header("💸 Expense Entry")
    exp_name = st.text_input("Expense Name")
    exp_amount = st.number_input("Expense Amount (₹)", min_value=0)
    if st.button("Add Expense"):
        entry = {"date": datetime.now().strftime("%Y-%m-%d"), "expense": exp_name, "amount": exp_amount}
        st.session_state.expenses.append(entry)
        st.success("✅ Expense Added!")

    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        st.subheader("📊 Expenses Records")
        st.dataframe(df)

# ---------------------------
# REPORTS
# ---------------------------
def reports():
    st.header("📈 Reports")
    period = st.selectbox("Select Report Period", ["Daily", "Weekly", "Monthly", "All Time"])
    today = datetime.now().date()

    if st.session_state.services:
        df = pd.DataFrame(st.session_state.services)
        df["date"] = pd.to_datetime(df["date"])

        if period == "Daily":
            df = df[df["date"].dt.date == today]
        elif period == "Weekly":
            df = df[df["date"].dt.date >= today - timedelta(days=7)]
        elif period == "Monthly":
            df = df[df["date"].dt.date >= today - timedelta(days=30)]

        st.subheader("🧾 Service Report")
        st.dataframe(df)

        st.write(f"Total Revenue: ₹{df['paid_amount'].sum()}")
        st.write(f"Total Government Amount: ₹{df['govt_amount'].sum()}")
        st.write(f"Total Profit: ₹{df['profit'].sum()}")

# ---------------------------
# DAILY DATA LOGGER
# ---------------------------
def daily_data():
    st.header("📅 Daily Data Logger")
    if st.session_state.services:
        df = pd.DataFrame(st.session_state.services)
        df["date"] = pd.to_datetime(df["date"])
        daily = df.groupby(df["date"].dt.date).sum(numeric_only=True)
        st.dataframe(daily)

# ---------------------------
# AGENTS / CUSTOMERS
# ---------------------------
def agents_customers():
    st.header("🤝 Agents / Customers Transactions")
    name = st.text_input("Agent / Customer Name")
    amount = st.number_input("Transaction Amount", min_value=0)
    status = st.selectbox("Status", ["Paid", "Pending", "Partial"])

    if st.button("Add Transaction"):
        st.session_state.transactions.append({"name": name, "amount": amount, "status": status})
        st.success("✅ Transaction Added!")

    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        st.subheader("📊 Transaction Records")
        st.dataframe(df)

# ---------------------------
# SUPPLIERS
# ---------------------------
def suppliers():
    st.header("🏭 Suppliers")
    supplier_name = st.text_input("Supplier Name")
    service_received = st.text_input("Service Received")
    balance = st.number_input("Balance Amount", min_value=0)

    if st.button("Add Supplier Record"):
        st.session_state.suppliers.append({"supplier": supplier_name, "service": service_received, "balance": balance})
        st.success("✅ Supplier Record Added!")

    if st.session_state.suppliers:
        df = pd.DataFrame(st.session_state.suppliers)
        st.subheader("📊 Supplier Records")
        st.dataframe(df)

# ---------------------------
# BALANCES
# ---------------------------
def balances():
    st.header("💵 Balances")
    opening = st.number_input("Opening Balance", min_value=0, value=st.session_state.balances["opening"])
    closing = st.number_input("Closing Balance", min_value=0, value=st.session_state.balances["closing"])
    cash_hand = st.number_input("Cash in Hand", min_value=0, value=st.session_state.balances["cash_in_hand"])
    cash_bank = st.number_input("Cash at Bank", min_value=0, value=st.session_state.balances["cash_at_bank"])

    if st.button("Update Balances"):
        st.session_state.balances = {"opening": opening, "closing": closing, "cash_in_hand": cash_hand, "cash_at_bank": cash_bank}
        st.success("✅ Balances Updated!")

    st.write(st.session_state.balances)

# ---------------------------
# RUN APP
# ---------------------------
if not st.session_state.logged_in:
    login()
else:
    app()
