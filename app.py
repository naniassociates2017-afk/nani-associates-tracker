import streamlit as st
import pandas as pd
from datetime import date, datetime

# ---------------------------
# Initialize session state
# ---------------------------
if "services" not in st.session_state:
    st.session_state.services = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "suppliers" not in st.session_state:
    st.session_state.suppliers = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = True  # fake login for now


# ---------------------------
# Helpers
# ---------------------------
def to_df(data, columns):
    if not data:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(data, columns=columns)


# ---------------------------
# Pages
# ---------------------------
def page_service_entry():
    st.header("📝 Service Entry")

    with st.form("service_form", clear_on_submit=True):
        customer = st.text_input("Customer / Agent Name")
        service_name = st.selectbox("Service", ["PAN", "Passport", "Aadhaar", "Birth Certificate", "Other"])
        applications = st.number_input("No. of Applications", min_value=1, step=1)
        govt_amt = st.number_input("Govt Amount", min_value=0.0, step=50.0)
        paid_amt = st.number_input("Paid Amount", min_value=0.0, step=50.0)
        profit_amt = paid_amt - govt_amt
        st.write(f"✅ Profit = {profit_amt}")
        submit = st.form_submit_button("Add Service")

        if submit and customer:
            st.session_state.services.append([
                date.today().strftime("%Y-%m-%d"),
                customer, service_name, applications,
                govt_amt, paid_amt, profit_amt
            ])
            st.success("Service added successfully!")

    df = to_df(st.session_state.services,
               ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    st.write("### All Service Entries")
    st.dataframe(df)


def page_expense_entry():
    st.header("💰 Expense Entry")

    with st.form("expense_form", clear_on_submit=True):
        expense_type = st.selectbox("Expense Type", [
            "Salaries", "Office Rent", "Power Bill", "Water Bill",
            "Stationary", "Printing Bill", "Furniture Repair", "Food", "Other"
        ])
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Expense")

        if submit and amount > 0:
            st.session_state.expenses.append([
                date.today().strftime("%Y-%m-%d"),
                expense_type, amount
            ])
            st.success("Expense added successfully!")

    df = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])
    st.write("### All Expenses")
    st.dataframe(df)


def page_reports():
    st.header("📊 Reports")

    df_services = to_df(st.session_state.services,
                        ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    df_expenses = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    # Filters
    filter_type = st.selectbox("Filter By", ["Daily", "Weekly", "Monthly", "All"])
    today = date.today()

    if filter_type == "Daily":
        df_services = df_services[df_services["Date"] == today.strftime("%Y-%m-%d")]
        df_expenses = df_expenses[df_expenses["Date"] == today.strftime("%Y-%m-%d")]
    elif filter_type == "Weekly":
        week_start = today - pd.to_timedelta(today.weekday(), unit="d")
        df_services["Date"] = pd.to_datetime(df_services["Date"])
        df_expenses["Date"] = pd.to_datetime(df_expenses["Date"])
        df_services = df_services[df_services["Date"] >= week_start]
        df_expenses = df_expenses[df_expenses["Date"] >= week_start]
    elif filter_type == "Monthly":
        df_services["Date"] = pd.to_datetime(df_services["Date"])
        df_expenses["Date"] = pd.to_datetime(df_expenses["Date"])
        df_services = df_services[df_services["Date"].dt.month == today.month]
        df_expenses = df_expenses[df_expenses["Date"].dt.month == today.month]

    # Totals
    total_income = df_services["Paid Amt"].sum() if not df_services.empty else 0
    total_expenses = df_expenses["Amount"].sum() if not df_expenses.empty else 0
    profit_loss = total_income - total_expenses

    st.metric("Total Income", f"₹{total_income:,.2f}")
    st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
    st.metric("Profit / Loss", f"₹{profit_loss:,.2f}")

    st.subheader("Service Details")
    st.dataframe(df_services)

    st.subheader("Expense Details")
    st.dataframe(df_expenses)


def page_daily_logger():
    st.header("📅 Daily Data Logger")
    df = to_df(st.session_state.services,
               ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    today = date.today().strftime("%Y-%m-%d")
    df_today = df[df["Date"] == today]
    st.write(f"### Services logged for {today}")
    st.dataframe(df_today)


def page_transactions():
    st.header("💳 Agent/Customer Transactions")

    name = st.text_input("Search by Name")
    status = st.selectbox("Status", ["Paid", "Pending", "Partial"])

    df = to_df(st.session_state.services,
               ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])

    if not name and not df.empty:
        st.dataframe(df)
    else:
        filtered = df[df["Customer"].str.contains(name, case=False, na=False)]
        st.dataframe(filtered)


def page_suppliers():
    st.header("🏢 Suppliers")

    with st.form("supplier_form", clear_on_submit=True):
        supplier = st.text_input("Supplier Name")
        service = st.text_input("Service Type")
        paid = st.number_input("Paid Amount", min_value=0.0, step=100.0)
        pending = st.number_input("Pending Amount", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Supplier")

        if submit and supplier:
            st.session_state.suppliers.append([
                supplier, service, paid, pending
            ])
            st.success("Supplier added successfully!")

    df = to_df(st.session_state.suppliers,
               ["Supplier", "Service", "Paid Amt", "Pending Amt"])
    st.write("### All Suppliers")
    st.dataframe(df)


def page_balances():
    st.header("💵 Balances")

    df_services = to_df(st.session_state.services,
                        ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    df_expenses = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    total_income = df_services["Paid Amt"].sum() if not df_services.empty else 0
    total_govt = df_services["Govt Amt"].sum() if not df_services.empty else 0
    total_profit = df_services["Profit Amt"].sum() if not df_services.empty else 0
    total_expenses = df_expenses["Amount"].sum() if not df_expenses.empty else 0

    cash_in_hand = total_income - total_expenses

    st.metric("Cash in Hand", f"₹{cash_in_hand:,.2f}")
    st.metric("Total Govt Amount", f"₹{total_govt:,.2f}")
    st.metric("Total Profit", f"₹{total_profit:,.2f}")


def page_logout():
    st.session_state.logged_in = False
    st.success("You have been logged out.")
    st.rerun()


# ---------------------------
# Main Layout
# ---------------------------
def main():
    st.sidebar.title("📌 Menu")
    menu = st.sidebar.radio("Select", [
        "Service Entry", "Expense Entry", "Reports", "Daily Data Logger",
        "Agent/Customer Transactions", "Suppliers", "Balances", "Logout"
    ])

    if menu == "Service Entry":
        page_service_entry()
    elif menu == "Expense Entry":
        page_expense_entry()
    elif menu == "Reports":
        page_reports()
    elif menu == "Daily Data Logger":
        page_daily_logger()
    elif menu == "Agent/Customer Transactions":
        page_transactions()
    elif menu == "Suppliers":
        page_suppliers()
    elif menu == "Balances":
        page_balances()
    elif menu == "Logout":
        page_logout()


if __name__ == "__main__":
    main()
