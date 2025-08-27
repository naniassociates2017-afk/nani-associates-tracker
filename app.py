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
import streamlit as st
import pandas as pd
from utils import load_data, save_data

# Hardcoded login (you can change anytime)
USERS = {"admin": "admin123", "nani": "sony@1430"}

def login():
    st.sidebar.subheader("🔑 Login Required")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if username in USERS and USERS[username] == password:
        st.session_state["logged_in"] = True
        st.success("✅ Login successful")
    else:
        if username and password:
            st.error("❌ Invalid username or password")

def main_app():
    st.sidebar.title("📂 Menu")
    menu = st.sidebar.radio("Select Page", ["Service Entry", "Expense Entry", "Reports", "Backup"])

    if menu == "Backup":
        df = load_data()
        if not df.empty:
            st.download_button("⬇️ Download Backup", df.to_csv(index=False).encode("utf-8"), "backup.csv")
        uploaded = st.file_uploader("Upload Backup CSV")
        if uploaded:
            df = pd.read_csv(uploaded)
            save_data(df)
            st.success("✅ Backup restored successfully!")

# --- Main ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
import streamlit as st
import pandas as pd
from service_entry import service_entry_page
from expense_entry import expense_entry_page
from reports_page import reports_page
from utils import load_data, save_data

# --- Hardcoded login details ---
USERS = {
    "naniassociates": "Sony@1430",
    "admin": "admin123"
}

def login():
    st.sidebar.subheader("🔑 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success(f"✅ Welcome, {username}!")
        else:
            st.error("❌ Invalid Username or Password")

def main_app():
    st.sidebar.title("📂 Menu")
    menu = st.sidebar.radio("Select Page", ["Service Entry", "Expense Entry", "Reports", "Backup"])

    if menu == "Service Entry":
        service_entry_page()
    elif menu == "Expense Entry":
        expense_entry_page()
    elif menu == "Reports":
        reports_page()
    elif menu == "Backup":
        backup_page()

def backup_page():
    st.header("📦 Backup & Restore")

    df = load_data()
    if not df.empty:
        st.download_button(
            "⬇️ Download Backup",
            df.to_csv(index=False).encode("utf-8"),
            "backup.csv",
            "text/csv"
        )

    uploaded = st.file_uploader("Upload Backup CSV")
    if uploaded:
        df = pd.read_csv(uploaded)
        save_data(df)
        st.success("✅ Backup restored successfully!")

# --- Main ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    main_app()

if not st.session_state["logged_in"]:
    login()
else:
    main_app()
