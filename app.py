import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# -------------------- DATABASE SETUP --------------------
def init_db():
    conn = sqlite3.connect("tracker.db")
    c = conn.cursor()

    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT)""")

    # Service entries
    c.execute("""CREATE TABLE IF NOT EXISTS service_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                customer TEXT,
                service TEXT,
                amount REAL,
                status TEXT,
                remarks TEXT)""")

    # Expense entries
    c.execute("""CREATE TABLE IF NOT EXISTS expense_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                expense_type TEXT,
                amount REAL,
                remarks TEXT)""")

    conn.commit()
    conn.close()


# -------------------- LOGIN --------------------
def login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.sidebar.subheader("🔑 Login")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login", key="login_button"):
            conn = sqlite3.connect("tracker.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            result = c.fetchone()
            conn.close()

            if result:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.sidebar.success(f"Welcome, {username}")
            else:
