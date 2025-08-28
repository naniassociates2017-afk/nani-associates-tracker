# appy.py
import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
from io import BytesIO
import matplotlib.pyplot as plt

# -------------------------
# Config / Credentials
# -------------------------
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

FILES = {
    "services": os.path.join(DATA_FOLDER, "services.csv"),
    "expenses": os.path.join(DATA_FOLDER, "expenses.csv"),
    "transactions": os.path.join(DATA_FOLDER, "transactions.csv"),
    "suppliers": os.path.join(DATA_FOLDER, "suppliers.csv"),
}

USER_CREDENTIALS = {
    "admin": "admin123",
    "user1": "user123",
    "user2": "user234",
    "mobile": "mobile123",
}

# -------------------------
# Utility Functions
# -------------------------
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return out.getvalue()

def load_csv(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            for c in columns:
                if c not in df.columns:
                    df[c] = ""
            return df[columns]
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def ensure_datafiles_exist():
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    for key, cols in zip(FILES.keys(), [svc_cols, exp_cols, txn_cols, sup_cols]):
        if not os.path.exists(FILES[key]):
            save_csv(pd.DataFrame(columns=cols), FILES[key])

def next_id(df):
    if df.empty:
        return 1
    try:
        return int(df["id"].max()) + 1
    except Exception:
        return len(df) + 1

def filter_date(df, date_col="date", period="Daily"):
    today = date.today()
    df[date_col] = pd.to_datetime(df[date_col])
    if period=="Daily":
        return df[df[date_col].dt.date==today]
    elif period=="Weekly":
        week_ago = today - timedelta(days=7)
        return df[df[date_col].dt.date>=week_ago]
    elif period=="Monthly":
        month_start = today.replace(day=1)
        return df[df[date_col].dt.date>=month_start]
    else:
        return df

# -------------------------
# Session State Init
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "device" not in st.session_state:
    st.session_state.device = None

ensure_datafiles_exist()

# -------------------------
# Authentication
# -------------------------
def login_page():
    st.title("🔐 Login - NANI ASSOCIATES")
    st.write("Use one of the predefined accounts:")
    st.markdown("""
    - **admin / admin123** (desktop)  
    - **user1 / user123** (desktop)  
    - **user2 / user234** (desktop)  
    - **mobile / mobile123** (mobile)
    """)
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username]==password:
                st.session_state.user = username
                st.session_state.device = "mobile" if username=="mobile" else "desktop"
                st.success(f"Logged in as {username}")
            else:
                st.error("Invalid username or password")

def logout():
    st.session_state.user = None
    st.session_state.device = None
    st.success("Logged out")

# -------------------------
# Service Entry
# -------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"]
    df = load_csv(FILES["services"], svc_cols)

    with st.form("svc_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            customer = st.text_input("Customer / Agent")
            service_type = st.selectbox("Service Type", [
                "NEW PAN CARD", "CORRECTION PAN CARD", "NEW PASSPORT", "RENEWAL PASSPORT",
                "DIGITAL SIGNATURE", "VOTER ID", "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
                "ADDRESS CHANGE IN AADHAR CARD", "DATE OF BIRTH CHANGE IN AADHAR CARD",
                "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
            ])
        with c2:
            num_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1)
            govt_amt = st.number_input("Government Amount (per app)", min_value=0.0, value=0.0)
            paid_amt = st.number_input("Paid Amount (per app)", min_value=0.0, value=0.0)
            status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
            notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Service"):
            if not customer:
                st.error("Enter customer / agent name")
            else:
                total_govt = round(num_apps*govt_amt,2)
                total_paid = round(num_apps*paid_amt,2)
                profit = round(total_paid-total_govt,2)
                nid = next_id(df)
                new_row = {
                    "id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"customer":customer,
                    "service_type":service_type,"num_apps":int(num_apps),"govt_amt":total_govt,
                    "paid_amt":total_paid,"profit_amt":profit,"status":status,"notes":notes
                }
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["services"])
                st.success("Service added ✅")

    st.markdown("---")
    st.subheader("Your Services")
    df_user = df[df["user"]==user].sort_values("date", ascending=False)
    st.dataframe(df_user, use_container_width=True)
    st.download_button("⬇️ Download Services CSV", df_user.to_csv(index=False).encode(), f"services_{user}.csv")
    st.download_button("⬇️ Download Services Excel", df_to_excel_bytes(df_user,"Services"), f"services_{user}.xlsx")

# -------------------------
# Expense Entry
# -------------------------
def expense_entry_page():
    st.header("💰 Expense Entry")
    user = st.session_state.user
    exp_cols = ["id","date","user","category","amount","notes"]
    df = load_csv(FILES["expenses"], exp_cols)

    with st.form("exp_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            category = st.text_input("Category")
        with c2:
            amount = st.number_input("Amount", min_value=0.0, value=0.0)
            notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Expense"):
            if not category:
                st.error("Enter expense category")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,
                           "category":category,"amount":amount,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["expenses"])
                st.success("Expense added ✅")

    st.markdown("---")
    st.subheader("Your Expenses")
    df_user = df[df["user"]==user].sort_values("date", ascending=False)
    st.dataframe(df_user, use_container_width=True)
    st.download_button("⬇️ Download Expenses CSV", df_user.to_csv(index=False).encode(), f"expenses_{user}.csv")
    st.download_button("⬇️ Download Expenses Excel", df_to_excel_bytes(df_user,"Expenses"), f"expenses_{user}.xlsx")

