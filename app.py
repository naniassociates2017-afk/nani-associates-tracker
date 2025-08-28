import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ======================
# INITIALIZATION
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "services" not in st.session_state:
    st.session_state.services = pd.DataFrame(
        columns=["ID", "Date", "Customer/Agent", "Service", "No. of Apps", "Govt Amt", "Paid Amt", "Profit Amt"]
    )

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(
        columns=["ID", "Date", "Expense Name", "Amount"]
    )

if "service_id" not in st.session_state:
    st.session_state.service_id = 1

if "expense_id" not in st.session_state:
    st.session_state.expense_id = 1

# ======================
# LOGIN PAGE
# ======================
def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
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

    customer = st.text_input("Customer / Agent Name")
    service = st.selectbox("Select Service", service_list)
    num_apps = st.number_input("Number of Applications", min_value=1, step=1, value=1)
    govt_amt = st.number_input("Government Amount (per application)", min_value=0.0, step=1.0)
    paid_amt = st.number_input("Customer Paid Amount (per application)", min_value=0.0, step=1.0)

    total_govt = govt_amt * num_apps
    total_paid = paid_amt * num_apps
    profit_amt = total_paid - total_govt

    st.write(f"💰 Total Profit: **{profit_amt}**")

    if st.button("Save Service Entry"):
        new_entry = {
            "ID": st.session_state.service_id,
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Customer/Agent": customer,
            "Service": service,
            "No. of Apps": num_apps,
            "Govt Amt": total_govt,
            "Paid Amt": total_paid,
            "Profit Amt": profit_amt,
        }
        st.session_state.services = pd.concat(
            [st.session_state.services, pd.DataFrame([new_entry])],
            ignore_index=True,
        )
        st.session_state.service_id += 1
        st.success("✅ Service entry saved successfully!")

    st.subheader("📋 Saved Services")
    if not st.session_state.services.empty:
        st.dataframe(st.session_state.services)

        edit_id = st.number_input("Enter Service ID to Edit/Delete", min_value=0, step=1)
        if edit_id in st.session_state.services["ID"].values:
            if st.button("✏️ Edit Service Entry"):
                st.info("Re-enter above details to update. Old entry removed.")
                st.session_state.services = st.session_state.services[st.session_state.services["ID"] != edit_id]

            if st.button("🗑️ Delete Service Entry"):
                st.session_state.services = st.session_state.services[st.session_state.services["ID"] != edit_id]
                st.success("✅ Entry deleted!")

# ======================
# EXPENSE ENTRY
# ======================
def expense_entry():
    st.header("💰 Expense Entry")

    expense_name = st.text_input("Expense Name")
    expense_amt = st.number_input("Expense Amount", min_value=0.0, step=1.0)

    if st.button("Save Expense"):
        new_expense = {
            "ID": st.session_state.expense_id,
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Expense Name": expense_name,
            "Amount": expense_amt,
        }
        st.session_state.expenses = pd.concat(
            [st.session_state.expenses, pd.DataFrame([new_expense])],
            ignore_index=True,
        )
        st.session_state.expense_id += 1
        st.success("✅ Expense saved successfully!")

    st.subheader("📋 Saved Expenses")
    if not st.session_state.expenses.empty:
        st.dataframe(st.session_state.expenses)

        edit_id = st.number_input("Enter Expense ID to Edit/Delete", min_value=0, step=1, key="exp_edit")
        if edit_id in st.session_state.expenses["ID"].values:
            if st.button("✏️ Edit Expense"):
                st.info("Re-enter above details to update. Old entry removed.")
                st.session_state.expenses = st.session_state.expenses[st.session_state.expenses["ID"] != edit_id]

            if st.button("🗑️ Delete Expense"):
                st.session_state.expenses = st.session_state.expenses[st.session_state.expenses["ID"] != edit_id]
                st.success("✅ Expense deleted!")

# ======================
# REPORTS
# ======================
def reports():
    st.header("📊 Reports")

    filter_type = st.radio("Filter by", ["All", "Daily", "Weekly", "Monthly"])
    today = datetime.today()

    df_services = st.session_state.services.copy()
    df_services["Date"] = pd.to_datetime(df_services["Date"])

    df_expenses = st.session_state.expenses.copy()
    df_expenses["Date"] = pd.to_datetime(df_expenses["Date"])

    if filter_type == "Daily":
        df_services = df_services[df_services["Date"] == today.normalize()]
        df_expenses = df_expenses[df_expenses["Date"] == today.normalize()]
    elif filter_type == "Weekly":
        week_ago = today - timedelta(days=7)
        df_services = df_services[df_services["Date"] >= week_ago]
        df_expenses = df_expenses[df_expenses["Date"] >= week_ago]
    elif filter_type == "Monthly":
        month_ago = today - timedelta(days=30)
        df_services = df_services[df_services["Date"] >= month_ago]
        df_expenses = df_expenses[df_expenses["Date"] >= month_ago]

    st.subheader("Services Summary")
    st.dataframe(df_services)

    st.subheader("Expenses Summary")
    st.dataframe(df_expenses)

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
