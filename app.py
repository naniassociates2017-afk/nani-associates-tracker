# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

# -----------------------------
# CONFIG / AUTH
# -----------------------------
USER_CREDENTIALS = {"admin": "admin123"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -----------------------------
# INITIALIZE STORAGE (in-memory via session_state)
# -----------------------------
def _init_lists():
    if "services" not in st.session_state:
        st.session_state.services = []  # dicts with keys below
    if "expenses" not in st.session_state:
        st.session_state.expenses = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    if "suppliers" not in st.session_state:
        st.session_state.suppliers = []

    if "service_id" not in st.session_state:
        st.session_state.service_id = 1
    if "expense_id" not in st.session_state:
        st.session_state.expense_id = 1
    if "transaction_id" not in st.session_state:
        st.session_state.transaction_id = 1
    if "supplier_id" not in st.session_state:
        st.session_state.supplier_id = 1

_init_lists()

# -----------------------------
# HELPERS
# -----------------------------
def to_df(list_of_dicts, expected_cols=None):
    if len(list_of_dicts) == 0:
        return pd.DataFrame(columns=expected_cols or [])
    return pd.DataFrame(list_of_dicts)

def download_bytes(obj_bytes, filename, label):
    st.download_button(label, data=obj_bytes, file_name=filename)

def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel_bytes(df, sheet_name="Sheet1"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def find_index_by_id(list_of_dicts, rec_id):
    for i, d in enumerate(list_of_dicts):
        if d.get("ID") == rec_id:
            return i
    return None

def safe_sum(series):
    if series.empty:
        return 0.0
    return series.astype(float).sum()

# -----------------------------
# AUTH UI
# -----------------------------
def login_screen():
    st.title("🔐 NANI ASSOCIATES - Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.success("Login successful ✅")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials ❌")

def logout_action():
    st.session_state.logged_in = False
    st.experimental_rerun()

# -----------------------------
# RENDER + ACTION HELPERS
# -----------------------------
def render_table_actions(list_key, title):
    """
    Show dataframe, export buttons and edit/delete controls for a list stored in session_state[list_key].
    Returns nothing. Uses unique widget keys based on title.
    """
    data_list = st.session_state.get(list_key, [])
    df = to_df(data_list)
    if df.empty:
        st.info(f"No {title} records yet.")
        return

    st.subheader(f"{title} Records")
    st.dataframe(df, use_container_width=True)

    # Export CSV
    csv_bytes = df_to_csv_bytes(df)
    download_bytes(csv_bytes, f"{title.lower().replace(' ','_')}.csv", f"⬇️ Download {title} CSV")

    # Export Excel
    excel_bytes = df_to_excel_bytes(df, sheet_name=title[:31])
    download_bytes(excel_bytes, f"{title.lower().replace(' ','_')}.xlsx", f"⬇️ Download {title} Excel")

    # Delete
    delete_id = st.number_input(f"Enter {title} ID to delete", min_value=1, step=1, key=f"del_{title}")
    if st.button(f"🗑️ Delete {title} Record", key=f"del_btn_{title}"):
        idx = find_index_by_id(data_list, delete_id)
        if idx is not None:
            data_list.pop(idx)
            st.success(f"{title} ID {delete_id} deleted ✅")
            st.experimental_rerun()
        else:
            st.error("ID not found")

    # Edit
    edit_id = st.number_input(f"Enter {title} ID to edit", min_value=1, step=1, key=f"edit_{title}")
    if st.button(f"✏️ Edit {title} Record", key=f"edit_btn_{title}"):
        idx = find_index_by_id(data_list, edit_id)
        if idx is None:
            st.error("ID not found")
        else:
            record = data_list[idx]
            st.write("### Edit record fields — change and Save")
            updated = {}
            for k, v in record.items():
                if k == "ID":
                    updated[k] = v
                    st.write(f"ID: {v}")
                elif k == "Date":
                    # date field
                    try:
                        val = datetime.strptime(v, "%Y-%m-%d").date()
                    except Exception:
                        val = datetime.today().date()
                    new_val = st.date_input(k, val, key=f"edit_{title}_{k}")
                    updated[k] = new_val.strftime("%Y-%m-%d")
                elif isinstance(v, (int, float)):
                    new_val = st.number_input(k, value=float(v), key=f"edit_{title}_{k}")
                    updated[k] = new_val
                else:
                    new_val = st.text_input(k, value=str(v), key=f"edit_{title}_{k}")
                    updated[k] = new_val
            if st.button("💾 Save changes", key=f"save_edit_{title}"):
                st.session_state[list_key][idx] = updated
                st.success("Record updated ✅")
                st.experimental_rerun()

# -----------------------------
# PAGES
# -----------------------------
def page_service_entry():
    st.header("📝 Service Entry")
    entry_date = st.date_input("Date", datetime.today(), key="svc_date")
    customer = st.text_input("Customer / Agent", key="svc_customer")
    service_type = st.selectbox("Service Type", [
        "NEW PAN CARD", "CORRECTION PAN CARD",
        "NEW PASSPORT", "RENEWAL PASSPORT",
        "DIGITAL SIGNATURE", "VOTER ID",
        "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
        "ADDRESS CHANGE IN AADHAR CARD", "DOB CHANGE IN AADHAR CARD",
        "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
    ], key="svc_type")
    num_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1, key="svc_num_apps")
    govt_amt_per = st.number_input("Government Amount (per application)", min_value=0.0, value=0.0, key="svc_govt_per")
    paid_amt_per = st.number_input("Paid Amount (per application)", min_value=0.0, value=0.0, key="svc_paid_per")

    total_govt = govt_amt_per * num_apps
    total_paid = paid_amt_per * num_apps
    total_profit = total_paid - total_govt

    st.metric("Total Govt (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid (₹)", f"{total_paid:,.2f}")
    st.metric("Total Profit (₹)", f"{total_profit:,.2f}")

    if st.button("➕ Add Service", key="svc_add_btn"):
        rec = {
            "ID": st.session_state.service_id,
            "Date": entry_date.strftime("%Y-%m-%d"),
            "Customer/Agent": customer,
            "Service Type": service_type,
            "No. of Applications": int(num_apps),
            "Govt Amt": float(total_govt),
            "Paid Amt": float(total_paid),
            "Profit Amt": float(total_profit)
        }
        st.session_state.services.append(rec)
        st.session_state.service_id += 1
        st.success("Service saved ✅")
        st.experimental_rerun()

    # Show table + actions
    render_table_with_actions(to_df(st.session_state.services), "Service", "services")
    # Note: render_table_with_actions expects list key; so provide different overload below:
    # We'll call the helper that expects list key correctly:
    # (We used to pass df; fix: call with actual list key)
    # But above rendered incorrectly; correct call below:
    # Re-render using list key version:
    st.write("")  # spacer
    render_table_with_actions_list("services", "Service")

def render_table_with_actions_list(list_key, title):
    """Same as render_table_with_actions but accepts list_key (string)"""
    data_list = st.session_state.get(list_key, [])
    df = to_df(data_list)
    if df.empty:
        st.info(f"No {title} records yet.")
        return

    st.subheader(f"{title} Records")
    st.dataframe(df, use_container_width=True)

    # Export buttons
    csv_bytes = df_to_csv_bytes(df)
    st.download_button(f"⬇️ Download {title} CSV", csv_bytes, f"{title.lower().replace(' ','_')}.csv", key=f"dl_csv_{title}")

    excel_bytes = df_to_excel_bytes(df, sheet_name=title[:31])
    st.download_button(f"⬇️ Download {title} Excel", excel_bytes, f"{title.lower().replace(' ','_')}.xlsx", key=f"dl_xlsx_{title}")

    # Delete control
    delete_id = st.number_input(f"Enter {title} ID to delete", min_value=1, step=1, key=f"del_{title}_list")
    if st.button(f"🗑️ Delete {title}", key=f"del_btn_{title}_list"):
        idx = find_index_by_id(data_list, delete_id)
        if idx is not None:
            data_list.pop(idx)
            st.success(f"{title} ID {delete_id} deleted ✅")
            st.experimental_rerun()
        else:
            st.error("ID not found")

    # Edit control
    edit_id = st.number_input(f"Enter {title} ID to edit", min_value=1, step=1, key=f"edit_{title}_list")
    if st.button(f"✏️ Edit {title}", key=f"edit_btn_{title}_list"):
        idx = find_index_by_id(data_list, edit_id)
        if idx is None:
            st.error("ID not found")
        else:
            record = data_list[idx]
            st.write("### Edit record — change fields and Save")
            updated = {}
            for k, v in record.items():
                if k == "ID":
                    updated[k] = v
                    st.write(f"ID: {v}")
                elif k == "Date":
                    try:
                        val = datetime.strptime(v, "%Y-%m-%d").date()
                    except Exception:
                        val = datetime.today().date()
                    new_val = st.date_input(k, val, key=f"edit_{title}_{k}")
                    updated[k] = new_val.strftime("%Y-%m-%d")
                elif isinstance(v, (int, float)):
                    new_val = st.number_input(k, value=float(v), key=f"edit_{title}_{k}")
                    updated[k] = new_val
                else:
                    new_val = st.text_input(k, value=str(v), key=f"edit_{title}_{k}")
                    updated[k] = new_val
            if st.button("💾 Save changes", key=f"save_edit_{title}_list"):
                st.session_state[list_key][idx] = updated
                st.success("Record updated ✅")
                st.experimental_rerun()

# -----------------------------
# EXPENSE PAGE
# -----------------------------
def page_expenses():
    st.header("💸 Expense Entry")
    entry_date = st.date_input("Date", datetime.today(), key="exp_date")
    expense_type = st.selectbox("Expense Type", [
        "Salaries", "Office Rent", "Power Bill", "Water Bill",
        "Stationery", "Furniture Repair", "Printing Bill", "Food", "Other"
    ], key="exp_type")
    if expense_type == "Other":
        expense_name = st.text_input("Expense Name (Other)", key="exp_other_name")
    else:
        expense_name = expense_type
    amount = st.number_input("Amount (₹)", min_value=0.0, key="exp_amount")

    if st.button("➕ Add Expense", key="exp_add_btn"):
        rec = {
            "ID": st.session_state.expense_id,
            "Date": entry_date.strftime("%Y-%m-%d"),
            "Expense Name": expense_name,
            "Amount": float(amount)
        }
        st.session_state.expenses.append(rec)
        st.session_state.expense_id += 1
        st.success("Expense saved ✅")
        st.experimental_rerun()

    render_table_with_actions_list("expenses", "Expense")

# -----------------------------
# REPORTS PAGE (with charts & filters)
# -----------------------------
def page_reports():
    st.header("📊 Reports & Analysis")
    services_df = to_df(st.session_state.services, expected_cols=[
        "ID","Date","Customer/Agent","Service Type","No. of Applications","Govt Amt","Paid Amt","Profit Amt"
    ])
    expenses_df = to_df(st.session_state.expenses, expected_cols=["ID","Date","Expense Name","Amount"])

    if services_df.empty and expenses_df.empty:
        st.info("No data to report.")
        return

    # Filters
    col1, col2 = st.columns([2,1])
    with col1:
        report_range = st.selectbox("Range", ["Daily","Weekly","Monthly","Custom","All"], key="rep_range")
    with col2:
        agent_filter = st.text_input("Filter by Agent/Customer (optional)", key="rep_agent")

    # determine date filter
    today = datetime.today().date()
    if report_range == "Daily":
        start = today
    elif report_range == "Weekly":
        start = today - timedelta(days=7)
    elif report_range == "Monthly":
        start = today - timedelta(days=30)
    elif report_range == "Custom":
        start = st.date_input("Start date", today - timedelta(days=30), key="rep_custom_start")
        end = st.date_input("End date", today, key="rep_custom_end")
    else:
        start = None

    # apply filters
    df_s = services_df.copy()
    if start is not None:
        if report_range == "Custom":
            df_s = df_s[(pd.to_datetime(df_s["Date"]) >= pd.to_datetime(start)) & (pd.to_datetime(df_s["Date"]) <= pd.to_datetime(end))]
        else:
            df_s = df_s[pd.to_datetime(df_s["Date"]) >= pd.to_datetime(start)]
    if agent_filter:
        df_s = df_s[df_s["Customer/Agent"].str.contains(agent_filter, case=False, na=False)]

    df_e = expenses_df.copy()
    if start is not None:
        if report_range == "Custom":
            df_e = df_e[(pd.to_datetime(df_e["Date"]) >= pd.to_datetime(start)) & (pd.to_datetime(df_e["Date"]) <= pd.to_datetime(end))]
        else:
            df_e = df_e[pd.to_datetime(df_e["Date"]) >= pd.to_datetime(start)]

    st.subheader("Service Records")
    st.dataframe(df_s, use_container_width=True)
    st.subheader("Expense Records")
    st.dataframe(df_e, use_container_width=True)

    # summary metrics
    total_govt = safe_sum(df_s["Govt Amt"]) if "Govt Amt" in df_s.columns else 0
    total_paid = safe_sum(df_s["Paid Amt"]) if "Paid Amt" in df_s.columns else 0
    total_profit = safe_sum(df_s["Profit Amt"]) if "Profit Amt" in df_s.columns else 0
    total_expenses = safe_sum(df_e["Amount"]) if "Amount" in df_e.columns else 0
    net_profit = total_profit - total_expenses

    st.subheader("Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Govt Amount (₹)", f"{total_govt:,.2f}")
    c2.metric("Customer Paid (₹)", f"{total_paid:,.2f}")
    c3.metric("Service Profit (₹)", f"{total_profit:,.2f}")
    c4.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")

    st.metric("Net Profit / Loss (₹)", f"{net_profit:,.2f}")

    # Charts: service-wise profit
    if not df_s.empty:
        grp = df_s.groupby("Service Type").agg({"No. of Applications":"sum","Govt Amt":"sum","Paid Amt":"sum","Profit Amt":"sum"}).reset_index()
        st.subheader("Service-wise Profit (₹)")
        st.bar_chart(grp.set_index("Service Type")["Profit Amt"])

        # Monthly trend: aggregate by month for Profit and Expenses
        df_s["Date"] = pd.to_datetime(df_s["Date"])
        df_s["Month"] = df_s["Date"].dt.to_period("M").astype(str)
        monthly_profit = df_s.groupby("Month")["Profit Amt"].sum().reset_index()
        df_e["Date"] = pd.to_datetime(df_e["Date"])
        df_e["Month"] = df_e["Date"].dt.to_period("M").astype(str)
        monthly_exp = df_e.groupby("Month")["Amount"].sum().reset_index()

        if not monthly_profit.empty:
            merged = pd.merge(monthly_profit, monthly_exp, on="Month", how="outer").fillna(0).sort_values("Month")
            merged = merged.rename(columns={"Profit Amt":"Profit", "Amount":"Expenses"})
            st.subheader("Monthly Profit vs Expenses")
            st.line_chart(merged.set_index("Month")[["Profit","Expenses"]])

# -----------------------------
# DAILY DATA LOGGER (service-wise)
# -----------------------------
def page_daily_logger():
    st.header("📅 Daily Data Logger - Service-wise Summary")
    df = to_df(st.session_state.services)
    if df.empty:
        st.info("No services recorded yet.")
        return

    chosen_date = st.date_input("Select Date", datetime.today(), key="log_date")
    date_str = chosen_date.strftime("%Y-%m-%d")
    df_day = df[df["Date"] == date_str]
    if df_day.empty:
        st.info(f"No services on {date_str}")
        return

    grouped = df_day.groupby("Service Type").agg({
        "No. of Applications":"sum",
        "Govt Amt":"sum",
        "Paid Amt":"sum",
        "Profit Amt":"sum"
    }).reset_index()
    st.subheader(f"Service-wise totals for {date_str}")
    st.dataframe(grouped, use_container_width=True)

    totals = {
        "Govt Amt": grouped["Govt Amt"].sum(),
        "Paid Amt": grouped["Paid Amt"].sum(),
        "Profit Amt": grouped["Profit Amt"].sum()
    }
    st.write("### Totals")
    st.write(totals)

# -----------------------------
# TRANSACTIONS PAGE
# -----------------------------
def page_transactions():
    st.header("🔄 Agent / Customer Transactions")
    entry_date = st.date_input("Date", datetime.today(), key="txn_date")
    name = st.text_input("Customer/Agent Name", key="txn_name")
    status = st.selectbox("Status", ["Paid","Pending","Partial"], key="txn_status")
    amount = st.number_input("Amount (₹)", min_value=0.0, key="txn_amount")

    if st.button("➕ Add Transaction", key="txn_add"):
        rec = {
            "ID": st.session_state.transaction_id,
            "Date": entry_date.strftime("%Y-%m-%d"),
            "Customer/Agent": name,
            "Status": status,
            "Amount": float(amount)
        }
        st.session_state.transactions.append(rec)
        st.session_state.transaction_id += 1
        st.success("Transaction saved ✅")
        st.experimental_rerun()

    render_table_with_actions_list("transactions", "Transaction")

# -----------------------------
# SUPPLIERS PAGE
# -----------------------------
def page_suppliers():
    st.header("🏢 Suppliers")
    entry_date = st.date_input("Date", datetime.today(), key="sup_date")
    supplier_name = st.text_input("Supplier Name", key="sup_name")
    service_type = st.selectbox("Service Type", ["PAN","Passport","Aadhaar","Birth Certificate","Other"], key="sup_serv")
    paid_amt = st.number_input("Paid Amount (₹)", min_value=0.0, key="sup_paid")
    pending_amt = st.number_input("Pending Amount (₹)", min_value=0.0, key="sup_pending")
    partial_amt = st.number_input("Partial Amount (₹)", min_value=0.0, key="sup_partial")

    if st.button("➕ Add Supplier", key="sup_add"):
        rec = {
            "ID": st.session_state.supplier_id,
            "Date": entry_date.strftime("%Y-%m-%d"),
            "Supplier Name": supplier_name,
            "Service Type": service_type,
            "Paid Amt": float(paid_amt),
            "Pending Amt": float(pending_amt),
            "Partial Amt": float(partial_amt)
        }
        st.session_state.suppliers.append(rec)
        st.session_state.supplier_id += 1
        st.success("Supplier saved ✅")
        st.experimental_rerun()

    render_table_with_actions_list("suppliers", "Supplier")

# -----------------------------
# BALANCES PAGE
# -----------------------------
def page_balances():
    st.header("💼 Balances & Cash")
    services_df = to_df(st.session_state.services)
    expenses_df = to_df(st.session_state.expenses)

    total_govt = safe_sum(services_df.get("Govt Amt", pd.Series([], dtype=float)))
    total_paid = safe_sum(services_df.get("Paid Amt", pd.Series([], dtype=float)))
    total_service_profit = safe_sum(services_df.get("Profit Amt", pd.Series([], dtype=float)))
    total_expenses = safe_sum(expenses_df.get("Amount", pd.Series([], dtype=float)))

    net_profit = total_service_profit - total_expenses
    cash_in_hand = total_paid - total_expenses  # simplistic cash calc

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Govt Amt (₹)", f"{total_govt:,.2f}")
    c2.metric("Total Paid by Customers (₹)", f"{total_paid:,.2f}")
    c3.metric("Service Profit (₹)", f"{total_service_profit:,.2f}")

    c4, c5 = st.columns(2)
    c4.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    c5.metric("Net Profit / Loss (₹)", f"{net_profit:,.2f}")

    st.write(f"Cash in Hand (simplified): ₹{cash_in_hand:,.2f}")

# -----------------------------
# SMALL UTILITY: wrapper for list-key rendering
# -----------------------------
def render_table_with_actions_list(list_key, title):
    data_list = st.session_state.get(list_key, [])
    df = to_df(data_list)
    if df.empty:
        st.info(f"No {title} records yet.")
        return

    st.subheader(f"{title} Records")
    st.dataframe(df, use_container_width=True)

    # Export CSV
    csv_bytes = df_to_csv_bytes(df)
    st.download_button(f"⬇️ Download {title} CSV", csv_bytes, f"{title.lower().replace(' ','_')}.csv", key=f"dl_{title}_csv")

    # Export Excel
    excel_bytes = df_to_excel_bytes(df, sheet_name=title[:31])
    st.download_button(f"⬇️ Download {title} Excel", excel_bytes, f"{title.lower().replace(' ','_')}.xlsx", key=f"dl_{title}_xlsx")

    # Delete
    delete_id = st.number_input(f"Enter {title} ID to delete", min_value=1, step=1, key=f"del_{list_key}")
    if st.button(f"🗑️ Delete {title}", key=f"del_{list_key}_btn"):
        idx = find_index_by_id(data_list, delete_id)
        if idx is not None:
            data_list.pop(idx)
            st.success(f"{title} ID {delete_id} deleted ✅")
            st.experimental_rerun()
        else:
            st.error("ID not found")

    # Edit
    edit_id = st.number_input(f"Enter {title} ID to edit", min_value=1, step=1, key=f"edit_{list_key}")
    if st.button(f"✏️ Edit {title}", key=f"edit_{list_key}_btn"):
        idx = find_index_by_id(data_list, edit_id)
        if idx is None:
            st.error("ID not found")
        else:
            record = data_list[idx]
            st.write("### Edit record — change fields and Save")
            updated = {}
            for k, v in record.items():
                if k == "ID":
                    updated[k] = v
                    st.write(f"ID: {v}")
                elif k == "Date":
                    try:
                        val = datetime.strptime(v, "%Y-%m-%d").date()
                    except Exception:
                        val = datetime.today().date()
                    new_val = st.date_input(k, val, key=f"edit_{list_key}_{k}")
                    updated[k] = new_val.strftime("%Y-%m-%d")
                elif isinstance(v, (int, float)):
                    new_val = st.number_input(k, value=float(v), key=f"edit_{list_key}_{k}")
                    updated[k] = new_val
                else:
                    new_val = st.text_input(k, value=str(v), key=f"edit_{list_key}_{k}")
                    updated[k] = new_val
            if st.button("💾 Save changes", key=f"save_edit_{list_key}_btn"):
                st.session_state[list_key][idx] = updated
                st.success("Record updated ✅")
                st.experimental_rerun()

# -----------------------------
# ROUTER / ENTRYPOINT
# -----------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES - Tracker", layout="wide")
    if not st.session_state.logged_in:
        login_screen()
        return

    st.sidebar.title("🧭 Menu")
    page = st.sidebar.radio("Select", [
        "Service Entry",
        "Expense Entry",
        "Reports",
        "Daily Data Logger",
        "Agent/Customer Transactions",
        "Suppliers",
        "Balances",
        "Logout"
    ], index=0)

    if page == "Service Entry":
        page_service_entry()
    elif page == "Expense Entry":
        page_expenses()
    elif page == "Reports":
        page_reports()
    elif page == "Daily Data Logger":
        page_daily_logger()
    elif page == "Agent/Customer Transactions":
        page_transactions()
    elif page == "Suppliers":
        page_suppliers()
    elif page == "Balances":
        page_balances()
    elif page == "Logout":
        logout_action()

if __name__ == "__main__":
    main()
