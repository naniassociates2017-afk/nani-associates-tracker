import streamlit as st
import pandas as pd
from datetime import datetime

# ======================
# INITIALIZATION
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "services" not in st.session_state:
    st.session_state.services = pd.DataFrame(
        columns=["Date", "Service", "Govt Amt", "Paid Amt", "Profit Amt"]
    )

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(
        columns=["Date", "Expense Name", "Amount"]
    )

# ======================
# LOGIN PAGE
# ======================
def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":  # Change if needed
            st.session_state.logged_in = True
            st.success("✅ Logged in successfully")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ======================
# SERVICE ENTRY
# ======================
def service_entry():
    st.header("📝 Service Entry")

    service_list = [
        "NEW PAN CARD",
        "CORRECTION PAN CARD",
        "NEW PASSPORT",
        "RENEWAL PASSPORT",
        "DIGITAL SIGNATURE",
        "VOTER ID",
        "NEW AADHAR CARD",
        "NAME CHANGE AADHAR CARD",
        "ADDRESS CHANGE IN AADHAR CARD",
        "DATE OF BIRTH CHANGE IN AADHAR CARD",
        "AADHAR CARD PRINT",
        "OTHER ONLINE SERVICES"
    ]

    service = st.selectbox("Select Service", service_list)
    govt_amt = st.number_input("Government Amount", min_value=0.0, step=1.0)
    paid_amt = st.number_input("Customer Paid Amount", min_value=0.0, step=1.0)
    profit_amt = paid_amt - govt_amt

    st.write(f"💰 Profit: **{profit_amt}**")

    if st.button("Save Service Entry"):
        new_entry = {
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Service": service,
            "Govt Amt": govt_amt,
            "Paid Amt": paid_amt,
            "Profit Amt": profit_amt,
        }
        st.session_state.services = pd.concat(
            [st.session_state.services, pd.DataFrame([new_entry])],
            ignore_index=True,
        )
        st.success("✅ Service entry saved successfully!")

    st.subheader("📋 Saved Services")
    st.dataframe(st.session_state.services)

# ======================
# EXPENSE ENTRY
# ======================
def expense_entry():
    st.header("💰 Expense Entry")

    expense_name = st.text_input("Expense Name")
    expense_amt = st.number_input("Expense Amount", min_value=0.0, step=1.0)

    if st.button("Save Expense"):
        new_expense = {
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Expense Name": expense_name,
            "Amount": expense_amt,
        }
        st.session_state.expenses = pd.concat(
            [st.session_state.expenses, pd.DataFrame([new_expense])],
            ignore_index=True,
        )
        st.success("✅ Expense saved successfully!")

    st.subheader("📋 Saved Expenses")
    st.dataframe(st.session_state.expenses)

# ======================
# REPORTS
# ======================
def reports():
    st.header("📊 Reports")

    st.subheader("Services Summary")
    st.dataframe(st.session_state.services)

    st.subheader("Expenses Summary")
    st.dataframe(st.session_state.expenses)

    st.info("📅 You can extend this to show Daily / Weekly / Monthly summaries.")

# ======================
# DAILY DATA LOGGER
# ======================
def daily_data_logger():
    st.header("📅 Daily Data Logger")
    st.info("👉 This section will keep logs of all daily activities.")

# ======================
# AGENT/CUSTOMER TRANSACTIONS
# ======================
def agent_customer_transactions():
    st.header("👥 Agent/Customer Transactions")
    st.info("👉 Here you can manage Paid, Pending, Partial transactions.")

# ======================
# SUPPLIERS
# ======================
def suppliers():
    st.header("📦 Suppliers")
    st.info("👉 Manage suppliers, received services, balance amounts here.")

# ======================
# BALANCES
# ======================
def balances():
    st.header("💵 Balances")

    total_paid = st.session_state.services["Paid Amt"].sum()
    total_govt = st.session_state.services["Govt Amt"].sum()
    total_profit = st.session_state.services["Profit Amt"].sum()
    total_expenses = st.session_state.expenses["Amount"].sum()

    cash_in_hand = total_profit - total_expenses

    st.metric("Total Customer Paid", f"₹ {total_paid}")
    st.metric("Total Government Amount", f"₹ {total_govt}")
    st.metric("Total Profit", f"₹ {total_profit}")
    st.metric("Total Expenses", f"₹ {total_expenses}")
    st.metric("Cash in Hand", f"₹ {cash_in_hand}")

# ======================
# MAIN APP
# ======================
def main_app():
    st.sidebar.title("📌 Menu")
    menu = st.sidebar.radio(
        "Select an option",
        [
            "Service Entry",
            "Expense Entry",
            "Reports",
            "Daily Data Logger",
            "Agent/Customer Transactions",
            "Suppliers",
            "Balances",
        ],
    )

    if menu == "Service Entry":
        service_entry()
    elif menu == "Expense Entry":
        expense_entry()
    elif menu == "Reports":
        reports()
    elif menu == "Daily Data Logger":
        daily_data_logger()
    elif menu == "Agent/Customer Transactions":
        agent_customer_transactions()
    elif menu == "Suppliers":
        suppliers()
    elif menu == "Balances":
        balances()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ======================
# RUN APP
# ======================
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
