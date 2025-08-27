import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------------------
# Initialize session state
# ----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin123"}  # default login
if "services" not in st.session_state:
    st.session_state.services = []
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# ----------------------------
# Login Function
# ----------------------------
def login():
    st.sidebar.subheader("🔑 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in st.session_state.users and st.session_state.users[username] == passwor
