import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------
# Configuration
# ---------------------------
FILE_PATH = "NANI_ASSOCIATES_DAILY_TRACKER.xlsx"
ADMIN_USER = "admin"
ADMIN_PASS = "1234"   # <-- Change this password before using

# ---------------------------
# Load Data
# ---------------------------
def load_data():
    if os.path.exists(FILE_PATH):
        return pd.read_excel(FILE_PATH, sheet_name="Service_Entry")
    else:
        return pd.DataFrame(columns=[
            "Date", "Customer/Agent", "Service",
            "Govt_Amount", "Charged_Amount", "Received_Amount",
            "Supplier_Paid", "Pending_Customer", "Pending_Supplier", "Profit"
        ])

# ---------------------------
# Save Data
# ---------------------------
def save_data(df):
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name="Service_Entry", index=False)

        # Daily Summary
        summary = df.groupby("Date").agg({
            "Charged_Amount": "sum",
            "Received_Amount": "sum",
            "Supplier_Paid": "sum",
            "Pending_Customer": "sum",
            "Pending_Supplier": "sum",
            "Profit": "sum"
        }).reset_index()
        summary.to_excel(writer, sheet_name="Daily_Summary", index=False)

        # Customer Ledger
        cust_ledger = df.groupby("Customer/Agent").agg({
            "Charged_Amount": "sum",
            "Received_Amount": "sum",
            "Pending_Customer": "sum"
        }).reset_index()
        cust_ledger.to_excel(writer, sheet_name="Customer_Ledger", index=False)

        # Supplier Ledger
        supp_ledger = df.groupby("Service").agg({
            "Govt_Amount": "sum",
            "Supplier_Paid": "sum",
            "Pending_Supplier": "sum"
        }).reset_index()
        supp_ledger.to_excel(writer, sheet_name="Supplier_Ledger", index=False)

# ---------------------------
# Login Page
# ---------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 NANI ASSOCIATES - Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.authenticated = True
            st.success("✅ Login successful!")
        else:
            st.error("❌ Invalid username or password")

else:
    # ---------------------------
    # Load or Initialize Data
    # ---------------------------
    if "data" not in st.session_state:
        st.session_state.data = load_data()

    # ---------------------------
    # Sidebar Menu
    # ---------------------------
    st.sidebar.title("NANI ASSOCIATES")
    menu = st.sidebar.radio("Navigation", ["Service Entry", "Daily Summary", "Customer Ledger", "Supplier Ledger", "All Transactions", "Logout"])

    # ---------------------------
    # Service Entry
    # ---------------------------
    if menu == "Service Entry":
        st.header("➕ Add New Service Entry")

        date = st.date_input("Date", datetime.date.today())
        cust = st.text_input("Customer/Agent Name")
        service = st.selectbox("Service", [
            "NEW PANCARD", "CORRECTION PANCARD", "NEW AADHAR CARD",
            "DATE OF BIRTH CHANGE", "NAME CHANGE", "ADDRESS CHANGE",
            "DIGITAL SIGNATURE", "PASSPORT", "RENEWAL PASSPORT",
            "MINOR PASSPORT", "MSME CERTIFICATE", "AADHAR PRINT", "OTHER"
        ])
        govt_amt = st.number_input("Govt. Amount (Supplier Cost)", min_value=0.0, step=10.0)
        charged = st.number_input("Charged Amount", min_value=0.0, step=10.0)
        received = st.number_input("Received Amount", min_value=0.0, step=10.0)
        supplier_paid = st.number_input("Supplier Paid", min_value=0.0, step=10.0)

        if st.button("Save Entry"):
            pending_customer = charged - received
            pending_supplier = govt_amt - supplier_paid
            profit = received - supplier_paid

            new_entry = pd.DataFrame([[
                date, cust, service, govt_amt, charged, received,
                supplier_paid, pending_customer, pending_supplier, profit
            ]], columns=st.session_state.data.columns)

            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            save_data(st.session_state.data)
            st.success("✅ Entry saved to Excel successfully!")

        st.write("### Today's Entries")
        st.dataframe(st.session_state.data[st.session_state.data["Date"] == pd.to_datetime(datetime.date.today())])

    # ---------------------------
    # Daily Summary
    # ---------------------------
    elif menu == "Daily Summary":
        st.header("📊 Daily Summary")
        if not st.session_state.data.empty:
            summary = st.session_state.data.groupby("Date").agg({
                "Charged_Amount": "sum",
                "Received_Amount": "sum",
                "Supplier_Paid": "sum",
                "Pending_Customer": "sum",
                "Pending_Supplier": "sum",
                "Profit": "sum"
            }).reset_index()
            st.dataframe(summary)
        else:
            st.info("No data available yet.")

    # ---------------------------
    # Customer Ledger
    # ---------------------------
    elif menu == "Customer Ledger":
        st.header("📒 Customer/Agent Ledger")
        if not st.session_state.data.empty:
            cust_ledger = st.session_state.data.groupby("Customer/Agent").agg({
                "Charged_Amount": "sum",
                "Received_Amount": "sum",
                "Pending_Customer": "sum"
            }).reset_index()
            st.dataframe(cust_ledger)
        else:
            st.info("No data available yet.")

    # ---------------------------
    # Supplier Ledger
    # ---------------------------
    elif menu == "Supplier Ledger":
        st.header("🏦 Supplier Ledger")
        if not st.session_state.data.empty:
            supp_ledger = st.session_state.data.groupby("Service").agg({
                "Govt_Amount": "sum",
                "Supplier_Paid": "sum",
                "Pending_Supplier": "sum"
            }).reset_index()
            st.dataframe(supp_ledger)
        else:
            st.info("No data available yet.")

    # ---------------------------
    # All Transactions
    # ---------------------------
    elif menu == "All Transactions":
        st.header("🗂️ All Service Entries")
        st.dataframe(st.session_state.data)

    # ---------------------------
    # Logout
    # ---------------------------
    elif menu == "Logout":
        st.session_state.authenticated = False
        st.rerun()
