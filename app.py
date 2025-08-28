# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from io import BytesIO
import uuid

# ===============================
# ---------- SETTINGS -----------
# ===============================
APP_TITLE = "📊 NANI ASSOCIATES – BUSINESS TRACKER"
DATA_DIR = "data"
FILES = {
    "services": os.path.join(DATA_DIR, "services.csv"),
    "expenses": os.path.join(DATA_DIR, "expenses.csv"),
    "transactions": os.path.join(DATA_DIR, "transactions.csv"),  # agents/customers
    "suppliers": os.path.join(DATA_DIR, "suppliers.csv"),
    "balances": os.path.join(DATA_DIR, "balances.csv"),
}
DATE_FMT = "%Y-%m-%d"

# Login credentials
VALID_USER = "admin"
VALID_PASS = "admin123"

# ===============================
# ---------- UTILITIES ----------
# ===============================
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_csv(path: str, cols: list) -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            # make sure any missing expected columns exist
            for c in cols:
                if c not in df.columns:
                    df[c] = pd.Series(dtype="object")
            # keep only expected columns (and id if present)
            keep = [c for c in df.columns if c in cols]
            # If id exists keep it
            if "id" in df.columns and "id" not in keep:
                keep = ["id"] + keep
            return df[keep]
        except Exception:
            return pd.DataFrame(columns=cols)
    else:
        return pd.DataFrame(columns=cols)

def save_csv(df: pd.DataFrame, path: str):
    ensure_data_dir()
    df.to_csv(path, index=False)

def gen_id() -> str:
    return uuid.uuid4().hex[:12]

