import streamlit as st
import pandas as pd
from datetime import datetime

# -------------------------------
# Helper Functions
# -------------------------------
def to_df(data_list):
    """Convert list of dicts to Pandas DataFrame safely"""
    if not data_list:
        return pd.DataFrame()
    return pd.DataFrame(data_list)

def render_table_with_actions(df, key_prefix, state_key):
    if df.empty:
        st.info("No records found.")
        return
    for i, row in df.iterrows():
        cols = st.columns(len(df.columns) + 2)
        for j, col in enumerate(df.columns):
            cols[j].write(row[col])
        if cols[-2].button("✏️ Edit", key=f"{key_prefix}_edit_{i}"):
            st.session_state[f"edit_{state_key}"] = i
        if cols[-1].button("🗑️ Delete", key=f"{key_prefix}_del_{i}"):
            st.session_state[state_key].pop(i)
            st.experimental_rerun()

def init_session_state():
    defaults = {
        "services": [], "expenses": [], "transactions": [],
        "suppliers": [], "logged_in": False, "user": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# -------------------------------
# Login Page
# -------------------------------
def login():
    st.title("🔐 Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "admin":
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success("✅ Login successful")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username/password")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.experimental_rerun()

# -------------------------------
# Service Entry
# -------------------------------
def page_service_entry():
    st.subheader("📝 Service Entry")
    with st.form("service_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.today())
        customer = st.text_input("Customer / Agent")
        service = st.selectbox("Service", [
            "NEW PAN CARD", "CORRECTION PAN CARD", "NEW PASSPORT", "RENEWAL PASSPORT",
            "DIGITAL SIGNATURE", "VOTER ID", "NEW AADHAR CARD",
            "NAME CHANGE AADHAR CARD", "ADDRESS CHANGE IN AADHAR CARD",
            "DATE OF BIRTH CHANGE IN AADHAR CARD", "AADHAR CARD PRINT", "OTHER ONLINE SERVICES"
        ])
        applications = st.number_input("No. of Applications", min_value=1, value=1)
        govt_amt = st.number_input("Govt Amount", min_value=0.0, value=0.0)
        paid_amt = st.number_input("Paid Amount", min_value=0.0, value=0.0)
        profit = paid_amt - govt_amt
        submitted = st.form_submit_button("Add Service")
        if submitted:
            st.session_state.services.append({
                "Date": str(date), "Customer": customer, "Service": service,
                "Applications": applications, "Govt Amt": govt_amt,
                "Paid Amt": paid_amt, "Profit": profit
            })
            st.success("✅ Service added")

    st.markdown("### 📋 Service Records")
    render_table_with_actions(to_df(st.session_state.services), "Service", "services")

# -------------------------------
# Expense Entry
# -------------------------------
def page_expense_entry():
    st.subheader("💰 Expense Entry")
    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.today())
        expense_type = st.selectbox("Expense Type", [
            "Salary", "Office Rent", "Power Bill", "Stationary", "Water Bill",
            "Furniture Repair", "Food", "Printing Bill", "Other"
        ])
        amount = st.number_input("Amount", min_value=0.0, value=0.0)
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            st.session_state.expenses.append({
                "Date": str(date), "Expense Type": expense_type, "Amount": amount
            })
            st.success("✅ Expense added")

    st.markdown("### 📋 Expense Records")
    render_table_with_actions(to_df(st.session_state.expenses), "Expense", "expenses")

# -------------------------------
# Reports
# -------------------------------
def page_reports():
    st.subheader("📊 Reports")
    df_services = to_df(st.session_state.services)
    df_expenses = to_df(st.session_state.expenses)
    if not df_services.empty:
        st.markdown("#### Service Report")
        st.dataframe(df_services)
        st.write("**Total Paid:**", df_services["Paid Amt"].sum())
        st.write("**Total Govt Amt:**", df_services["Govt Amt"].sum())
        st.write("**Total Profit:**", df_services["Profit"].sum())
    if not df_expenses.empty:
        st.markdown("#### Expense Report")
        st.dataframe(df_expenses)
        st.write("**Total Expenses:**", df_expenses["Amount"].sum())

# -------------------------------
# Daily Data Logger
# -------------------------------
def page_daily_logger():
    st.subheader("📅 Daily Data Logger")
    df = to_df(st.session_state.services)
    if not df.empty:
        grouped = df.groupby("Date").sum(numeric_only=True)[["Govt Amt", "Paid Amt", "Profit"]]
        st.dataframe(grouped)

# -------------------------------
# Agent/Customer Transactions
# -------------------------------
def page_transactions():
    st.subheader("🤝 Agent/Customer Transactions")
    df = to_df(st.session_state.services)
    if df.empty:
        st.info("No transactions found")
    else:
        name = st.text_input("Search by Customer/Agent")
        if name:
            df = df[df["Customer"].str.contains(name, case=False, na=False)]
        st.dataframe(df)

# -------------------------------
# Suppliers
# -------------------------------
def page_suppliers():
    st.subheader("🚚 Suppliers")
    with st.form("supplier_form", clear_on_submit=True):
        name = st.text_input("Supplier Name")
        service = st.text_input("Service Provided")
        paid = st.number_input("Paid Amount", min_value=0.0, value=0.0)
        pending = st.number_input("Pending Amount", min_value=0.0, value=0.0)
        submitted = st.form_submit_button("Add Supplier")
        if submitted:
            st.session_state.suppliers.append({
                "Supplier": name, "Service": service, "Paid": paid, "Pending": pending
            })
            st.success("✅ Supplier added")

    st.markdown("### 📋 Supplier Records")
    render_table_with_actions(to_df(st.session_state.suppliers), "Supplier", "suppliers")

# -------------------------------
# Balances & Profit/Loss
# -------------------------------
def page_balances():
    st.subheader("💵 Balances & Profit/Loss")
    df_s = to_df(st.session_state.services)
    df_e = to_df(st.session_state.expenses)
    total_paid = df_s["Paid Amt"].sum() if not df_s.empty else 0
    total_govt = df_s["Govt Amt"].sum() if not df_s.empty else 0
    total_profit = df_s["Profit"].sum() if not df_s.empty else 0
    total_expenses = df_e["Amount"].sum() if not df_e.empty else 0
    net_profit = total_profit - total_expenses
    st.write("**Cash In Hand:**", total_paid - total_govt - total_expenses)
    st.write("**Total Govt Amt:**", total_govt)
    st.write("**Total Profit:**", total_profit)
    st.write("**Total Expenses:**", total_expenses)
    st.write("**Net Profit/Loss:**", net_profit)

# -------------------------------
# Main
# -------------------------------
def main():
    init_session_state()
    if not st.session_state.logged_in:
        login()
    else:
        with st.sidebar:
            st.title("⏰ Menu")
            choice = st.radio("Select", [
                "Service Entry", "Expense Entry", "Reports",
                "Daily Data Logger", "Agent/Customer Transactions",
                "Suppliers", "Balances", "Logout"
            ])
        if choice == "Service Entry":
            page_service_entry()
        elif choice == "Expense Entry":
            page_expense_entry()
        elif choice == "Reports":
            page_reports()
        elif choice == "Daily Data Logger":
            page_daily_logger()
        elif choice == "Agent/Customer Transactions":
            page_transactions()
        elif choice == "Suppliers":
            page_suppliers()
        elif choice == "Balances":
            page_balances()
        elif choice == "Logout":
            logout()

if __name__ == "__main__":
    main()