# -------------------------
# Transactions Page
# -------------------------
def transactions_page():
    st.header("💳 Transactions")
    user = st.session_state.user
    txn_cols = ["id","date","user","party","service_type","status","amount","notes"]
    df = load_csv(FILES["transactions"], txn_cols)

    with st.form("txn_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            party = st.text_input("Party / Customer")
            service_type = st.selectbox("Service Type", ["NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT","DIGITAL SIGNATURE","VOTER ID"])
        with c2:
            status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
            amount = st.number_input("Amount", min_value=0.0, value=0.0)
            notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Transaction"):
            if not party:
                st.error("Enter party / customer")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,
                           "party":party,"service_type":service_type,"status":status,"amount":amount,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["transactions"])
                st.success("Transaction added ✅")

    st.markdown("---")
    st.subheader("Your Transactions")
    df_user = df[df["user"]==user].sort_values("date", ascending=False)
    st.dataframe(df_user, use_container_width=True)
    st.download_button("⬇️ Download Transactions CSV", df_user.to_csv(index=False).encode(), f"transactions_{user}.csv")
    st.download_button("⬇️ Download Transactions Excel", df_to_excel_bytes(df_user,"Transactions"), f"transactions_{user}.xlsx")

# -------------------------
# Suppliers Page
# -------------------------
def suppliers_page():
    st.header("🏢 Supplier / Partner Entry")
    user = st.session_state.user
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","notes"]
    df = load_csv(FILES["suppliers"], sup_cols)

    with st.form("sup_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            supplier_name = st.text_input("Supplier Name")
            service_type = st.selectbox("Service Type", ["NEW PAN CARD","CORRECTION PAN CARD","NEW PASSPORT","RENEWAL PASSPORT"])
        with c2:
            paid_amt = st.number_input("Paid Amount", min_value=0.0, value=0.0)
            pending_amt = st.number_input("Pending Amount", min_value=0.0, value=0.0)
            partial_amt = st.number_input("Partial Amount", min_value=0.0, value=0.0)
            notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Supplier Entry"):
            if not supplier_name:
                st.error("Enter supplier name")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,
                           "supplier_name":supplier_name,"service_type":service_type,
                           "paid_amt":paid_amt,"pending_amt":pending_amt,"partial_amt":partial_amt,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["suppliers"])
                st.success("Supplier entry added ✅")

    st.markdown("---")
    st.subheader("Your Suppliers")
    df_user = df[df["user"]==user].sort_values("date", ascending=False)
    st.dataframe(df_user, use_container_width=True)
    st.download_button("⬇️ Download Suppliers CSV", df_user.to_csv(index=False).encode(), f"suppliers_{user}.csv")
    st.download_button("⬇️ Download Suppliers Excel", df_to_excel_bytes(df_user,"Suppliers"), f"suppliers_{user}.xlsx")

# -------------------------
# Reports & Analytics
# -------------------------
def reports_page():
    st.header("📊 Reports & Analytics")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","notes"]
    df = load_csv(FILES["services"], svc_cols)
    df_user = df[df["user"]==user]
    
    period = st.radio("Select Period", ["Daily","Weekly","Monthly","All Time"])
    df_period = filter_date(df_user, "date", period)
    
    st.subheader("📈 Product-wise Flow")
    prod_group = df_period.groupby("service_type").agg({"num_apps":"sum","govt_amt":"sum","paid_amt":"sum","profit_amt":"sum"}).reset_index()
    st.dataframe(prod_group)

    st.subheader("💹 Charts")
    if not prod_group.empty:
        fig, ax = plt.subplots(figsize=(10,5))
        ax.bar(prod_group["service_type"], prod_group["num_apps"])
        ax.set_xticklabels(prod_group["service_type"], rotation=45, ha="right")
        ax.set_ylabel("No. of Applications")
        st.pyplot(fig)

    st.subheader("💰 Profit & Loss Summary")
    total_govt = df_period["govt_amt"].sum()
    total_paid = df_period["paid_amt"].sum()
    total_profit = df_period["profit_amt"].sum()
    st.write(f"**Total Govt Amount:** ₹{total_govt}")
    st.write(f"**Total Paid Amount:** ₹{total_paid}")
    st.write(f"**Profit:** ₹{total_profit}")

# -------------------------
# Main
# -------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES - Tracker", layout="wide")
    if st.session_state.user is None:
        login_page()
        return

    st.sidebar.title("📊 NANI ASSOCIATES")
    st.sidebar.write(f"Logged in as: **{st.session_state.user}** ({st.session_state.device})")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Menu", [
        "Service Entry",
        "Expense Entry",
        "Transactions",
        "Suppliers",
        "Reports & Analytics",
    ])
    if page=="Service Entry":
        service_entry_page()
    elif page=="Expense Entry":
        expense_entry_page()
    elif page=="Transactions":
        transactions_page()
    elif page=="Suppliers":
        suppliers_page()
    elif page=="Reports & Analytics":
        reports_page()

if __name__=="__main__":
    main()
