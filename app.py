import streamlit as st
import pandas as pd
import datetime

# ---------------- SESSION STATE INIT ----------------
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin123"}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "services" not in st.session_state:
    st.session_state.services = []
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "suppliers" not in st.session_state:
    st.session_state.suppliers = []

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in st.session_state.users and st.session_state.users[username] == password:
            st.session_state.logged_in = True
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.logged_in = False
    st.success("✅ Logged out successfully")
    st.rerun()

# ---------------- SERVICE ENTRY ----------------
def page_service_entry():
    st.header("📝 Service Entry")

    with st.form("service_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.date.today())
        customer = st.text_input("Customer / Agent")
        service = st.selectbox("Service", [
            "NEW PAN CARD", "CORRECTION PAN CARD", "NEW PASSPORT", "RENEWAL PASSPORT",
            "DIGITAL SIGNATURE", "VOTER ID", "NEW AADHAR CARD", "NAME CHANGE AADHAR",
            "ADDRESS CHANGE AADHAR", "DOB CHANGE AADHAR", "AADHAR PRINT", "OTHER SERVICES"
        ])
        applications = st.number_input("No. of Applications", min_value=1, step=1)
        govt_amt = st.number_input("Government Amount", min_value=0.0, step=10.0)
        paid_amt = st.number_input("Paid Amount", min_value=0.0, step=10.0)
        profit = paid_amt - govt_amt

        submitted = st.form_submit_button("➕ Add Service")
        if submitted:
            st.session_state.services.append({
                "Date": date, "Customer": customer, "Service": service,
                "Applications": applications, "Govt Amt": govt_amt,
                "Paid Amt": paid_amt, "Profit": profit
            })
            st.success("✅ Service Added")

    if st.session_state.services:
        df = pd.DataFrame(st.session_state.services)
        st.dataframe(df)

# ---------------- EXPENSE ENTRY ----------------
def page_expense_entry():
    st.header("💰 Expense Entry")

    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.date.today())
        category = st.selectbox("Expense Type", [
            "Salaries", "Office Rent", "Power Bill", "Stationery",
            "Water Bills", "Furniture Repair", "Food", "Printing Bill", "Other"
        ])
        amount = st.number_input("Amount", min_value=0.0, step=50.0)

        submitted = st.form_submit_button("➕ Add Expense")
        if submitted:
            st.session_state.expenses.append({"Date": date, "Category": category, "Amount": amount})
            st.success("✅ Expense Added")

    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        st.dataframe(df)

# ---------------- REPORTS ----------------
def page_reports():
    st.header("📊 Reports")
    option = st.radio("Choose Report", ["Daily", "Weekly", "Monthly", "Profit & Loss"])

    df_services = pd.DataFrame(st.session_state.services)
    df_exp = pd.DataFrame(st.session_state.expenses)

    if option == "Daily":
        today = datetime.date.today()
        st.write("### Today's Report")
        st.write(df_services[df_services["Date"] == today])

    elif option == "Weekly":
        today = datetime.date.today()
        week = today - datetime.timedelta(days=7)
        st.write("### Weekly Report")
        st.write(df_services[df_services["Date"] >= week])

    elif option == "Monthly":
        today = datetime.date.today()
        month = today - datetime.timedelta(days=30)
        st.write("### Monthly Report")
        st.write(df_services[df_services["Date"] >= month])

    elif option == "Profit & Loss":
        total_income = sum([s["Paid Amt"] for s in st.session_state.services])
        total_exp = sum([e["Amount"] for e in st.session_state.expenses])
        profit = total_income - total_exp
        st.metric("Total Income", f"₹{total_income}")
        st.metric("Total Expenses", f"₹{total_exp}")
        st.metric("Net Profit", f"₹{profit}")

# ---------------- TRANSACTIONS ----------------
def page_transactions():
    st.header("💳 Agent/Customer Transactions")
    name = st.text_input("Search by Name")
    status = st.selectbox("Status", ["All", "Paid", "Pending", "Partial"])

    df = pd.DataFrame(st.session_state.transactions)
    if not df.empty:
        if name:
            df = df[df["Name"].str.contains(name, case=False)]
        if status != "All":
            df = df[df["Status"] == status]
        st.dataframe(df)

# ---------------- SUPPLIERS ----------------
def page_suppliers():
    st.header("🏢 Suppliers")
    with st.form("suppliers_form", clear_on_submit=True):
        name = st.text_input("Supplier Name")
        service = st.text_input("Service Provided")
        paid = st.number_input("Paid Amount", min_value=0.0, step=100.0)
        pending = st.number_input("Pending Amount", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("➕ Add Supplier")
        if submitted:
            st.session_state.suppliers.append({
                "Supplier": name, "Service": service,
                "Paid": paid, "Pending": pending
            })
            st.success("✅ Supplier Added")

    if st.session_state.suppliers:
        df = pd.DataFrame(st.session_state.suppliers)
        st.dataframe(df)

# ---------------- BALANCES ----------------
def page_balances():
    st.header("💵 Balances")
    total_govt = sum([s["Govt Amt"] for s in st.session_state.services])
    total_paid = sum([s["Paid Amt"] for s in st.session_state.services])
    total_profit = sum([s["Profit"] for s in st.session_state.services])
    total_exp = sum([e["Amount"] for e in st.session_state.expenses])

    cash_in_hand = total_paid - total_exp

    st.metric("Govt Amount", f"₹{total_govt}")
    st.metric("Paid Amount", f"₹{total_paid}")
    st.metric("Profit", f"₹{total_profit}")
    st.metric("Cash in Hand", f"₹{cash_in_hand}")

# ---------------- MAIN ----------------
def main():
    if not st.session_state.logged_in:
        login()
        return

    st.sidebar.title("⏰ Menu")
    menu = st.sidebar.radio("Select", [
        "Service Entry", "Expense Entry", "Reports",
        "Daily Data Logger", "Agent/Customer Transactions",
        "Suppliers", "Balances", "Logout"
    ])

    if menu == "Service Entry":
        page_service_entry()
    elif menu == "Expense Entry":
        page_expense_entry()
    elif menu == "Reports":
        page_reports()
    elif menu == "Daily Data Logger":
        st.write("📖 Daily Data Logger (to be expanded)...")
        st.dataframe(pd.DataFrame(st.session_state.services))
    elif menu == "Agent/Customer Transactions":
        page_transactions()
    elif menu == "Suppliers":
        page_suppliers()
    elif menu == "Balances":
        page_balances()
    elif menu == "Logout":
        logout()

if __name__ == "__main__":
    main()
