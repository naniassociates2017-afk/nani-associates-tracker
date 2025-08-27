import streamlit as st
import pandas as pd
from utils import load_data, save_data

CATEGORIES = [
    "NEW PAN CARD", "CORRECTION PAN CARD", "THUMB PAN CARD", "GAZZETED PAN CARD",
    "BIRTH CERTIFICATES", "NEW PASSPORT", "MINOR PASSPORT", "REISSUE PASSPORT",
    "DIGITAL SIGNATURE", "NEW AADHAR CARD", "ADDRESS CHANGE", "DATE OF BIRTH CHANGE",
    "NAME CHANGE", "GENDER CHANGE", "NEW VOTER ID", "CORRECTION VOTER ID",
    "AADHAR PRINT", "ONLINE SERVICES"
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
