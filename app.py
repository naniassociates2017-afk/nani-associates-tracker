import streamlit as st
import pandas as pd
from datetime import date

# ---------------------------
# Initialize session state
# ---------------------------
if "services" not in st.session_state:
    st.session_state.services = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "suppliers" not in st.session_state:
    st.session_state.suppliers = []


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
        entry_date = st.date_input("Date", value=date.today())
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
                str(entry_date), customer, service_name, applications,
                govt_amt, paid_amt, profit_amt
            ])
            st.success("Service added successfully!")

    st.write("### All Service Entries")
    df = to_df(st.session_state.services,
               ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])

    for i, row in df.iterrows():
        cols = st.columns([6, 1, 1])
        cols[0].write(row.to_dict())
        if cols[1].button("✏️ Edit", key=f"edit_service_{i}"):
            with st.form(f"edit_service_form_{i}"):
                new_date = st.date_input("Date", value=pd.to_datetime(row["Date"]))
                new_customer = st.text_input("Customer", value=row["Customer"])
                new_service = st.text_input("Service", value=row["Service"])
                new_apps = st.number_input("Applications", value=int(row["Applications"]), step=1)
                new_govt = st.number_input("Govt Amt", value=float(row["Govt Amt"]))
                new_paid = st.number_input("Paid Amt", value=float(row["Paid Amt"]))
                new_profit = new_paid - new_govt
                save = st.form_submit_button("Save Changes")
                if save:
                    st.session_state.services[i] = [str(new_date), new_customer, new_service,
                                                    new_apps, new_govt, new_paid, new_profit]
                    st.success("Service updated!")
                    st.experimental_rerun()
        if cols[2].button("🗑️ Delete", key=f"delete_service_{i}"):
            st.session_state.services.pop(i)
            st.warning("Service deleted!")
            st.experimental_rerun()


def page_expense_entry():
    st.header("💰 Expense Entry")

    with st.form("expense_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        expense_type = st.selectbox("Expense Type", [
            "Salaries", "Office Rent", "Power Bill", "Water Bill",
            "Stationary", "Printing Bill", "Furniture Repair", "Food", "Other"
        ])
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Expense")

        if submit and amount > 0:
            st.session_state.expenses.append([
                str(entry_date), expense_type, amount
            ])
            st.success("Expense added successfully!")

    st.write("### All Expenses")
    df = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    for i, row in df.iterrows():
        cols = st.columns([6, 1, 1])
        cols[0].write(row.to_dict())
        if cols[1].button("✏️ Edit", key=f"edit_expense_{i}"):
            with st.form(f"edit_expense_form_{i}"):
                new_date = st.date_input("Date", value=pd.to_datetime(row["Date"]))
                new_expense = st.text_input("Expense", value=row["Expense"])
                new_amt = st.number_input("Amount", value=float(row["Amount"]))
                save = st.form_submit_button("Save Changes")
                if save:
                    st.session_state.expenses[i] = [str(new_date), new_expense, new_amt]
                    st.success("Expense updated!")
                    st.experimental_rerun()
        if cols[2].button("🗑️ Delete", key=f"delete_expense_{i}"):
            st.session_state.expenses.pop(i)
            st.warning("Expense deleted!")
            st.experimental_rerun()


def page_reports():
    st.header("📊 Reports")

    df_services = to_df(st.session_state.services,
                        ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])
    df_expenses = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

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
    today = str(date.today())
    df_today = df[df["Date"] == today]
    st.write(f"### Services logged for {today}")
    st.dataframe(df_today)


def page_transactions():
    st.header("💳 Agent/Customer Transactions")

    name = st.text_input("Search by Name")
    df = to_df(st.session_state.services,
               ["Date", "Customer", "Service", "Applications", "Govt Amt", "Paid Amt", "Profit Amt"])

    if name:
        filtered = df[df["Customer"].str.contains(name, case=False, na=False)]
        st.dataframe(filtered)
    else:
        st.dataframe(df)


def page_suppliers():
    st.header("🏢 Suppliers")

    with st.form("supplier_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        supplier = st.text_input("Supplier Name")
        service = st.text_input("Service Type")
        paid = st.number_input("Paid Amount", min_value=0.0, step=100.0)
        pending = st.number_input("Pending Amount", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Supplier")

        if submit and supplier:
            st.session_state.suppliers.append([
                str(entry_date), supplier, service, paid, pending
            ])
            st.success("Supplier added successfully!")

    st.write("### All Suppliers")
    df = to_df(st.session_state.suppliers,
               ["Date", "Supplier", "Service", "Paid Amt", "Pending Amt"])

    for i, row in df.iterrows():
        cols = st.columns([6, 1, 1])
        cols[0].write(row.to_dict())
        if cols[1].button("✏️ Edit", key=f"edit_supplier_{i}"):
            with st.form(f"edit_supplier_form_{i}"):
                new_date = st.date_input("Date", value=pd.to_datetime(row["Date"]))
                new_supplier = st.text_input("Supplier", value=row["Supplier"])
                new_service = st.text_input("Service", value=row["Service"])
                new_paid = st.number_input("Paid Amt", value=float(row["Paid Amt"]))
                new_pending = st.number_input("Pending Amt", value=float(row["Pending Amt"]))
                save = st.form_submit_button("Save Changes")
                if save:
                    st.session_state.suppliers[i] = [str(new_date), new_supplier, new_service, new_paid, new_pending]
                    st.success("Supplier updated!")
                    st.experimental_rerun()
        if cols[2].button("🗑️ Delete", key=f"delete_supplier_{i}"):
            st.session_state.suppliers.pop(i)
            st.warning("Supplier deleted!")
            st.experimental_rerun()


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
