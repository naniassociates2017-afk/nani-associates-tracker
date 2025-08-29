# appy.py
import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
from io import BytesIO

# -------------------------
# Config / Credentials
# -------------------------
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

FILES = {
    "services": os.path.join(DATA_FOLDER, "services.csv"),
    "expenses": os.path.join(DATA_FOLDER, "expenses.csv"),
    "suppliers": os.path.join(DATA_FOLDER, "suppliers.csv"),
    "cash": os.path.join(DATA_FOLDER, "cash.csv"),
}

USER_CREDENTIALS = {
    "admin": "admin123",
    "user1": "user123",
    "user2": "user234",
    "mobile": "mobile123",
}

PAYMENT_TYPES = ["Cash","UPI","Bank Transfer","Cheque","Other"]

DEFAULT_GOVT_AMT = {
    "NEW PAN CARD": 107.0,
    "CORRECTION PAN CARD": 107.0,
    "NEW PASSPORT": 1500.0,
    "RENEWAL PASSPORT": 1500.0,
    "DIGITAL SIGNATURE": 1400.0,
    "VOTER ID": 0.0,
    "NEW AADHAR CARD": 100.0,
    "NAME CHANGE AADHAR CARD": 0.0,
    "DATE OF BIRTH CHANGE IN AADHAR CARD": 0.0,
    "BIRTH CERTIFICATE": 3000.0,
    "OTHER ONLINE SERVICES": 0.0,
}

# -------------------------
# Utilities
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
                    df[c] = 0.0 if 'amt' in c.lower() or 'cash' in c.lower() else ""
            return df[columns]
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def ensure_datafiles_exist():
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    exp_cols = ["id","date","user","category","amount","notes"]
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","profit_amt","payment_type","notes"]
    cash_cols = ["id","date","user","cash_in_hand","cash_at_bank","notes"]
    for key, cols in zip(FILES.keys(), [svc_cols, exp_cols, sup_cols, cash_cols]):
        if not os.path.exists(FILES[key]):
            save_csv(pd.DataFrame(columns=cols), FILES[key])

def next_id(df):
    if df.empty:
        return 1
    try:
        return int(df["id"].max()) + 1
    except Exception:
        return len(df) + 1

def filter_date(df, date_col="date", start=None, end=None):
    df[date_col] = pd.to_datetime(df[date_col])
    if start and end:
        return df[(df[date_col].dt.date>=start) & (df[date_col].dt.date<=end)]
    else:
        return df

def color_status(val):
    if val=="Paid":
        return 'background-color: lightgreen'
    elif val=="Pending":
        return 'background-color: #ff9999'
    elif val=="Partial":
        return 'background-color: orange'
    return ''

def format_amounts(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: round(float(x),2))
    return df

