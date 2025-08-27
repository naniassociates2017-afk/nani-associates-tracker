import streamlit as st
import pandas as pd
import datetime

# --- Simple Login Setup ---
USER_CREDENTIALS = {
    "admin": "admin123",    # Owner
    "staff1": "staffpass",  # Staff member 1
    "staff2": "staffpass2"  # Staff member 2
}

# --- Login Form ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login Required")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# --- Business Tracker App ---
st.title("📊 NANI ASSOCIATES Business Tracker")

# Initialize session state for data
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# Transaction Form
with st.form("transaction_form"):
    service = st.selectbox("Service", ["PAN Card", "Passport", "Aadhar Card", "Digital Signature", "Other Online Service"])
    income = st.number_input("Income (₹)", min_value=0.0, step=10.0)
    expense = st.number_input("Expense (₹)", min_value=0.0, step=10.0)
    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        st.session_state.transactions.append({
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "service": service,
            "income": income,
            "expense": expense,
            "profit_loss": income - expense
        })
        st.success("Transaction added successfully!")

# Display Data
if st.session_state.transactions:
    df = pd.DataFrame(st.session_state.transactions)
    st.subheader("📅 Daily Transactions")
    st.dataframe(df)

    # Summary
    st.subheader("📈 Summary")
    total_income = df["income"].sum()
    total_expense = df["expense"].sum()
    total_profit = df["profit_loss"].sum()
    st.write(f"**Total Income:** ₹{total_income}")
    st.write(f"**Total Expenses:** ₹{total_expense}")
    st.write(f"**Net Profit/Loss:** ₹{total_profit}")

    # Export Option
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Transactions as CSV", csv, "transactions.csv", "text/csv")
