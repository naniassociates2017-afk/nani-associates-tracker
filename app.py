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
    CATEGORIES = [
    "NEW PAN CARD", "CORRECTION PAN CARD", "THUMB PAN CARD", "GAZZETED PAN CARD",
    "BIRTH CERTIFICATES", "NEW PASSPORT", "MINOR PASSPORT", "REISSUE PASSPORT",
    "DIGITAL SIGNATURE", "NEW AADHAR CARD", "ADDRESS CHANGE", "DATE OF BIRTH CHANGE",
    "NAME CHANGE", "GENDER CHANGE", "NEW VOTER ID", "CORRECTION VOTER ID",
    "AADHAR PRINT", "ONLINE SERVICES"
]

OFFICE_EXPENSES = [
    "Office Rent", "Salaries", "Power Bill", "Water Bill",
    "Stationery", "Repairs", "Food", "Miscellaneous"
]
def service_entry_page():
    st.header("📝 Service Entry Form")

    date = st.date_input("Date")
    customer = st.text_input("Customer Name")
    service_type = st.selectbox("Service Type", CATEGORIES)
    expense = st.number_input("Expense (₹)", min_value=0.0, step=0.1)
    income = st.number_input("Income (₹)", min_value=0.0, step=0.1)

    payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"])
    amount_received = 0.0
    if payment_status == "Partial":
        amount_received = st.number_input("Amount Received (₹)", min_value=0.0, max_value=income, step=0.1)
    elif payment_status == "Paid":
        amount_received = income

    remarks = st.text_area("Remarks")

    if st.button("Save Service Entry"):
        df = load_data()

        profit = income - expense
        pending = income - amount_received

        new_entry = {
            "Date": str(date),
            "Type": "Service",
            "Customer": customer,
            "Service": service_type,
            "Expense": expense,
            "Income": income,
            "Profit": profit,
            "Payment Status": payment_status,
            "Amount Received": amount_received,
            "Pending Amount": pending,
            "Remarks": remarks
        }

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Service Entry Saved Successfully!")
def expense_entry_page():
    st.header("💰 Office Expense Entry")

    date = st.date_input("Date")
    expense_type = st.selectbox("Expense Category", OFFICE_EXPENSES)
    amount = st.number_input("Amount (₹)", min_value=0.0, step=0.1)
    remarks = st.text_area("Remarks")

    if st.button("Save Expense Entry"):
        df = load_data()

        new_entry = {
            "Date": str(date),
            "Type": "Expense",
            "Customer": "",
            "Service": expense_type,
            "Expense": amount,
            "Income": 0.0,
            "Profit": -amount,
            "Payment Status": "",
            "Amount Received": 0.0,
            "Pending Amount": 0.0,
            "Remarks": remarks
        }

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Expense Entry Saved Successfully!")
def reports_page():
    st.header("📊 Reports")

    df = load_data()
    if df.empty:
        st.info("No data available yet.")
        return

    df["Date"] = pd.to_datetime(df["Date"])

    # Opening & Closing Balance
    df["Net Cash"] = df["Amount Received"] - df["Expense"]
    daily_balance = df.groupby("Date")["Net Cash"].sum().cumsum().reset_index()
    daily_balance.rename(columns={"Net Cash": "Closing Balance"}, inplace=True)
    daily_balance["Opening Balance"] = daily_balance["Closing Balance"].shift(1).fillna(0)

    st.subheader("📅 Daily Balances")
    st.dataframe(daily_balance)

    # Summary
    st.subheader("📑 Summary")
    total_income = df["Income"].sum()
    total_expense = df["Expense"].sum()
    total_received = df["Amount Received"].sum()
    total_pending = df["Pending Amount"].sum()
    closing_balance = daily_balance["Closing Balance"].iloc[-1]

    st.metric("Total Income (₹)", f"{total_income:,.2f}")
    st.metric("Total Expense (₹)", f"{total_expense:,.2f}")
    st.metric("Total Received (₹)", f"{total_received:,.2f}")
    st.metric("Total Pending (₹)", f"{total_pending:,.2f}")
    st.metric("Closing Balance (₹)", f"{closing_balance:,.2f}")
    import streamlit as st
import pandas as pd

# Import your functions
# (we’ll create these below)
from service_entry import service_entry_page
from expense_entry import expense_entry_page
from reports import reports_page

st.sidebar.title("📂 Menu")
menu = st.sidebar.radio("Select Page", ["Service Entry", "Expense Entry", "Reports"])

if menu == "Service Entry":
    service_entry_page()
elif menu == "Expense Entry":
    expense_entry_page()
elif menu == "Reports":
    reports_page()


