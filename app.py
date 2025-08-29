# appy.py
import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta, datetime
from io import BytesIO

# -------------------------
# Config / Credentials
# -------------------------
DATA_FOLDER = "data"
BACKUP_FOLDER = "backup"
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

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

PAYMENT_TYPES = ["Cash","UPI","Bank Transfer","Cheque","Other"]

# -------------------------
# Utility Functions
# -------------------------
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
    # Backup automatically
    backup_path = os.path.join(BACKUP_FOLDER, f"{os.path.basename(file_path).replace('.csv','')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(backup_path, index=False)

def ensure_datafiles_exist():
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","payment_type","notes"]
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

def filter_date_range(df, date_col="date", start_date=None, end_date=None):
    df[date_col] = pd.to_datetime(df[date_col])
    if start_date:
        df = df[df[date_col].dt.date >= start_date]
    if end_date:
        df = df[df[date_col].dt.date <= end_date]
    return df

def color_status(val):
    if val=="Paid":
        color = 'background-color: lightgreen'
    elif val=="Pending":
        color = 'background-color: #ff9999'
    elif val=="Partial":
        color = 'background-color: orange'
    else:
        color = ''
    return color

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
# Entry Pages
# -------------------------
def service_entry_page():
    st.header("📝 Service Entry")
    user = st.session_state.user
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
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
            payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
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
                    "paid_amt":total_paid,"profit_amt":profit,"status":status,"payment_type":payment_type,"notes":notes
                }
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["services"])
                st.success("Service added ✅")

    st.markdown("---")
    st.subheader("Search / Filter by Date")
    start_date = st.date_input("From", value=date.today()-timedelta(days=30), key="svc_start")
    end_date = st.date_input("To", value=date.today(), key="svc_end")
    df_user = df[df["user"]==user]
    df_filtered = filter_date_range(df_user,"date",start_date,end_date).sort_values("date", ascending=False)
    st.dataframe(df_filtered.style.applymap(color_status, subset=["status"]), use_container_width=True)
    st.download_button("⬇️ Download Services CSV", df_filtered.to_csv(index=False).encode(), f"services_{user}.csv")
    st.download_button("⬇️ Download Services Excel", df_to_excel_bytes(df_filtered,"Services"), f"services_{user}.xlsx")

# Expenses
def expenses_entry_page():
    st.header("💵 Expenses Entry")
    user = st.session_state.user
    exp_cols = ["id","date","user","category","amount","notes"]
    df = load_csv(FILES["expenses"], exp_cols)

    with st.form("exp_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        category = st.text_input("Category")
        amount = st.number_input("Amount", min_value=0.0)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Expense"):
            if not category:
                st.error("Enter category")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"category":category,"amount":amount,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["expenses"])
                st.success("Expense added ✅")

    st.markdown("---")
    st.subheader("Search / Filter by Date")
    start_date = st.date_input("From", value=date.today()-timedelta(days=30), key="exp_start")
    end_date = st.date_input("To", value=date.today(), key="exp_end")
    df_user = df[(df["user"]==user)]
    df_filtered = filter_date_range(df_user,"date",start_date,end_date).sort_values("date", ascending=False)
    st.dataframe(df_filtered, use_container_width=True)
    st.download_button("⬇️ Download Expenses CSV", df_filtered.to_csv(index=False).encode(), f"expenses_{user}.csv")
    st.download_button("⬇️ Download Expenses Excel", df_to_excel_bytes(df_filtered,"Expenses"), f"expenses_{user}.xlsx")

# Transactions
def transactions_entry_page():
    st.header("💳 Transactions Entry")
    user = st.session_state.user
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    df = load_csv(FILES["transactions"], txn_cols)

    with st.form("txn_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        party = st.text_input("Party Name")
        service_type = st.text_input("Service Type")
        status = st.selectbox("Payment Status", ["Paid","Pending","Partial"])
        amount = st.number_input("Amount", min_value=0.0)
        payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Transaction"):
            if not party or not service_type:
                st.error("Enter party and service type")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"party":party,
                           "service_type":service_type,"status":status,"amount":amount,"payment_type":payment_type,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["transactions"])
                st.success("Transaction added ✅")

    st.markdown("---")
    st.subheader("Search / Filter by Date")
    start_date = st.date_input("From", value=date.today()-timedelta(days=30), key="txn_start")
    end_date = st.date_input("To", value=date.today(), key="txn_end")
    df_user = df[(df["user"]==user)]
    df_filtered = filter_date_range(df_user,"date",start_date,end_date).sort_values("date", ascending=False)
    st.dataframe(df_filtered.style.applymap(color_status, subset=["status"]), use_container_width=True)
    st.download_button("⬇️ Download Transactions CSV", df_filtered.to_csv(index=False).encode(), f"transactions_{user}.csv")
    st.download_button("⬇️ Download Transactions Excel", df_to_excel_bytes(df_filtered,"Transactions"), f"transactions_{user}.xlsx")

