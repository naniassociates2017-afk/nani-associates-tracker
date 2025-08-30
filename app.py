import streamlit as st
import pandas as pd
import uuid
from pathlib import Path

# -----------------------------
# Setup folders and files
# -----------------------------
DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

FILES = {
    "services": DATA_FOLDER / "services.csv",
    "suppliers": DATA_FOLDER / "suppliers.csv",
    "expenses": DATA_FOLDER / "expenses.csv",
    "cash": DATA_FOLDER / "cash.csv",
}

# -----------------------------
# Helper functions
# -----------------------------
def load_csv(file, cols):
    if file.exists():
        df = pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=cols)
    return df

def save_csv(file, df):
    df.to_csv(file, index=False)

# -----------------------------
# Dashboard Summary
# -----------------------------
def dashboard_summary():
    st.header("📊 Dashboard Summary")

    if FILES["services"].exists():
        df = pd.read_csv(FILES["services"])
        if not df.empty:
            df["govt_amt"] = pd.to_numeric(df["govt_amt"], errors="coerce").fillna(0)
            df["paid_amt"] = pd.to_numeric(df["paid_amt"], errors="coerce").fillna(0)
            df["profit_amt"] = pd.to_numeric(df["profit_amt"], errors="coerce").fillna(0)

            total_govt = df["govt_amt"].sum()
            total_paid = df["paid_amt"].sum()
            total_profit = df["profit_amt"].sum()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Govt Amount", f"₹{total_govt:,.2f}")
            col2.metric("Total Paid Amount", f"₹{total_paid:,.2f}")
            col3.metric("Total Profit", f"₹{total_profit:,.2f}")
        else:
            st.info("No service data available yet.")
    else:
        st.info("No service data available yet.")

# -----------------------------
# Service Entry Page
# -----------------------------
def service_entry_page():
    st.header("📝 Service Entry")

    df = load_csv(FILES["services"], ["id","customer","agent","govt_amt","paid_amt","profit_amt","status","notes"])

    with st.form("service_form"):
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
            st.dataframe(df[["customer","agent","status"]])

        with st.expander("Paid Amounts"):
            st.dataframe(df[["customer","govt_amt","paid_amt"]].style.format("₹{:.2f}"))

        with st.expander("Profit Summary"):
            st.dataframe(df[["customer","profit_amt"]].style.format("₹{:.2f}"))

# -----------------------------
# Suppliers Entry Page
# -----------------------------
def suppliers_entry_page():
    st.header("🏢 Suppliers Entry")
    df = load_csv(FILES["suppliers"], ["id","supplier","amount","notes"])

    with st.form("supplier_form"):
        supplier = st.text_input("Supplier Name")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Supplier Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
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
# Expenses Entry Page
# -----------------------------
def expenses_entry_page():
    st.header("💸 Expenses Entry")
    df = load_csv(FILES["expenses"], ["id","category","amount","notes"])

    with st.form("expense_form"):
        category = st.text_input("Expense Category")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Expense Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
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
# Cash Entry Page
# -----------------------------
def cash_entry_page():
    st.header("💰 Cash Entry")
    df = load_csv(FILES["cash"], ["id","source","amount","notes"])

    with st.form("cash_form"):
        source = st.text_input("Cash Source")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Cash Entry")
        if submitted:
            new_row = {
                "id": str(uuid.uuid4()),
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
# Main App
# -----------------------------
st.set_page_config(page_title="Nani Associates App", layout="wide")

st.sidebar.title("📌 Navigation")
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
