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
