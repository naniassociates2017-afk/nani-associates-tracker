import streamlit as st
import pandas as pd
from utils import load_data, save_data

OFFICE_EXPENSES = [
    "Office Rent", "Salaries", "Power Bill", "Water Bill",
    "Stationery", "Repairs", "Food", "Miscellaneous"
]

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