def money(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0

def today_str() -> str:
    return datetime.now().strftime(DATE_FMT)

def periodize(df: pd.DataFrame, date_col: str, period: str) -> pd.DataFrame:
    if df.empty:
        return df
    tmp = df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    if period == "Daily":
        grp = tmp.groupby(tmp[date_col].dt.date)
    elif period == "Weekly":
        grp = tmp.groupby(tmp[date_col].dt.to_period("W").astype(str))
    else:  # Monthly
        grp = tmp.groupby(tmp[date_col].dt.to_period("M").astype(str))
    return grp.sum(numeric_only=True).reset_index().rename(columns={date_col: period})

# ===============================
# ------- SESSION / LOGIN -------
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_ui():
    st.title(APP_TITLE)
    st.subheader("🔐 Login")
    u = st.text_input("Username", key="login_user")
    p = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
        if u == VALID_USER and p == VALID_PASS:
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout_btn():
    st.sidebar.button("Logout", key="logout_btn", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.sidebar.success("Logged in as admin")

# ===============================
# ---------- DATA MODELS --------
# ===============================
SERVICE_COLS = [
    "id","date","service_type","client","agent","amount","paid_amount","status","method","remarks"
]
EXPENSE_COLS = [
    "id","date","category","payee","amount","paid_amount","method","notes"
]
TXN_COLS = [
    "id","date","party_type","party","service","amount","paid_amount","status","method","notes"
]
SUP_COLS = [
    "id","date","supplier","description","amount","paid_amount","status","method","notes"
]
BAL_COLS = ["date","opening_cash","opening_bank"]

def recompute_status(row) -> str:
    amt = money(row.get("amount",0))
    paid = money(row.get("paid_amount",0))
    if paid <= 0:
        return "Pending"
    if paid >= amt:
        return "Paid"
    return "Partial"

# ===============================
# ----------- PAGES -------------
# ===============================
def page_service_entry():
    st.header("📝 Service Entry")
    df = load_csv(FILES["services"], SERVICE_COLS)

    with st.form("service_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("Date", value=date.today(), key="srv_date")
        with c2:
            s_type = st.selectbox("Service Type", ["Consulting","Installation","Maintenance","Other"], key="srv_type")
        with c3:
            method = st.selectbox("Payment Method", ["Cash","Bank","Other"], key="srv_method")

        c4, c5, c6 = st.columns(3)
        with c4:
            client = st.text_input("Client / Customer", key="srv_client")
        with c5:
            agent = st.text_input("Agent", key="srv_agent")
        with c6:
            amount = st.number_input("Amount", min_value=0.0, step=0.1, key="srv_amount")

        c7, c8 = st.columns(2)
        with c7:
            paid = st.number_input("Paid Amount", min_value=0.0, step=0.1, key="srv_paid")
        with c8:
            remarks = st.text_input("Remarks", key="srv_remarks")

        submitted = st.form_submit_button("Save Service")
        if submitted:
            new = {
                "id": gen_id(),
                "date": d.strftime(DATE_FMT),
                "service_type": s_type,
                "client": client.strip(),
                "agent": agent.strip(),
                "amount": amount,
                "paid_amount": paid,
                "status": "Pending",  # will recompute
                "method": method,
                "remarks": remarks.strip()
            }
            new["status"] = recompute_status(new)
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_csv(df, FILES["services"])
            st.success("✅ Service entry saved.")
            st.rerun()

    st.subheader("Recent Service Entries")
    if not df.empty:
        # Allow delete
        show = df.copy()
        show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.strftime(DATE_FMT)
        st.dataframe(show.sort_values("date", ascending=False), use_container_width=True)
        delete_id = st.selectbox("Delete a row by ID", options=["-"] + show["id"].tolist(), key="srv_del_id")
        if delete_id != "-" and st.button("Delete Service", key="srv_del_btn"):
            df = df[df["id"] != delete_id]
            save_csv(df, FILES["services"])
            st.success("Deleted.")
            st.rerun()
    else:
        st.info("No service entries yet.")

def page_expense_entry():
    st.header("💸 Expense Entry")
    df = load_csv(FILES["expenses"], EXPENSE_COLS)

    with st.form("exp_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("Date", value=date.today(), key="exp_date")
        with c2:
            cat = st.selectbox("Category", ["Rent","Salary","Purchase","Travel","Misc"], key="exp_cat")
        with c3:
            method = st.selectbox("Payment Method", ["Cash","Bank","Other"], key="exp_method")

        c4, c5 = st.columns(2)
        with c4:
            payee = st.text_input("Payee / Vendor", key="exp_payee")
        with c5:
            amount = st.number_input("Amount", min_value=0.0, step=0.1, key="exp_amount")

        c6, c7 = st.columns(2)
        with c6:
            paid = st.number_input("Paid Amount", min_value=0.0, step=0.1, key="exp_paid")
        with c7:
            notes = st.text_input("Notes", key="exp_notes")

        submitted = st.form_submit_button("Save Expense")
        if submitted:
            new = {
                "id": gen_id(),
                "date": d.strftime(DATE_FMT),
                "category": cat,
                "payee": payee.strip(),
                "amount": amount,
                "paid_amount": paid,
                "method": method,
                "notes": notes.strip()
            }
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_csv(df, FILES["expenses"])
            st.success("✅ Expense saved.")
            st.rerun()

    st.subheader("Recent Expenses")
    if not df.empty:
        show = df.copy()
        show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.strftime(DATE_FMT)
        st.dataframe(show.sort_values("date", ascending=False), use_container_width=True)
        del_id = st.selectbox("Delete a row by ID", options=["-"] + show["id"].tolist(), key="exp_del_id")
        if del_id != "-" and st.button("Delete Expense", key="exp_del_btn"):
            df = df[df["id"] != del_id]
            save_csv(df, FILES["expenses"])
            st.success("Deleted.")
            st.rerun()
    else:
        st.info("No expenses yet.")

def page_agents_customers():
    st.header("👥 Agents / Customers – Transactions")
    df = load_csv(FILES["transactions"], TXN_COLS)

    with st.form("txn_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("Date", value=date.today(), key="txn_date")
        with c2:
            party_type = st.selectbox("Party Type", ["Agent","Customer"], key="txn_ptype")
        with c3:
            method = st.selectbox("Payment Method", ["Cash","Bank","Other"], key="txn_method")

        c4, c5 = st.columns(2)
        with c4:
            party = st.text_input("Agent/Customer Name", key="txn_party")
        with c5:
            service = st.text_input("Service / Product", key="txn_service")

        c6, c7 = st.columns(2)
        with c6:
            amount = st.number_input("Billed Amount", min_value=0.0, step=0.1, key="txn_amount")
        with c7:
            paid = st.number_input("Paid Amount", min_value=0.0, step=0.1, key="txn_paid")

        notes = st.text_input("Notes", key="txn_notes")

        submitted = st.form_submit_button("Save Transaction")
        if submitted:
            new = {
                "id": gen_id(),
                "date": d.strftime(DATE_FMT),
                "party_type": party_type,
                "party": party.strip(),
                "service": service.strip(),
                "amount": amount,
                "paid_amount": paid,
                "status": "Pending",
                "method": method,
                "notes": notes.strip()
            }
            new["status"] = recompute_status(new)
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_csv(df, FILES["transactions"])
            st.success("✅ Transaction saved.")
            st.rerun()

    if not df.empty:
        st.subheader("Filter")
        c1, c2, c3 = st.columns(3)
        with c1:
            ptype = st.selectbox("Party Type", ["All","Agent","Customer"], key="txn_f_ptype")
        with c2:
            status = st.selectbox("Status", ["All","Paid","Partial","Pending"], key="txn_f_status")
        with c3:
            method = st.selectbox("Method", ["All","Cash","Bank","Other"], key="txn_f_method")

        show = df.copy()
        if ptype != "All":
            show = show[show["party_type"] == ptype]
        if status != "All":
            show = show[show["status"] == status]
        if method != "All":
            show = show[show["method"] == method]

        # totals
        st.write(
            f"**Total Billed:** {show['amount'].fillna(0).astype(float).sum():,.2f} | "
            f"**Total Paid:** {show['paid_amount'].fillna(0).astype(float).sum():,.2f} | "
            f"**Balance:** {(show['amount'].fillna(0).astype(float)-show['paid_amount'].fillna(0).astype(float)).sum():,.2f}"
        )

        show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.strftime(DATE_FMT)
        st.dataframe(show.sort_values("date", ascending=False), use_container_width=True)

        del_id = st.selectbox("Delete by ID", options=["-"] + show["id"].tolist(), key="txn_del_id")
        if del_id != "-" and st.button("Delete Transaction", key="txn_del_btn"):
            df = df[df["id"] != del_id]
            save_csv(df, FILES["transactions"])
            st.success("Deleted.")
            st.rerun()
    else:
        st.info("No transactions yet.")

def page_suppliers():
    st.header("🏷️ Suppliers – Invoices & Payments")
    df = load_csv(FILES["suppliers"], SUP_COLS)

    with st.form("sup_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("Date", value=date.today(), key="sup_date")
        with c2:
            supplier = st.text_input("Supplier", key="sup_name")
        with c3:
            method = st.selectbox("Payment Method", ["Cash","Bank","Other"], key="sup_method")

        c4, c5 = st.columns(2)
        with c4:
            desc = st.text_input("Description (services received / invoice)", key="sup_desc")
        with c5:
            amount = st.number_input("Invoice Amount", min_value=0.0, step=0.1, key="sup_amount")

        c6, c7 = st.columns(2)
        with c6:
            paid = st.number_input("Paid Amount", min_value=0.0, step=0.1, key="sup_paid")
        with c7:
            notes = st.text_input("Notes", key="sup_notes")

        submitted = st.form_submit_button("Save Supplier Entry")
        if submitted:
            new = {
                "id": gen_id(),
                "date": d.strftime(DATE_FMT),
                "supplier": supplier.strip(),
                "description": desc.strip(),
                "amount": amount,
                "paid_amount": paid,
                "status": "Pending",
                "method": method,
                "notes": notes.strip()
            }
            new["status"] = recompute_status(new)
            df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_csv(df, FILES["suppliers"])
            st.success("✅ Supplier entry saved.")
            st.rerun()

    if not df.empty:
        st.subheader("Balances by Supplier")
        bal = df.groupby("supplier").agg(
            billed=("amount","sum"),
            paid=("paid_amount","sum")
        ).reset_index()
        bal["balance"] = (bal["billed"] - bal["paid"]).round(2)
        st.dataframe(bal, use_container_width=True)

        st.subheader("All Supplier Entries")
        show = df.copy()
        show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.strftime(DATE_FMT)
        st.dataframe(show.sort_values("date", ascending=False), use_container_width=True)

        del_id = st.selectbox("Delete by ID", options=["-"] + show["id"].tolist(), key="sup_del_id")
        if del_id != "-" and st.button("Delete Supplier Entry", key="sup_del_btn"):
            df = df[df["id"] != del_id]
            save_csv(df, FILES["suppliers"])
            st.success("Deleted.")
            st.rerun()
    else:
        st.info("No supplier entries yet.")

def page_daily_logger():
    st.header("📓 Daily Data Logger")
    # per-day CSV simple logger: time, name, amount
    folder = os.path.join(DATA_DIR, "daily")
    os.makedirs(folder, exist_ok=True)

    def today_file():
        return os.path.join(folder, f"data_{today_str()}.csv")

    def load_day(fp):
        if os.path.exists(fp):
            return pd.read_csv(fp)
        return pd.DataFrame(columns=["time","name","amount"])

    name = st.text_input("Name", key="dlog_name")
    amount = st.number_input("Amount", min_value=0.0, step=0.1, key="dlog_amt")
    if st.button("Save Entry", key="dlog_save"):
        df = load_day(today_file())
        df = pd.concat([df, pd.DataFrame([{
            "time": datetime.now().strftime("%H:%M:%S"),
            "name": name.strip(),
            "amount": amount
        }])], ignore_index=True)
        df.to_csv(today_file(), index=False)
        st.success("Saved.")
        st.rerun()

    st.subheader("Today")
    st.dataframe(load_day(today_file()), use_container_width=True)

    all_files = sorted([f for f in os.listdir(folder) if f.startswith("data_") and f.endswith(".csv")], reverse=True)
    if all_files:
        sel = st.selectbox("View another day", options=all_files, key="dlog_sel")
        st.dataframe(load_day(os.path.join(folder, sel)), use_container_width=True)

def page_reports():
    st.header("📈 Reports (Daily / Weekly / Monthly)")

    services = load_csv(FILES["services"], SERVICE_COLS)
    txns = load_csv(FILES["transactions"], TXN_COLS)
    expenses = load_csv(FILES["expenses"], EXPENSE_COLS)
    suppliers = load_csv(FILES["suppliers"], SUP_COLS)

    # Income is "paid_amount" from services + transactions
    income_df = pd.DataFrame(columns=["date","paid_amount"])
    if not services.empty:
        s = services[["date","paid_amount"]].copy()
        s.rename(columns={"paid_amount":"paid_amount"}, inplace=True)
        income_df = pd.concat([income_df, s], ignore_index=True)
    if not txns.empty:
        t = txns[["date","paid_amount"]].copy()
        income_df = pd.concat([income_df, t], ignore_index=True)

    # Expenses are paid (expenses + supplier paid)
    out_df = pd.DataFrame(columns=["date","paid_amount"])
    if not expenses.empty:
        e = expenses[["date","paid_amount"]].copy()
        out_df = pd.concat([out_df, e], ignore_index=True)
    if not suppliers.empty:
        sp = suppliers[["date","paid_amount"]].copy()
        out_df = pd.concat([out_df, sp], ignore_index=True)

    period = st.radio("Period", ["Daily","Weekly","Monthly"], key="rep_period", horizontal=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        total_income = income_df["paid_amount"].fillna(0).astype(float).sum()
        st.metric("Total Income (paid)", f"{total_income:,.2f}")
    with c2:
        total_exp = out_df["paid_amount"].fillna(0).astype(float).sum()
        st.metric("Total Expenses (paid)", f"{total_exp:,.2f}")
    with c3:
        st.metric("Net", f"{(total_income-total_exp):,.2f}")

    if not income_df.empty:
        incp = income_df.rename(columns={"paid_amount":"amount"}).copy()
        incp = periodize(incp, "date", period)
        incp.rename(columns={"amount":"Income"}, inplace=True)
        st.subheader(f"Income – {period}")
        st.dataframe(incp, use_container_width=True)
        if not incp.empty:
            st.bar_chart(incp.set_index(incp.columns[0]))
    else:
        st.info("No income records yet.")

    if not out_df.empty:
        outp = out_df.rename(columns={"paid_amount":"amount"}).copy()
        outp = periodize(outp, "date", period)
        outp.rename(columns={"amount":"Expenses"}, inplace=True)
        st.subheader(f"Expenses – {period}")
        st.dataframe(outp, use_container_width=True)
        if not outp.empty:
            st.bar_chart(outp.set_index(outp.columns[0]))
    else:
        st.info("No expense records yet.")

def page_cash_balances():
    st.header("💼 Cash & Bank – Opening / Closing")
    bal = load_csv(FILES["balances"], BAL_COLS)

    st.subheader("Set Opening Balances (one time or when needed)")
    with st.form("open_bal_form"):
        d = st.date_input("Effective Date", value=date.today(), key="bal_date")
        oc = st.number_input("Opening Cash (in hand)", min_value=0.0, step=0.1, key="bal_oc")
        ob = st.number_input("Opening Bank", min_value=0.0, step=0.1, key="bal_ob")
        submitted = st.form_submit_button("Save Opening Balances")
        if submitted:
            # Keep latest for that date (override)
            row = {"date": d.strftime(DATE_FMT), "opening_cash": oc, "opening_bank": ob}
            bal = bal[bal["date"] != row["date"]]
            bal = pd.concat([bal, pd.DataFrame([row])], ignore_index=True)
            save_csv(bal, FILES["balances"])
            st.success("Opening balances saved.")
            st.rerun()

    st.subheader("Current Running Balances")
    # compute current based on latest opening + paid flows
    services = load_csv(FILES["services"], SERVICE_COLS)
    txns = load_csv(FILES["transactions"], TXN_COLS)
    expenses = load_csv(FILES["expenses"], EXPENSE_COLS)
    suppliers = load_csv(FILES["suppliers"], SUP_COLS)

    latest_open = {"opening_cash":0.0,"opening_bank":0.0,"date":"-"}
    if not bal.empty:
        bal["date"] = pd.to_datetime(bal["date"], errors="coerce")
        row = bal.sort_values("date").iloc[-1]
        latest_open = {"opening_cash":money(row["opening_cash"]), "opening_bank":money(row["opening_bank"]), "date": row["date"].strftime(DATE_FMT)}

    # inflows (paid) by method
    def sum_paid(df, method):
        if df.empty: return 0.0
        return df.loc[df["method"]==method, "paid_amount"].fillna(0).astype(float).sum()

    cash_in = sum_paid(services,"Cash") + sum_paid(txns,"Cash")
    bank_in = sum_paid(services,"Bank") + sum_paid(txns,"Bank")

    cash_out = sum_paid(expenses,"Cash") + sum_paid(suppliers,"Cash")
    bank_out = sum_paid(expenses,"Bank") + sum_paid(suppliers,"Bank")

    cash_now = latest_open["opening_cash"] + cash_in - cash_out
    bank_now = latest_open["opening_bank"] + bank_in - bank_out

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Opening Cash (latest)", f"{latest_open['opening_cash']:,.2f}", help=f"From {latest_open['date']}")
    with c2:
        st.metric("Opening Bank (latest)", f"{latest_open['opening_bank']:,.2f}", help=f"From {latest_open['date']}")
    with c3:
        st.write("")

    c4, c5 = st.columns(2)
    with c4:
        st.metric("Cash in Hand (now)", f"{cash_now:,.2f}")
    with c5:
        st.metric("Cash at Bank (now)", f"{bank_now:,.2f}")

    st.subheader("Opening Balance Records")
    if not bal.empty:
        bshow = bal.copy()
        bshow["date"] = pd.to_datetime(bshow["date"], errors="coerce").dt.strftime(DATE_FMT)
        st.dataframe(bshow.sort_values("date"), use_container_width=True)
    else:
        st.info("No opening balance recorded yet.")

# ===============================
# ------------- APP -------------
# ===============================
def main():
    st.set_page_config(page_title="NANI Associates", layout="wide")
    if not st.session_state.logged_in:
        login_ui()
        return

    logout_btn()
    st.sidebar.markdown("### 📁 Menu")
    menu = st.sidebar.radio(
        "Menu",
        [
            "Service Entry",
            "Expense Entry",
            "Agents/Customers",
            "Suppliers",
            "Reports",
            "Cash & Balances",
            "Daily Data Logger",
        ],
        key="menu_radio"
    )

    if menu == "Service Entry":
        page_service_entry()
    elif menu == "Expense Entry":
        page_expense_entry()
    elif menu == "Agents/Customers":
        page_agents_customers()
    elif menu == "Suppliers":
        page_suppliers()
    elif menu == "Reports":
        page_reports()
    elif menu == "Cash & Balances":
        page_cash_balances()
    elif menu == "Daily Data Logger":
        page_daily_logger()
    else:
        st.header("Welcome")

if __name__ == "__main__":
    main()
