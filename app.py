import streamlit as st
import pandas as pd
from datetime import date, datetime

# ---------------------------
# Helper Functions
# ---------------------------
def to_df(data, columns):
    if not data:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(data, columns=columns)

def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "services" not in st.session_state:
        st.session_state.services = []
    if "expenses" not in st.session_state:
        st.session_state.expenses = []
    if "suppliers" not in st.session_state:
        st.session_state.suppliers = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

# ---------------------------
# Pages
# ---------------------------
def page_login():
    st.title("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin":  # Simple check
            st.session_state.logged_in = True
            st.success("Login successful!")
        else:
            st.error("Invalid credentials")

def page_service_entry():
    st.title("📝 Service Entry")
    with st.form("service_form"):
        entry_date = st.date_input("Date", date.today())
        customer = st.text_input("Customer/Agent")
        service = st.selectbox("Service", ["PAN", "Passport", "Aadhaar", "Birth Certificate"])
        applications = st.number_input("No. of Applications", min_value=1, step=1)
        govt_amt = st.number_input("Govt Amt", min_value=0.0, step=1.0)
        paid_amt = st.number_input("Paid Amt", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Save Service Entry")

        if submitted:
            profit_amt = paid_amt - govt_amt
            st.session_state.services.append([
                str(entry_date), customer, service, applications, govt_amt, paid_amt, profit_amt
            ])
            st.success("Service entry saved!")

    df = to_df(st.session_state.services,
               ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    st.subheader("Saved Service Entries")
    st.dataframe(df)

    # Edit / Delete
    if not df.empty:
        row = st.number_input("Row number to Edit/Delete", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Delete Service Entry"):
            st.session_state.services.pop(row)
            st.success("Deleted successfully!")
        if st.button("Edit Service Entry"):
            st.info("Please re-enter details above to overwrite this row.")
            st.session_state.services[row] = [
                str(date.today()), "Edited Customer", "PAN", 1, 100, 120, 20
            ]

def page_expense_entry():
    st.title("💰 Expense Entry")
    with st.form("expense_form"):
        exp_date = st.date_input("Date", date.today())
        expense_type = st.selectbox("Expense Type",
                                    ["Salaries", "Office Rent", "Power Bill", "Stationery",
                                     "Water Bill", "Furniture Repair", "Food", "Printing Bill"])
        amount = st.number_input("Amount", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Save Expense")

        if submitted:
            st.session_state.expenses.append([str(exp_date), expense_type, amount])
            st.success("Expense saved!")

    df = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])
    st.subheader("Saved Expenses")
    st.dataframe(df)

    # Edit / Delete
    if not df.empty:
        row = st.number_input("Row number to Edit/Delete (Expense)", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Delete Expense"):
            st.session_state.expenses.pop(row)
            st.success("Expense deleted!")
        if st.button("Edit Expense"):
            st.session_state.expenses[row] = [str(date.today()), "Edited Expense", 500]
            st.success("Expense edited!")

def page_reports():
    st.title("📊 Reports")
    service_df = to_df(st.session_state.services,
                       ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    exp_df = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    total_income = service_df["Paid Amt"].sum() if not service_df.empty else 0
    total_expenses = exp_df["Amount"].sum() if not exp_df.empty else 0
    profit_loss = total_income - total_expenses

    st.metric("Total Income", f"₹{total_income:.2f}")
    st.metric("Total Expenses", f"₹{total_expenses:.2f}")
    st.metric("Profit / Loss", f"₹{profit_loss:.2f}")

    st.subheader("Service Details")
    st.dataframe(service_df)

    st.subheader("Expense Details")
    st.dataframe(exp_df)

def page_data_logger():
    st.title("📒 Daily Data Logger")
    service_df = to_df(st.session_state.services,
                       ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    if service_df.empty:
        st.info("No service data available yet.")
    else:
        grouped = service_df.groupby(["Date", "Service"]).agg({"Applications": "sum", "Profit Amt": "sum"}).reset_index()
        st.dataframe(grouped)

def page_suppliers():
    st.title("🏭 Suppliers")
    with st.form("supplier_form"):
        name = st.text_input("Supplier Name")
        paid = st.number_input("Paid Amount", min_value=0.0, step=1.0)
        pending = st.number_input("Pending Amount", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Save Supplier")
        if submitted:
            st.session_state.suppliers.append([name, paid, pending])
            st.success("Supplier added!")

    df = to_df(st.session_state.suppliers, ["Supplier", "Paid Amt", "Pending Amt"])
    st.dataframe(df)

    if not df.empty:
        row = st.number_input("Row number to Delete (Supplier)", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Delete Supplier"):
            st.session_state.suppliers.pop(row)
            st.success("Supplier deleted!")

def page_balances():
    st.title("💵 Balances")
    service_df = to_df(st.session_state.services,
                       ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    exp_df = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    govt_amt = service_df["Govt Amt"].sum() if not service_df.empty else 0
    paid_amt = service_df["Paid Amt"].sum() if not service_df.empty else 0
    profit_amt = service_df["Profit Amt"].sum() if not service_df.empty else 0
    total_exp = exp_df["Amount"].sum() if not exp_df.empty else 0

    cash_in_hand = paid_amt - govt_amt - total_exp

    st.metric("Cash in Hand", f"₹{cash_in_hand:.2f}")
    st.metric("Total Govt Amt", f"₹{govt_amt:.2f}")
    st.metric("Total Profit", f"₹{profit_amt:.2f}")

# ---------------------------
# Main
# ---------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES - Tracker", layout="wide")
    init_session()

    if not st.session_state.logged_in:
        page_login()
    else:
        menu = st.sidebar.radio("Select", ["Service Entry", "Expense Entry", "Reports",
                                           "Daily Data Logger", "Suppliers", "Balances", "Logout"])
        if menu == "Service Entry":
            page_service_entry()
        elif menu == "Expense Entry":
            page_expense_entry()
        elif menu == "Reports":
            page_reports()
        elif menu == "Daily Data Logger":
            page_data_logger()
        elif menu == "Suppliers":
            page_suppliers()
        elif menu == "Balances":
            page_balances()
        elif menu == "Logout":
            st.session_state.logged_in = False
            st.success("Logged out!")

if __name__ == "__main__":
    main()