# Suppliers
def suppliers_entry_page():
    st.header("🏢 Suppliers Entry")
    user = st.session_state.user
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","payment_type","notes"]
    df = load_csv(FILES["suppliers"], sup_cols)

    with st.form("sup_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        supplier = st.text_input("Supplier Name")
        service_type = st.text_input("Service Type")
        paid_amt = st.number_input("Paid Amount", min_value=0.0)
        pending_amt = st.number_input("Pending Amount", min_value=0.0)
        partial_amt = st.number_input("Partial Amount", min_value=0.0)
        payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Supplier Entry"):
            if not supplier or not service_type:
                st.error("Enter supplier and service type")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"supplier_name":supplier,
                           "service_type":service_type,"paid_amt":paid_amt,"pending_amt":pending_amt,"partial_amt":partial_amt,
                           "payment_type":payment_type,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["suppliers"])
                st.success("Supplier added ✅")

    st.markdown("---")
    st.subheader("Search / Filter by Date")
    start_date = st.date_input("From", value=date.today()-timedelta(days=30), key="sup_start")
    end_date = st.date_input("To", value=date.today(), key="sup_end")
    df_user = df[(df["user"]==user)]
    df_filtered = filter_date_range(df_user,"date",start_date,end_date).sort_values("date", ascending=False)
    st.dataframe(df_filtered, use_container_width=True)
    st.download_button("⬇️ Download Suppliers CSV", df_filtered.to_csv(index=False).encode(), f"suppliers_{user}.csv")
    st.download_button("⬇️ Download Suppliers Excel", df_to_excel_bytes(df_filtered,"Suppliers"), f"suppliers_{user}.xlsx")

# -------------------------
# Dashboard / Analytics
# -------------------------
def dashboard_page():
    st.header("📊 Dashboard & Analytics")
    user = st.session_state.user

    # Load all data
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    txn_cols = ["id","date","user","party","service_type","status","amount","payment_type","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","payment_type","notes"]
    df_svc = load_csv(FILES["services"], svc_cols)
    df_txn = load_csv(FILES["transactions"], txn_cols)
    df_sup = load_csv(FILES["suppliers"], sup_cols)

    df_svc_user = df_svc[df_svc["user"]==user]
    df_txn_user = df_txn[df_txn["user"]==user]
    df_sup_user = df_sup[df_sup["user"]==user]

    st.subheader("Payment Summary")
    svc_sum = df_svc_user.groupby("status")["paid_amt"].sum().reindex(["Paid","Pending","Partial"],fill_value=0)
    txn_sum = df_txn_user.groupby("status")["amount"].sum().reindex(["Paid","Pending","Partial"],fill_value=0)
    sup_sum = pd.Series({"Paid":df_sup_user["paid_amt"].sum(),"Pending":df_sup_user["pending_amt"].sum(),"Partial":df_sup_user["partial_amt"].sum()})
    c1,c2,c3 = st.columns(3)
    c1.metric("Services", f"₹{svc_sum['Paid']}", f"Pending: ₹{svc_sum['Pending']} | Partial: ₹{svc_sum['Partial']}")
    c2.metric("Transactions", f"₹{txn_sum['Paid']}", f"Pending: ₹{txn_sum['Pending']} | Partial: ₹{txn_sum['Partial']}")
    c3.metric("Suppliers", f"₹{sup_sum['Paid']}", f"Pending: ₹{sup_sum['Pending']} | Partial: ₹{sup_sum['Partial']}")

    # Charts
    st.subheader("Service / Product Analytics")
    period = st.selectbox("Select Period", ["Daily","Weekly","Monthly","All"])
    today = date.today()
    if period=="Daily":
        df_period = df_svc_user[df_svc_user["date"]==today.strftime("%Y-%m-%d")]
    elif period=="Weekly":
        week_ago = today - timedelta(days=7)
        df_period = df_svc_user[df_svc_user["date"]>=week_ago.strftime("%Y-%m-%d")]
    elif period=="Monthly":
        month_start = today.replace(day=1)
        df_period = df_svc_user[df_svc_user["date"]>=month_start.strftime("%Y-%m-%d")]
    else:
        df_period = df_svc_user

    if not df_period.empty:
        chart_data = df_period.groupby("service_type")[["num_apps","paid_amt","profit_amt"]].sum()
        st.bar_chart(chart_data[["num_apps"]], use_container_width=True, height=200)
        st.bar_chart(chart_data[["paid_amt"]], use_container_width=True, height=200)
        st.bar_chart(chart_data[["profit_amt"]], use_container_width=True, height=200)
    else:
        st.info("No services in this period")

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
        "Dashboard",
        "Service Entry",
        "Expenses Entry",
        "Transactions Entry",
        "Suppliers Entry"
    ])
    if page=="Dashboard":
        dashboard_page()
    elif page=="Service Entry":
        service_entry_page()
    elif page=="Expenses Entry":
        expenses_entry_page()
    elif page=="Transactions Entry":
        transactions_entry_page()
    elif page=="Suppliers Entry":
        suppliers_entry_page()

if __name__=="__main__":
    main()
