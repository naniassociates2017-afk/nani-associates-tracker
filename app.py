import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ------------------
# File paths
# ------------------
FILES = {
    "users": "users.csv",
    "services": "services.csv",
    "transactions": "transactions.csv",
    "suppliers": "suppliers.csv",
    "expenses": "expenses.csv"
}

# ------------------
# Helper functions
# ------------------
def load_csv(path, columns):
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=columns)
    return df

def save_csv(df, path):
    df.to_csv(path, index=False)

# ------------------
# Login Page
# ------------------
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        df_users = load_csv(FILES["users"], ["user","password"])
        user_match = df_users[(df_users["user"]==username) & (df_users["password"]==password)]
        if not user_match.empty:
            st.session_state["user"] = username
            st.success(f"Logged in as {username}")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# ------------------
# Dashboard
# ------------------
def dashboard():
    user = st.session_state["user"]
    st.title(f"Dashboard - {user}")

    # Load data
    df_svc = load_csv(FILES["services"], ["id","date","user","service_type","amount","paid_amt","payment_status","payment_type"])
    df_txn = load_csv(FILES["transactions"], ["id","date","user","product","amount","paid_amt","payment_status","payment_type"])
    df_sup = load_csv(FILES["suppliers"], ["id","name","paid_amt","pending_amt"])
    df_exp = load_csv(FILES["expenses"], ["id","date","user","category","amount","notes"])

    df_svc_user = df_svc[df_svc["user"]==user]
    df_txn_user = df_txn[df_txn["user"]==user]
    df_exp_user = df_exp[df_exp["user"]==user]

    # Payment Status Summary
    st.subheader("Payment Status Summary")
    def payment_summary(df):
        pending = df[df['payment_status']=='Pending']['amount'].sum()
        paid = df[df['payment_status']=='Paid']['paid_amt'].sum()
        partial = df[df['payment_status']=='Partial']['paid_amt'].sum()
        return pending, paid, partial

    svc_pending, svc_paid, svc_partial = payment_summary(df_svc_user)
    txn_pending, txn_paid, txn_partial = payment_summary(df_txn_user)

    st.markdown(f"""
| Type | Pending | Paid | Partial |
|------|--------|------|---------|
| Services | {svc_pending} | {svc_paid} | {svc_partial} |
| Transactions | {txn_pending} | {txn_paid} | {txn_partial} |
""", unsafe_allow_html=True)

    # Product/Service Charts
    st.subheader("Service & Product Flow Charts")

    if not df_svc_user.empty:
        svc_daily = df_svc_user.groupby('date')['amount'].sum()
        svc_daily.plot(kind='bar', title='Daily Service Amounts')
        st.pyplot(plt)
        plt.clf()

    if not df_txn_user.empty:
        txn_daily = df_txn_user.groupby('date')['amount'].sum()
        txn_daily.plot(kind='bar', title='Daily Transaction Amounts', color='orange')
        st.pyplot(plt)
        plt.clf()

    # Profit & Loss
    st.subheader("💰 Profit & Loss Statement")
    total_revenue = df_svc_user['paid_amt'].sum() + df_txn_user['paid_amt'].sum()
    total_expenses = df_exp_user['amount'].sum() + df_sup['paid_amt'].sum()
    profit = total_revenue - total_expenses

    st.markdown(f"""
| Metric | Amount (₹) |
|--------|------------|
| Total Revenue | {total_revenue} |
| Total Expenses | {total_expenses} |
| **Profit / Loss** | **{profit}** |
""", unsafe_allow_html=True)

    pl_chart_data = pd.DataFrame({
        "Category":["Revenue","Expenses","Profit"],
        "Amount":[total_revenue,total_expenses,profit]
    })
    fig, ax = plt.subplots()
    ax.bar(pl_chart_data['Category'], pl_chart_data['Amount'], color=["green","red","blue"])
    ax.set_title("Profit & Loss Overview")
    st.pyplot(fig)

# ------------------
# Main
# ------------------
def main():
    if "user" not in st.session_state:
        login_page()
    else:
        dashboard()

if __name__ == '__main__':
    main()
