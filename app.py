import streamlit as st
from service_entry import service_entry_page
from expense_entry import expense_entry_page
from reports import reports_page

def main():
    st.title("📊 NANI ASSOCIATES BUSINESS TRACKER")

    menu = ["Service Entry", "Expense Entry", "Reports"]
    choice = st.sidebar.radio("📂 Menu", menu)

    if choice == "Service Entry":
        service_entry_page()
    elif choice == "Expense Entry":
        expense_entry_page()
    elif choice == "Reports":
        reports_page()

if __name__ == "__main__":
    main()
elif page == "View Transactions":
    st.header("All Transactions")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    # Agent filter
    agents = df["agent"].unique().tolist()
    agents.sort()
    selected_agent = st.selectbox("Select Agent", ["All"] + agents)

    if selected_agent != "All":
        df = df[df["agent"] == selected_agent]

    st.dataframe(df)

    # Optional: show totals for the filtered data
    total_amount = df["amount"].sum()
    st.write(f"**Total Amount: {total_amount}**")

# Suppliers Table
c.execute("""
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
import streamlit as st
import pandas as pd
import sqlite3

# --- Database connection ---
conn = sqlite3.connect("services.db", check_same_thread=False)
c = conn.cursor()

# --- Create Tables ---
c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    application_no TEXT,
    product TEXT,
    supplier TEXT,
    amount REAL NOT NULL,
    type TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# --- Login System ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")

    if login_btn:
        if username == "admin" and password == "admin123":  # change as needed
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")

# --- Main App ---
if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    page = st.sidebar.selectbox(
        "Navigation",
        ["Add Transaction", "View Transactions", "Manage Suppliers"]
    )

    # ---------------- Add Transaction Page ----------------
    if page == "Add Transaction":
        st.header("Add Transaction")
elif page == "View Transactions":
    st.header("Transactions Report")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    if df.empty:
        st.warning("No transactions found yet.")
    else:
        df["date"] = pd.to_datetime(df["date"])

        # --- Filters ---
        agents = df["agent"].dropna().unique().tolist()
        agents.sort()
        selected_agent = st.selectbox("Select Agent", ["All"] + agents)
        if selected_agent != "All":
            df = df[df["agent"] == selected_agent]

        products = df["product"].dropna().unique().tolist()
        products.sort()
        selected_product = st.selectbox("Select Product", ["All"] + products)
        if selected_product != "All":
            df = df[df["product"] == selected_product]

        suppliers = df["supplier"].dropna().unique().tolist()
        suppliers.sort()
        selected_supplier = st.selectbox("Select Supplier", ["All"] + suppliers)
        if selected_supplier != "All":
            df = df[df["supplier"] == selected_supplier]

        # --- Application Number Search ---
        search_app = st.text_input("Search by Application Number")
        if search_app:
            df = df[df["application_no"].str.contains(search_app, case=False, na=False)]

        # --- Period Selection ---
        period = st.radio("Select Period", ["Daily", "Weekly", "Monthly"])

        if period == "Daily":
            report = df.groupby(df["date"].dt.date).agg({"amount": "sum"}).reset_index()
            report.rename(columns={"date": "Date", "amount": "Total Amount"}, inplace=True)
        elif period == "Weekly":
            report = df.groupby(df["date"].dt.to_period("W")).agg({"amount": "sum"}).reset_index()
            report["date"] = report["date"].astype(str)
            report.rename(columns={"date": "Week", "amount": "Total Amount"}, inplace=True)
        elif period == "Monthly":
            report = df.groupby(df["date"].dt.to_period("M")).agg({"amount": "sum"}).reset_index()
            report["date"] = report["date"].astype(str)
            report.rename(columns={"date": "Month", "amount": "Total Amount"}, inplace=True)

        # --- Show Table ---
        st.subheader(f"{period} Summary")
        st.dataframe(report)

        st.write(f"**Total Amount: {df['amount'].sum()}**")

        # --- Chart ---
        st.subheader(f"{period} Chart")
        st.bar_chart(report.set_index(report.columns[0]))




