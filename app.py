import streamlit as st

# -------------------------
# USER CREDENTIALS
# -------------------------
USER_CREDENTIALS = {
    "nani": "Sony@1430",
    "admin": "admin123"
}

# -------------------------
# LOGIN SYSTEM
# -------------------------
def login_screen():
    st.title("🔐 Login Required")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful!")
            st.rerun()  # ✅ fixed (old: st.experimental_rerun)
        else:
            st.error("❌ Invalid username or password")
            st.stop()

# -------------------------
# MAIN APP
# -------------------------
def main_app():
    st.sidebar.success(f"👋 Welcome, {st.session_state.username}")
    st.sidebar.button("Logout", on_click=logout)

    st.title("📊 Nani Associates Tracker")

    st.write("This is your main application after successful login.")
    # 👉 Add your actual app features below
    st.write("✅ App is working fine with the new login system!")

# -------------------------
# LOGOUT FUNCTION
# -------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

# -------------------------
# APP ENTRY POINT
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login_screen()
import pandas as pd
import os
import streamlit as st
from datetime import date

DATA_FILE = "services.csv"

# Load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Service", "Expense", "Income", "Profit", "Remarks"])

# Save data
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Service Entry Form
def service_entry_page():
    st.header("📝 Service Entry Form")

    services = [
        "NEW PAN CARD", "CORRECTION PAN CARD", "THUMB PAN CARD", "GAZZETED PAN CARD",
        "BIRTH CERTIFICATES", "NEW PASSPORT", "MINOR PASSPORT", "REISSUE PASSPORT",
        "DIGITAL SIGNATURE", "NEW AADHAR CARD", "ADDRESS CHANGE", "DATE OF BIRTH CHANGE",
        "NAME CHANGE", "GENDER CHANGE", "NEW VOTER ID", "CORRECTION VOTER ID",
        "AADHAR PRINT", "ONLINE SERVICES"
    ]

    # Inputs
    entry_date = st.date_input("Date", value=date.today())
    service = st.selectbox("Service Type", services)
    expense = st.number_input("Expense (₹)", min_value=0.0, format="%.2f")
    income = st.number_input("Income (₹)", min_value=0.0, format="%.2f")
    remarks = st.text_area("Remarks")

    if st.button("💾 Save Entry"):
        profit = income - expense
        df = load_data()
        new_entry = {"Date": entry_date, "Service": service, "Expense": expense, "Income": income, "Profit": profit, "Remarks": remarks}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Entry saved successfully!")
        import streamlit as st
import pandas as pd
import os
from datetime import date

# ====== FILE SETTINGS ======
DATA_FILE = "services.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Service", "Expense", "Income", "Profit", "Remarks"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ====== PAGE 1: Service Entry ======
def service_entry_page():
    st.header("📝 Service Entry Form")

    services = [
        "NEW PAN CARD", "CORRECTION PAN CARD", "THUMB PAN CARD", "GAZZETED PAN CARD",
        "BIRTH CERTIFICATES", "NEW PASSPORT", "MINOR PASSPORT", "REISSUE PASSPORT",
        "DIGITAL SIGNATURE", "NEW AADHAR CARD", "ADDRESS CHANGE", "DATE OF BIRTH CHANGE",
        "NAME CHANGE", "GENDER CHANGE", "NEW VOTER ID", "CORRECTION VOTER ID",
        "AADHAR PRINT", "ONLINE SERVICES"
    ]

    # Inputs
    entry_date = st.date_input("Date", value=date.today())
    service = st.selectbox("Service Type", services)
    expense = st.number_input("Expense (₹)", min_value=0.0, format="%.2f")
    income = st.number_input("Income (₹)", min_value=0.0, format="%.2f")
    remarks = st.text_area("Remarks")

    if st.button("💾 Save Entry"):
        profit = income - expense
        df = load_data()
        new_entry = {
            "Date": entry_date,
            "Service": service,
            "Expense": expense,
            "Income": income,
            "Profit": profit,
            "Remarks": remarks
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Entry saved successfully!")

    # Show entries
    st.subheader("📊 All Service Entries")
    df = load_data()
    st.dataframe(df)

# ====== PAGE 2: Reports ======
def reports_page():
    st.header("📈 Reports - Daily / Weekly / Monthly")

    df = load_data()
    if df.empty:
        st.warning("No data available yet.")
        return

    df["Date"] = pd.to_datetime(df["Date"])

    # Filters
    report_type = st.selectbox("Select Report Type", ["Daily", "Weekly", "Monthly"])
    
    if report_type == "Daily":
        grouped = df.groupby("Date").sum(numeric_only=True)
    elif report_type == "Weekly":
        grouped = df.groupby(df["Date"].dt.to_period("W")).sum(numeric_only=True)
    else:
        grouped = df.groupby(df["Date"].dt.to_period("M")).sum(numeric_only=True)

    st.subheader(f"{report_type} Summary")
    st.write(grouped[["Expense", "Income", "Profit"]])

    st.bar_chart(grouped[["Expense", "Income", "Profit"]])

# ====== MAIN APP ======
def main():
    st.title("🏢 Nani Associates Business Tracker")

    menu = ["Service Entry", "Reports"]
    choice = st.sidebar.radio("📂 Menu", menu)

    if choice == "Service Entry":
        service_entry_page()
    elif choice == "Reports":
        reports_page()

if __name__ == "__main__":
    main()


    # Show entries
    st.subheader("📊 All Service Entries")
    df = load_data()
    st.dataframe(df)
