import streamlit as st
import pandas as pd
from utils import load_data

def reports_page():
    st.title("📊 Reports")

    df = load_data()
    if df.empty:
        st.warning("No data available!")
        return

    # Date filter
    st.subheader("📅 Filter by Date")
    start_date = st.date_input("Start Date", df["Date"].min())
    end_date = st.date_input("End Date", df["Date"].max())

    if start_date > end_date:
        st.error("Start date must be before end date")
        return

    filtered = df[(df["Date"] >= str(start_date)) & (df["Date"] <= str(end_date))]

    # Show table
    st.subheader("📑 Filtered Records")
    st.dataframe(filtered)

    # Summary
    st.subheader("💰 Summary")
    total_income = filtered["Income"].sum()
    total_expense = filtered["Expense"].sum()
    profit = total_income - total_expense

    st.write(f"**Total Income:** ₹{total_income}")
    st.write(f"**Total Expense:** ₹{total_expense}")
    st.write(f"**Net Profit:** ₹{profit}")
