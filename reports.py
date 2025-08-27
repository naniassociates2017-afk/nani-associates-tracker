import streamlit as st
import pandas as pd
from utils import load_data

def reports_page():
    st.header("📊 Reports")

    df = load_data()
    if df.empty:
        st.info("No data available yet.")
        return

    df["Date"] = pd.to_datetime(df["Date"])
    df["Net Cash"] = df["Amount Received"] - df["Expense"]

    # Daily balances
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

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income (₹)", f"{total_income:,.2f}")
    col2.metric("Total Expense (₹)", f"{total_expense:,.2f}")
    col3.metric("Total Received (₹)", f"{total_received:,.2f}")

    col4, col5 = st.columns(2)
    col4.metric("Total Pending (₹)", f"{total_pending:,.2f}")
    col5.metric("Closing Balance (₹)", f"{closing_balance:,.2f}")
