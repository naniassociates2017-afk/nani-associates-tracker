import streamlit as st
import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime

# -----------------------------
# 🔑 User Authentication
# -----------------------------
USERS = {
    "admin": "admin123",
    "agent1": "agent123",
    "agent2": "agent456",
}

def login_page():
    st.title("🔑 Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success(f"✅ Welcome, {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

# -----------------------------
# 📂 Data storage setup
# -----------------------------
DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

FILES = {
    "services": DATA_FOLDER / "services.csv",
    "suppliers": DATA_FOLDER / "suppliers.csv",
    "expenses": DATA_FOLDER / "expenses.csv",
    "cash": DATA_FOLDER / "cash.csv",
}

def load_csv(file, cols):
    if file.exists():
        df = pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=cols)
    return df

def save_csv(file, df):
    df.to_csv(file, index=False)

# -----------------------------
# 📊 Dashboard
# -----------------------------
def dashboard_summary():
    st.header("📊 Dashboard Summary")

    if FILES["services"].exists():
        df = pd.read_csv(FILES["services"])
        if not df.empty:
            df["govt_amt"] = pd.to_numeric(df["govt_amt"], errors="coerce").fillna(0)
            df["paid_amt"] = pd.to_numeric(df["paid_amt"], errors="coerce").fillna(0)
            df["profit_amt"] = df["paid_amt"] - df["govt_amt"]

            total_govt = df["govt_amt"].sum()
            total_paid = df["paid_amt"].sum()
            total_profit = df["profit_amt"].sum()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Govt Amount", f"₹{total_govt:,.2f}")
            col2.metric("Total Paid Amount", f"₹{total_paid:,.2f}")
            col3.metric("Total Profit", f"₹{total_profit:,.2f}")

            st.subheader("📂 Transaction-wise Profit")
            st.dataframe(df[["date","customer","agent","govt_amt","paid_amt","profit_amt","status"]].style.format({
                "govt_amt": "₹{:.2f}",
                "paid_amt": "₹{:.2f}",
                "profit_amt": "₹{:.2f}"
            }))
        else:
            st.info("No service data available yet.")
    else:
        st.info("No service data available yet.")

# -----------------------------
# 📝 Service Entry
# -----------------------------
def service_entry_page():
    st.header("📝 Service Entry")

    df = load_csv(FILES["services"], ["id","date","customer","agent","govt_amt","paid_amt","profit_amt","status","notes"])

    with st.form("service_form"):
        date = st.date_input("Date", datetime.today())
        customer = st.text_input("Customer Name")
        agent = st.text_input("Agent Name")
        govt_amt = st.number_input("Govt Amount", min_value=0.0, format="%.2f")
        paid_amt = st.number_input("Paid Amount", min_value=0.0, format="%.2f")
        profit_amt = paid_amt - govt_amt
        status = st.selectbox("Status", ["Pending", "Partial", "Paid"])
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save Service Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
                "date": str(date),
                "customer": customer,
                "agent": agent,
                "govt_amt": round(govt_amt, 2),
                "paid_amt": round(paid_amt, 2),
                "profit_amt": round(profit_amt, 2),
                "status": status,
                "notes": notes,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(FILES["services"], df)
            st.success("✅ Service entry saved!")

    if not df.empty:
        st.subheader("📂 Service Records")
        with st.expander("Customer / Agent History"):
            st.dataframe(df[["date","customer","agent","status"]])

        with st.expander("Paid Amounts"):
            st.dataframe(df[["date","customer","govt_amt","paid_amt"]].style.format("₹{:.2f}"))

        with st.expander("Profit Summary"):
            st.dataframe(df[["date","customer","profit_amt"]].style.format("₹{:.2f}"))

# -----------------------------
# 🏢 Suppliers Entry
# -----------------------------
def suppliers_entry_page():
    st.header("🏢 Suppliers Entry")
    df = load_csv(FILES["suppliers"], ["id","date","supplier","amount","notes"])

    with st.form("supplier_form"):
        date = st.date_input("Date", datetime.today(), key="sup_date")
        supplier = st.text_input("Supplier Name")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="sup_amt")
        notes = st.text_area("Notes", key="sup_notes")
        submitted = st.form_submit_button("Save Supplier Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
                "date": str(date),
                "supplier": supplier,
                "amount": round(amount, 2),
                "notes": notes,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(FILES["suppliers"], df)
            st.success("✅ Supplier entry saved!")

    if not df.empty:
        st.dataframe(df.style.format({"amount": "₹{:.2f}"}))

# -----------------------------
# 💸 Expenses Entry
# -----------------------------
def expenses_entry_page():
    st.header("💸 Expenses Entry")
    df = load_csv(FILES["expenses"], ["id","date","category","amount","notes"])

    with st.form("expense_form"):
        date = st.date_input("Date", datetime.today(), key="exp_date")
        category = st.text_input("Expense Category")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="exp_amt")
        notes = st.text_area("Notes", key="exp_notes")
        submitted = st.form_submit_button("Save Expense Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
                "date": str(date),
                "category": category,
                "amount": round(amount, 2),
                "notes": notes,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(FILES["expenses"], df)
            st.success("✅ Expense entry saved!")

    if not df.empty:
        st.dataframe(df.style.format({"amount": "₹{:.2f}"}))

# -----------------------------
# 💰 Cash Entry
# -----------------------------
def cash_entry_page():
    st.header("💰 Cash Entry")
    df = load_csv(FILES["cash"], ["id","date","source","amount","notes"])

    with st.form("cash_form"):
        date = st.date_input("Date", datetime.today(), key="cash_date")
        source = st.text_input("Cash Source")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="cash_amt")
        notes = st.text_area("Notes", key="cash_notes")
        submitted = st.form_submit_button("Save Cash Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
                "date": str(date),
                "source": source,
                "amount": round(amount, 2),
                "notes": notes,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(FILES["cash"], df)
            st.success("✅ Cash entry saved!")

    if not df.empty:
        st.dataframe(df.style.format({"amount": "₹{:.2f}"}))

# -----------------------------
# 🚀 Main Navigation
# -----------------------------
st.set_page_config(page_title="Nani Associates App", layout="wide")

st.sidebar.title("📌 Navigation")
st.sidebar.write(f"👤 Logged in as: {st.session_state['user']}")
page = st.sidebar.radio("Go to", ["Dashboard", "Service Entry", "Suppliers Entry", "Expenses Entry", "Cash Entry"])

if page == "Dashboard":
    dashboard_summary()
elif page == "Service Entry":
    service_entry_page()
elif page == "Suppliers Entry":
    suppliers_entry_page()
elif page == "Expenses Entry":
    expenses_entry_page()
elif page == "Cash Entry":
    cash_entry_page()