# -------------------------
# Session State
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
    st.markdown("""
    - **admin / admin123**  
    - **user1 / user123**  
    - **user2 / user234**  
    - **mobile / mobile123**
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
    svc_cols = ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"]
    df = load_csv(FILES["services"], svc_cols)
    df = format_amounts(df, ["govt_amt","paid_amt","profit_amt"])
    customers = df["customer"].dropna().unique().tolist()

    st.subheader("➕ Add New Service")
    with st.form("svc_add_form", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Date", value=date.today())
            customer = st.text_input("Customer / Agent", value="", placeholder="Start typing...")
            service_type = st.selectbox("Service Type", list(DEFAULT_GOVT_AMT.keys()))
        with c2:
            num_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1)
            default_amt = DEFAULT_GOVT_AMT.get(service_type,0.0)
            govt_amt = st.number_input("Government Amount (per app)", min_value=0.0, value=float(default_amt))
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
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"customer":customer,
                           "service_type":service_type,"num_apps":int(num_apps),"govt_amt":total_govt,
                           "paid_amt":total_paid,"profit_amt":profit,"status":status,"payment_type":payment_type,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                df = format_amounts(df, ["govt_amt","paid_amt","profit_amt"])
                save_csv(df, FILES["services"])
                st.success("Service added ✅")

    st.markdown("---")
    st.subheader("📊 Service History")
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="svc_start")
    end_date = st.date_input("End Date", value=date.today(), key="svc_end")
    df_filtered = filter_date(df, start=start_date, end=end_date)
    df_filtered = format_amounts(df_filtered, ["govt_amt","paid_amt","profit_amt"])
    st.dataframe(df_filtered.style.applymap(color_status, subset=["status"]))

    st.markdown("### 💰 Service Amount Summary")
    summary = df_filtered.groupby("status")[["paid_amt","profit_amt"]].sum().reindex(["Paid","Partial","Pending"], fill_value=0)
    summary = format_amounts(summary, ["paid_amt","profit_amt"])
    st.dataframe(summary)

    st.markdown("### 🔍 Customer / Agent History")
    customer_select = st.selectbox("Select Customer / Agent", customers)
    if customer_select:
        df_history = df_filtered[df_filtered["customer"]==customer_select]
        df_history = format_amounts(df_history, ["govt_amt","paid_amt","profit_amt"])
        st.dataframe(df_history.style.applymap(color_status, subset=["status"]))
        st.download_button("⬇️ Download Customer History CSV", df_history.to_csv(index=False).encode(), f"{customer_select}_history.csv")
        st.download_button("⬇️ Download Customer History Excel", df_to_excel_bytes(df_history,f"{customer_select}_history"), f"{customer_select}_history.xlsx")

# -------------------------
# Expenses Entry
# -------------------------
def expenses_entry_page():
    st.header("💵 Expenses Entry")
    user = st.session_state.user
    exp_cols = ["id","date","user","category","amount","notes"]
    df = load_csv(FILES["expenses"], exp_cols)
    df = format_amounts(df, ["amount"])

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
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,
                           "category":category,"amount":round(amount,2),"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                save_csv(df, FILES["expenses"])
                st.success("Expense added ✅")

    st.markdown("---")
    st.subheader("Your Expenses")
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="exp_start")
    end_date = st.date_input("End Date", value=date.today(), key="exp_end")
    df_user = df[(df["user"]==user) & (pd.to_datetime(df["date"]).dt.date>=start_date) & (pd.to_datetime(df["date"]).dt.date<=end_date)].sort_values("date", ascending=False)
    df_user = format_amounts(df_user, ["amount"])
    st.dataframe(df_user)
    st.download_button("⬇️ Download Expenses CSV", df_user.to_csv(index=False).encode(), f"expenses_{user}.csv")
    st.download_button("⬇️ Download Expenses Excel", df_to_excel_bytes(df_user,"Expenses"), f"expenses_{user}.xlsx")

# -------------------------
# Suppliers Entry
# -------------------------
def suppliers_entry_page():
    st.header("🏢 Suppliers Entry")
    user = st.session_state.user
    sup_cols = ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","profit_amt","payment_type","notes"]
    df = load_csv(FILES["suppliers"], sup_cols)
    df = format_amounts(df, ["paid_amt","pending_amt","partial_amt","profit_amt"])
    suppliers = df["supplier_name"].dropna().unique().tolist()

    with st.form("sup_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        supplier = st.text_input("Supplier Name")
        service_type = st.text_input("Service Type")
        paid_amt = st.number_input("Paid Amount", min_value=0.0)
        pending_amt = st.number_input("Pending Amount", min_value=0.0)
        partial_amt = st.number_input("Partial Amount", min_value=0.0)
        profit_amt = round(paid_amt - (pending_amt + partial_amt),2)
        payment_type = st.selectbox("Payment Type", PAYMENT_TYPES)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Supplier Entry"):
            if not supplier or not service_type:
                st.error("Enter supplier and service type")
            else:
                nid = next_id(df)
                new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"supplier_name":supplier,"service_type":service_type,
                           "paid_amt":round(paid_amt,2),"pending_amt":round(pending_amt,2),"partial_amt":round(partial_amt,2),"profit_amt":profit_amt,"payment_type":payment_type,"notes":notes}
                df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
                df = format_amounts(df, ["paid_amt","pending_amt","partial_amt","profit_amt"])
                save_csv(df, FILES["suppliers"])
                st.success("Supplier added ✅")

    st.markdown("---")
    st.subheader("Suppliers History")
    start_date = st.date_input("Start Date", value=date.today()-timedelta(days=30), key="sup_start")
    end_date = st.date_input("End Date", value=date.today(), key="sup_end")
    df_filtered = filter_date(df, start=start_date, end=end_date)
    df_filtered = format_amounts(df_filtered, ["paid_amt","pending_amt","partial_amt","profit_amt"])
    st.dataframe(df_filtered)
    st.markdown("### Supplier Summary")
    summary = df_filtered.groupby("supplier_name")[["paid_amt","pending_amt","partial_amt","profit_amt"]].sum()
    summary = format_amounts(summary, ["paid_amt","pending_amt","partial_amt","profit_amt"])
    st.dataframe(summary)

# -------------------------
# Cash in Hand / Bank
# -------------------------
def cash_entry_page():
    st.header("💰 Cash In Hand / Bank")
    user = st.session_state.user
    cash_cols = ["id","date","user","cash_in_hand","cash_at_bank","notes"]
    df = load_csv(FILES["cash"], cash_cols)
    df = format_amounts(df, ["cash_in_hand","cash_at_bank"])

    with st.form("cash_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        cash_hand = st.number_input("Cash In Hand", min_value=0.0)
        cash_bank = st.number_input("Cash At Bank", min_value=0.0)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("➕ Add Cash Entry"):
            nid = next_id(df)
            new_row = {"id":nid,"date":entry_date.strftime("%Y-%m-%d"),"user":user,"cash_in_hand":round(cash_hand,2),"cash_at_bank":round(cash_bank,2),"notes":notes}
            df = pd.concat([df,pd.DataFrame([new_row])], ignore_index=True)
            df = format_amounts(df, ["cash_in_hand","cash_at_bank"])
            save_csv(df, FILES["cash"])
            st.success("Cash entry added ✅")

    st.markdown("---")
    st.subheader("Cash Records")
    df_user = df[df["user"]==user].sort_values("date", ascending=False)
    st.dataframe(df_user)
    st.download_button("⬇️ Download Cash CSV", df_user.to_csv(index=False).encode(), f"cash_{user}.csv")
    st.download_button("⬇️ Download Cash Excel", df_to_excel_bytes(df_user,"Cash"), f"cash_{user}.xlsx")

# -------------------------
# Dashboard with daily profit/loss
# -------------------------
def dashboard_summary():
    st.header("📊 Dashboard Summary")
    user = st.session_state.user

    df_svc = load_csv(FILES["services"], ["id","date","user","customer","service_type","num_apps","govt_amt","paid_amt","profit_amt","status","payment_type","notes"])
    df_svc = format_amounts(df_svc, ["govt_amt","paid_amt","profit_amt"])
    df_sup = load_csv(FILES["suppliers"], ["id","date","user","supplier_name","service_type","paid_amt","pending_amt","partial_amt","profit_amt","payment_type","notes"])
    df_sup = format_amounts(df_sup, ["paid_amt","pending_amt","partial_amt","profit_amt"])
    df_exp = load_csv(FILES["expenses"], ["id","date","user","category","amount","notes"])
    df_exp = format_amounts(df_exp, ["amount"])
    df_cash = load_csv(FILES["cash"], ["id","date","user","cash_in_hand","cash_at_bank","notes"])
    df_cash = format_amounts(df_cash, ["cash_in_hand","cash_at_bank"])

    df_svc_user = df_svc[df_svc["user"]==user]
    df_sup_user = df_sup[df_sup["user"]==user]
    df_exp_user = df_exp[df_exp["user"]==user]
    df_cash_user = df_cash[df_cash["user"]==user]

    st.subheader("Services Summary")
    st.dataframe(df_svc_user.groupby("status")[["paid_amt","profit_amt"]].sum())

    st.subheader("Suppliers Summary")
    st.dataframe(df_sup_user.groupby("supplier_name")[["paid_amt","pending_amt","partial_amt","profit_amt"]].sum())

    st.subheader("Expenses Total")
    st.write(f"Total Expenses: ₹{df_exp_user['amount'].sum()}")

    st.subheader("Cash Verification")
    if not df_cash_user.empty:
        today_cash = df_cash_user[df_cash_user["date"]==date.today().strftime("%Y-%m-%d")]
        if not today_cash.empty:
            st.write(f"Cash In Hand: ₹{today_cash['cash_in_hand'].sum()}, Cash At Bank: ₹{
