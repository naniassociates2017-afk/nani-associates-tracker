import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# =========================
# SESSION STATE INITIALIZATION
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "services" not in st.session_state:
    st.session_state.services = pd.DataFrame(columns=[
        "ID", "Date", "Customer/Agent", "Service Type", "No. of Applications",
        "Govt Amt", "Paid Amt", "Profit Amt"
    ])
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["ID", "Date", "Expense Name", "Amount"])
if "suppliers" not in st.session_state:
    st.session_state.suppliers = pd.DataFrame(columns=[
        "ID", "Date", "Supplier Name", "Service Type", "Paid Amt", "Pending Amt", "Partial Amt"
    ])
if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=[
        "ID", "Date", "Customer/Agent", "Status", "Amount"
    ])
if "service_id" not in st.session_state:
    st.session_state.service_id = 1
if "expense_id" not in st.session_state:
    st.session_state.expense_id = 1
if "supplier_id" not in st.session_state:
    st.session_state.supplier_id = 1
if "transaction_id" not in st.session_state:
    st.session_state.transaction_id = 1

# =========================
# LOGIN FUNCTION
# =========================
def login():
    st.title("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
        else:
            st.error("❌ Invalid Username or Password")

# =========================
# LOGOUT FUNCTION
# =========================
def logout():
    st.session_state.logged_in = False
    st.success("✅ Logged out successfully!")

# =========================
# SERVICE ENTRY
# =========================
def service_entry():
    st.header("🛠 Service Entry")

    services_list = [
        "New PAN Card", "Correction PAN Card", "New Passport", "Renewal Passport",
        "Digital Signature", "Voter ID", "New Aadhaar Card", "Name Change Aadhaar Card",
        "Address Change Aadhaar Card", "Date of Birth Change Aadhaar Card",
        "Aadhaar Card Print", "Birth Certificate", "Other Online Services"
    ]

    customer = st.text_input("Customer/Agent Name")
    service_type = st.selectbox("Service Type", services_list)
    num_apps = st.number_input("No. of Applications", min_value=1, step=1)
    govt_amt = st.number_input("Govt Amount", min_value=0.0, step=1.0)
    paid_amt = st.number_input("Paid Amount", min_value=0.0, step=1.0)
    profit_amt = paid_amt - govt_amt

    if st.button("Save Service Entry"):
        new_service = {
            "ID": st.session_state.service_id,
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Customer/Agent": customer,
            "Service Type": service_type,
            "No. of Applications": num_apps,
            "Govt Amt": govt_amt,
            "Paid Amt": paid_amt,
            "Profit Amt": profit_amt
        }
        st.session_state.services = pd.concat(
            [st.session_state.services, pd.DataFrame([new_service])],
            ignore_index=True,
        )
        st.session_state.service_id += 1
        st.success("✅ Service Entry saved successfully!")

    st.subheader("📋 Saved Service Entries")
    if not st.session_state.services.empty:
        st.dataframe(st.session_state.services)

        edit_id = st.number_input("Enter Service ID to Edit/Delete", min_value=0, step=1, key="srv_edit")
        if edit_id in st.session_state.services["ID"].values:
            if st.button("✏️ Edit Service"):
                st.info("Re-enter above details to update. Old entry removed.")
                st.session_state.services = st.session_state.services[st.session_state.services["ID"] != edit_id]

            if st.button("🗑️ Delete Service"):
                st.session_state.services = st.session_state.services[st.session_state.services["ID"] != edit_id]
                st.success("✅ Service deleted!")

# =========================
# EXPENSE ENTRY
# =========================
def expense_entry():
    st.header("💰 Expense Entry")

    expense_list = [
        "Salaries", "Office Rent", "Power Bill", "Stationery", "Water Bills",
        "Furniture/Repair", "Food", "Printing Bill", "Other"
    ]

    expense_type = st.selectbox("Select Expense Type", expense_list)
    if expense_type == "Other":
        expense_name = st.text_input("Enter Expense Name")
    else:
        expense_name = expense_type

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

# =========================
# REPORTS
# =========================
def reports():
    st.header("📊 Reports")

    if st.session_state.services.empty and st.session_state.expenses.empty:
        st.info("No data available yet.")
        return

    report_type = st.selectbox("Select Report Type", ["Daily", "Weekly", "Monthly"])
    filter_name = st.text_input("Filter by Customer/Agent")

    today = datetime.today()
    if report_type == "Daily":
        start_date = today - timedelta(days=1)
    elif report_type == "Weekly":
        start_date = today - timedelta(weeks=1)
    else:
        start_date = today - timedelta(days=30)

    filtered_services = st.session_state.services[
        (pd.to_datetime(st.session_state.services["Date"]) >= start_date)
    ]
    filtered_expenses = st.session_state.expenses[
        (pd.to_datetime(st.session_state.expenses["Date"]) >= start_date)
    ]

    if filter_name:
        filtered_services = filtered_services[filtered_services["Customer/Agent"].str.contains(filter_name, case=False)]

    st.subheader("🛠 Service Report")
    st.dataframe(filtered_services)

    st.subheader("💰 Expense Report")
    st.dataframe(filtered_expenses)

    st.subheader("📌 Summary")
    st.write("Total Services Income:", filtered_services["Paid Amt"].sum())
    st.write("Total Govt Amount:", filtered_services["Govt Amt"].sum())
    st.write("Total Profit:", filtered_services["Profit Amt"].sum())
    st.write("Total Expenses:", filtered_expenses["Amount"].sum())

# =========================
# DAILY DATA LOGGER (Placeholder)
# =========================
def daily_logger():
    st.header("📝 Daily Data Logger")
    st.info("🚧 Feature under development...")

# =========================
# AGENT / CUSTOMER TRANSACTIONS
# =========================
def agent_transactions():
    st.header("💼 Agent/Customer Transactions")

    name = st.text_input("Customer/Agent Name")
    status = st.selectbox("Status", ["Paid", "Pending", "Partial"])
    amount = st.number_input("Transaction Amount", min_value=0.0, step=1.0)

    if st.button("Save Transaction"):
        new_txn = {
            "ID": st.session_state.transaction_id,
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Customer/Agent": name,
            "Status": status,
            "Amount": amount,
        }
        st.session_state.transactions = pd.concat(
            [st.session_state.transactions, pd.DataFrame([new_txn])],
            ignore_index=True,
        )
        st.session_state.transaction_id += 1
        st.success("✅ Transaction saved successfully!")

    st.subheader("📋 Transactions")
    search = st.text_input("Search by Customer/Agent")
    filtered_txns = st.session_state.transactions
    if search:
        filtered_txns = filtered_txns[filtered_txns["Customer/Agent"].str.contains(search, case=False)]

    st.dataframe(filtered_txns)

# =========================
# SUPPLIERS
# =========================
def suppliers():
    st.header("🏢 Suppliers")

    supplier_name = st.text_input("Supplier Name")
    service_type = st.selectbox("Service Type", [
        "PAN", "Passport", "Aadhaar", "Birth Certificate", "Other"
    ])
    paid_amt = st.number_input("Paid Amount", min_value=0.0, step=1.0)
    pending_amt = st.number_input("Pending Amount", min_value=0.0, step=1.0)
    partial_amt = st.number_input("Partial Amount", min_value=0.0, step=1.0)

    if st.button("Save Supplier"):
        new_supplier = {
            "ID": st.session_state.supplier_id,
            "Date": datetime.today().strftime("%Y-%m-%d"),
            "Supplier Name": supplier_name,
            "Service Type": service_type,
            "Paid Amt": paid_amt,
            "Pending Amt": pending_amt,
            "Partial Amt": partial_amt,
        }
        st.session_state.suppliers = pd.concat(
            [st.session_state.suppliers, pd.DataFrame([new_supplier])],
            ignore_index=True,
        )
        st.session_state.supplier_id += 1
        st.success("✅ Supplier entry saved!")

    st.subheader("📋 Supplier Data")
    if not st.session_state.suppliers.empty:
        st.dataframe(st.session_state.suppliers)

        edit_id = st.number_input("Enter Supplier ID to Delete", min_value=0, step=1, key="sup_edit")
        if edit_id in st.session_state.suppliers["ID"].values:
            if st.button("🗑️ Delete Supplier"):
                st.session_state.suppliers = st.session_state.suppliers[st.session_state.suppliers["ID"] != edit_id]
                st.success("✅ Supplier deleted!")

# =========================
# BALANCES
# =========================
def balances():
    st.header("💵 Balances")

    total_paid = st.session_state.services["Paid Amt"].sum()
    total_govt = st.session_state.services["Govt Amt"].sum()
    total_profit = st.session_state.services["Profit Amt"].sum()
    total_expenses = st.session_state.expenses["Amount"].sum()

    cash_in_hand = total_paid - total_expenses

    st.write("Total Govt Amount:", total_govt)
    st.write("Total Paid Amount:", total_paid)
    st.write("Total Profit Amount:", total_profit)
    st.write("Total Expenses:", total_expenses)
    st.write("Cash in Hand:", cash_in_hand)

# =========================
# MAIN APP
# =========================
def main():
    if not st.session_state.logged_in:
        login()
    else:
        st.sidebar.title("📌 Menu")
        menu = st.sidebar.radio("Select an option", [
            "Service Entry", "Expense Entry", "Reports",
            "Daily Data Logger", "Agent Transactions",
            "Suppliers", "Balances", "Logout"
        ])

        if menu == "Service Entry":
            service_entry()
        elif menu == "Expense Entry":
            expense_entry()
        elif menu == "Reports":
            reports()
        elif menu == "Daily Data Logger":
            daily_logger()
        elif menu == "Agent Transactions":
            agent_transactions()
        elif menu == "Suppliers":
            suppliers()
        elif menu == "Balances":
            balances()
        elif menu == "Logout":
            logout()

if __name__ == "__main__":
    main()
