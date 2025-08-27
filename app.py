import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from utils.db_utils import init_db, add_user, validate_user


# -------------------- LOGIN --------------------
def login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.sidebar.subheader("🔑 Login")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login", key="login_button"):
            if validate_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.sidebar.success(f"Welcome, {username}")
            else:
                st.sidebar.error("Invalid username or password")
    else:
        st.sidebar.success(f"✅ Logged in as {st.session_state['username']}")
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""


# -------------------- SERVICE ENTRY --------------------
def service_entry():
    st.subheader("📝 Service Entry")

    customer = st.text_input("Customer Name")
    service = st.text_input("Service Description")
    amount = st.number_input("Amount", min_value=0.0, step=100.0)
    status = st.selectbox("Payment Status", ["Paid", "Pending"])
    remarks = st.text_area("Remarks")

    if st.button("Save Service Entry"):
        conn = sqlite3.connect("tracker.db")
        c = conn.cursor()
        c.execute("INSERT INTO service_entry (date, customer, service, amount, status, remarks) VALUES (?, ?, ?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d"), customer, service, amount, status, remarks))
        conn.commit()
        conn.close()
        st.success("✅ Service Entry Saved!")


# -------------------- EXPENSE ENTRY --------------------
def expense_entry():
    st.subheader("💰 Expense Entry")

    expense_type = st.selectbox("Expense Type", ["Office Rent", "Salaries", "Power Bill", "Water Bill", "Stationery", "Repairs", "Food", "Other"])
    amount = st.number_input("Amount", min_value=0.0, step=100.0)
    remarks = st.text_area("Remarks")

    if st.button("Save Expense Entry"):
        conn = sqlite3.connect("tracker.db")
        c = conn.cursor()
        c.execute("INSERT INTO expense_entry (date, expense_type, amount, remarks) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d"), expense_type, amount, remarks))
        conn.commit()
        conn.close()
        st.success("✅ Expense Entry Saved!")


# -------------------- REPORTS --------------------
def reports():
    st.subheader("📊 Reports")

    conn = sqlite3.connect("tracker.db")

    # Service entries
    df_service = pd.read_sql("SELECT * FROM service_entry", conn)
    st.write("### Service Entries", df_service)

    # Expense entries
    df_expense = pd.read_sql("SELECT * FROM expense_entry", conn)
    st.write("### Expense Entries", df_expense)

    # Daily summary
    if not df_service.empty or not df_expense.empty:
        st.write("### Daily Summary")

        income = df_service[df_service["status"] == "Paid"]["amount"].sum()
        pending = df_service[df_service["status"] == "Pending"]["amount"].sum()
        expenses = df_expense["amount"].sum()
        balance = income - expenses

        st.metric("💵 Total Income (Paid)", f"{income:.2f}")
        st.metric("⏳ Pending Am
