import streamlit as st
import pandas as pd
from datetime import date

# ---------------------------
# Session State Initialization
# ---------------------------
if "services" not in st.session_state:
    st.session_state.services = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = True  # you can link this to a login system later

# ---------------------------
# Utility Functions
# ---------------------------
def to_df(data, columns):
    if not data:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(data, columns=columns)

# ---------------------------
# Pages
# ---------------------------
def page_service_entry():
    st.header("Service Entry")

    with st.form("service_form", clear_on_submit=True):
        service_name = st.text_input("Service Name")
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Service")

        if submit and service_name:
            st.session_state.services.append(
                [date.today().strftime("%Y-%m-%d"), service_name, amount]
            )
            st.success("Service added successfully!")

    df_services = to_df(st.session_state.services, ["Date", "Service", "Amount"])
    st.write("### All Services")
    st.dataframe(df_services)


def page_expense_entry():
    st.header("Expense Entry")

    with st.form("expense_form", clear_on_submit=True):
        expense_name = st.text_input("Expense Name")
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        submit = st.form_submit_button("Add Expense")

        if submit and expense_name:
            st.session_state.expenses.append(
                [date.today().strftime("%Y-%m-%d"), expense_name, amount]
            )
            st.success("Expense added successfully!")

    df_expenses = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])
    st.write("### All Expenses")
    st.dataframe(df_expenses)


def page_reports():
    st.header("Reports")

    df_services = to_df(st.session_state.services, ["Date", "Service", "Amount"])
    df_expenses = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    total_income = df_services["Amount"].sum() if not df_services.empty else 0
    total_expenses = df_expenses["Amount"].sum() if not df_expenses.empty else 0
    profit_loss = total_income - total_expenses

    st.metric("Total Income", f"₹{total_income:,.2f}")
    st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
    st.metric("Profit / Loss", f"₹{profit_loss:,.2f}")


def page_transactions():
    st.header("Transactions")

    df_services = to_df(st.session_state.services, ["Date", "Service", "Amount"])
    df_expenses = to_df(st.session_state.expenses, ["Date", "Expense", "Amount"])

    st.subheader("All Services")
    st.dataframe(df_services)

    st.subheader("All Expenses")
    st.dataframe(df_expenses)


def page_logout():
    st.session_state.logged_in = False
    st.success("You have been logged out.")
    st.rerun()

# ---------------------------
# Main App Layout
# ---------------------------
def main():
    st.sidebar.title("Menu")
    choice = st.sidebar.radio(
        "Select",
        ["Service Entry", "Expense Entry", "Reports", "Transactions", "Logout"]
    )

    if choice == "Service Entry":
        page_service_entry()
    elif choice == "Expense Entry":
        page_expense_entry()
    elif choice == "Reports":
        page_reports()
    elif choice == "Transactions":
        page_transactions()
    elif choice == "Logout":
        page_logout()


if __name__ == "__main__":
    main()
