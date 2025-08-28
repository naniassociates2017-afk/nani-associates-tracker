# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from io import BytesIO

# ---------------------------
# Utilities
# ---------------------------
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def df_to_excel_bytes(df: pd.DataFrame, sheet_name="Sheet1") -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return out.getvalue()

def to_df(rows, columns):
    """rows: list of lists; columns: list of column names"""
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "services" not in st.session_state:
        st.session_state.services = []  # each row: [Date, Customer, Service Type, NoApps, GovtAmt, PaidAmt, ProfitAmt]
    if "expenses" not in st.session_state:
        st.session_state.expenses = []  # [Date, Category, Amount, Notes]
    if "transactions" not in st.session_state:
        st.session_state.transactions = []  # [Date, Customer/Agent, Service Type, Status(Paid/Pending/Partial), Amount, Notes]
    if "suppliers" not in st.session_state:
        st.session_state.suppliers = []  # [Date, SupplierName, ServiceType, PaidAmt, PendingAmt, PartialAmt, Notes]

# ---------------------------
# AUTH
# ---------------------------
def login_page():
    st.title("🔐 Login")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Login")
        if submitted:
            # Demo credentials; change as needed
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.success("Logged in successfully ✅")
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state.logged_in = False
    st.success("Logged out")
    st.rerun()

# ---------------------------
# SERVICE ENTRY
# ---------------------------
def page_service_entry():
    st.header("📝 Service Entry")
    with st.form("service_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today(), key="svc_date")
        customer = st.text_input("Customer / Agent", key="svc_customer")
        service_type = st.selectbox("Service Type", [
            "NEW PAN CARD", "CORRECTION PAN CARD",
            "NEW PASSPORT", "RENEWAL PASSPORT",
            "DIGITAL SIGNATURE", "VOTER ID",
            "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
            "ADDRESS CHANGE IN AADHAR CARD", "DOB CHANGE IN AADHAR CARD",
            "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
        ], key="svc_type")
        no_apps = st.number_input("No. of Applications", min_value=1, value=1, step=1, key="svc_apps")
        govt_amt_per = st.number_input("Government Amount (per app)", min_value=0.0, value=0.0, key="svc_govt_per")
        paid_amt_per = st.number_input("Paid Amount (per app)", min_value=0.0, value=0.0, key="svc_paid_per")
        notes = st.text_input("Notes (optional)", key="svc_notes")
        submit = st.form_submit_button("Add Service")

        if submit:
            total_govt = float(govt_amt_per) * int(no_apps)
            total_paid = float(paid_amt_per) * int(no_apps)
            profit = total_paid - total_govt
            st.session_state.services.append([
                entry_date.strftime("%Y-%m-%d"),
                customer,
                service_type,
                int(no_apps),
                round(total_govt,2),
                round(total_paid,2),
                round(profit,2),
                notes
            ])
            st.success("Service added ✅")
            st.experimental_rerun()

    st.subheader("Saved Services")
    svc_cols = ["Date","Customer","Service Type","No. of Apps","Govt Amt","Paid Amt","Profit Amt","Notes"]
    df_services = to_df(st.session_state.services, svc_cols)
    if df_services.empty:
        st.info("No services recorded yet.")
    else:
        st.dataframe(df_services, use_container_width=True)
        c1, c2, c3 = st.columns([2,1,1])
        with c1:
            idx_to_edit = st.number_input("Select row index to Edit", min_value=0, max_value=len(df_services)-1, step=1, key="svc_edit_idx")
        with c2:
            if st.button("Edit Selected Service", key="btn_edit_svc"):
                row = st.session_state.services[idx_to_edit]
                # show edit form
                with st.form(f"svc_edit_form_{idx_to_edit}", clear_on_submit=False):
                    e_date = st.date_input("Date", value=pd.to_datetime(row[0]).date(), key=f"edit_svc_date_{idx_to_edit}")
                    e_customer = st.text_input("Customer / Agent", value=row[1], key=f"edit_svc_cust_{idx_to_edit}")
                    e_service = st.selectbox("Service Type", [
                        "NEW PAN CARD", "CORRECTION PAN CARD",
                        "NEW PASSPORT", "RENEWAL PASSPORT",
                        "DIGITAL SIGNATURE", "VOTER ID",
                        "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
                        "ADDRESS CHANGE IN AADHAR CARD", "DOB CHANGE IN AADHAR CARD",
                        "AADHAR CARD PRINT", "BIRTH CERTIFICATE", "OTHER ONLINE SERVICES"
                    ], index=max(0,0), key=f"edit_svc_type_{idx_to_edit}")  # allow changing
                    e_noapps = st.number_input("No. of Applications", min_value=1, value=int(row[3]), key=f"edit_svc_apps_{idx_to_edit}")
                    e_govt = st.number_input("Government Amount (total)", min_value=0.0, value=float(row[4]), key=f"edit_svc_govt_{idx_to_edit}")
                    e_paid = st.number_input("Paid Amount (total)", min_value=0.0, value=float(row[5]), key=f"edit_svc_paid_{idx_to_edit}")
                    e_notes = st.text_input("Notes", value=row[7], key=f"edit_svc_notes_{idx_to_edit}")
                    save = st.form_submit_button("Save Changes")
                    if save:
                        e_profit = float(e_paid) - float(e_govt)
                        st.session_state.services[idx_to_edit] = [
                            e_date.strftime("%Y-%m-%d"),
                            e_customer,
                            e_service,
                            int(e_noapps),
                            round(float(e_govt),2),
                            round(float(e_paid),2),
                            round(float(e_profit),2),
                            e_notes
                        ]
                        st.success("Service updated ✅")
                        st.rerun()
        with c3:
            if st.button("Delete Selected Service", key="btn_del_svc"):
                st.session_state.services.pop(idx_to_edit)
                st.success("Service deleted ✅")
                st.rerun()

        # export buttons
        csv_bytes = df_to_csv_bytes(df_services)
        excel_bytes = df_to_excel_bytes(df_services, sheet_name="Services")
        st.download_button("⬇️ Download Services CSV", csv_bytes, "services.csv", key="dl_svc_csv")
        st.download_button("⬇️ Download Services Excel", excel_bytes, "services.xlsx", key="dl_svc_xlsx")

# ---------------------------
# EXPENSE ENTRY
# ---------------------------
def page_expense_entry():
    st.header("💸 Expense Entry")
    with st.form("expense_add_form", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today(), key="exp_date")
        category = st.selectbox("Expense Type", [
            "Salaries", "Office Rent", "Power Bill", "Water Bill",
            "Stationery", "Furniture Repair", "Printing Bill", "Food", "Other"
        ], key="exp_cat")
        amount = st.number_input("Amount", min_value=0.0, value=0.0, key="exp_amount")
        notes = st.text_input("Notes (optional)", key="exp_notes")
        submit = st.form_submit_button("Add Expense")
        if submit:
            st.session_state.expenses.append([
                entry_date.strftime("%Y-%m-%d"),
                category,
                round(float(amount),2),
                notes
            ])
            st.success("Expense added ✅")
            st.experimental_rerun()

    st.subheader("Saved Expenses")
    exp_cols = ["Date","Expense Type","Amount","Notes"]
    df_exp = to_df(st.session_state.expenses, exp_cols)
    if df_exp.empty:
        st.info("No expenses recorded yet.")
    else:
        st.dataframe(df_exp, use_container_width=True)
        c1, c2, c3 = st.columns([2,1,1])
        with c1:
            idx = st.number_input("Select Expense row index to Edit/Delete", min_value=0, max_value=len(df_exp)-1, step=1, key="exp_idx")
        with c2:
            if st.button("Edit Selected Expense", key="btn_edit_exp"):
                row = st.session_state.expenses[idx]
                with st.form(f"exp_edit_form_{idx}", clear_on_submit=False):
                    d = st.date_input("Date", value=pd.to_datetime(row[0]).date(), key=f"edit_exp_date_{idx}")
                    cat = st.selectbox("Expense Type", [
                        "Salaries", "Office Rent", "Power Bill", "Water Bill",
                        "Stationery", "Furniture Repair", "Printing Bill", "Food", "Other"
                    ], key=f"edit_exp_cat_{idx}")
                    amt = st.number_input("Amount", min_value=0.0, value=float(row[2]), key=f"edit_exp_amt_{idx}")
                    notes = st.text_input("Notes", value=row[3], key=f"edit_exp_notes_{idx}")
                    save = st.form_submit_button("Save Expense")
                    if save:
                        st.session_state.expenses[idx] = [d.strftime("%Y-%m-%d"), cat, round(float(amt),2), notes]
                        st.success("Expense updated ✅")
                        st.rerun()
        with c3:
            if st.button("Delete Selected Expense", key="btn_del_exp"):
                st.session_state.expenses.pop(idx)
                st.success("Expense deleted ✅")
                st.rerun()

        # export
        st.download_button("⬇️ Download Expenses CSV", df_to_csv_bytes(df_exp), "expenses.csv", key="dl_exp_csv")
        st.download_button("⬇️ Download Expenses Excel", df_to_excel_bytes(df_exp, "Expenses"), "expenses.xlsx", key="dl_exp_xlsx")

# ---------------------------
# AGENT/CUSTOMER TRANSACTIONS
# ---------------------------
def page_transactions():
    st.header("💳 Agent/Customer Transactions")
    with st.form("txn_add_form", clear_on_submit=True):
        t_date = st.date_input("Date", value=date.today(), key="txn_date")
        t_name = st.text_input("Customer/Agent Name", key="txn_name")
        t_service = st.selectbox("Service Type (optional)", ["", "NEW PAN CARD", "NEW PASSPORT", "NEW AADHAR CARD", "OTHER"], key="txn_service")
        t_status = st.selectbox("Status", ["Paid", "Pending", "Partial"], key="txn_status")
        t_amount = st.number_input("Amount", min_value=0.0, value=0.0, key="txn_amount")
        t_notes = st.text_input("Notes (optional)", key="txn_notes")
        add_txn = st.form_submit_button("Add Transaction")
        if add_txn:
            st.session_state.transactions.append([
                t_date.strftime("%Y-%m-%d"),
                t_name,
                t_service,
                t_status,
                round(float(t_amount),2),
                t_notes
            ])
            st.success("Transaction added ✅")
            st.rerun()

    st.subheader("Transactions (search & filter)")
    # filtering UI
    search_name = st.text_input("Search by Name", key="txn_search_name")
    filter_status = st.selectbox("Filter by Status", ["All","Paid","Pending","Partial"], key="txn_filter_status")
    txn_cols = ["Date","Customer/Agent","Service Type","Status","Amount","Notes"]
    df_txn = to_df(st.session_state.transactions, txn_cols)
    if not df_txn.empty:
        df_view = df_txn.copy()
        if search_name:
            df_view = df_view[df_view["Customer/Agent"].str.contains(search_name, case=False, na=False)]
        if filter_status != "All":
            df_view = df_view[df_view["Status"] == filter_status]
        st.dataframe(df_view, use_container_width=True)

        # Edit/Delete selected index
        c1, c2, c3 = st.columns([2,1,1])
        with c1:
            idx = st.number_input("Select Transaction index to Edit/Delete", min_value=0, max_value=len(df_view)-1, step=1, key="txn_idx")
            # map idx in filtered view back to original index
            filtered_indices = df_view.index.tolist()
            orig_idx = filtered_indices[idx] if filtered_indices else None
        with c2:
            if st.button("Edit Selected Transaction", key="btn_edit_txn") and orig_idx is not None:
                row = st.session_state.transactions[orig_idx]
                with st.form(f"txn_edit_form_{orig_idx}", clear_on_submit=False):
                    d = st.date_input("Date", value=pd.to_datetime(row[0]).date(), key=f"edit_txn_date_{orig_idx}")
                    name = st.text_input("Customer/Agent", value=row[1], key=f"edit_txn_name_{orig_idx}")
                    service = st.selectbox("Service Type", ["", "NEW PAN CARD", "NEW PASSPORT", "NEW AADHAR CARD", "OTHER"], index=0, key=f"edit_txn_service_{orig_idx}")
                    status = st.selectbox("Status", ["Paid","Pending","Partial"], index=["Paid","Pending","Partial"].index(row[3]) if row[3] in ["Paid","Pending","Partial"] else 0, key=f"edit_txn_status_{orig_idx}")
                    amount = st.number_input("Amount", min_value=0.0, value=float(row[4]), key=f"edit_txn_amt_{orig_idx}")
                    notes = st.text_input("Notes", value=row[5], key=f"edit_txn_notes_{orig_idx}")
                    save = st.form_submit_button("Save Transaction")
                    if save:
                        st.session_state.transactions[orig_idx] = [d.strftime("%Y-%m-%d"), name, service, status, round(float(amount),2), notes]
                        st.success("Transaction updated ✅")
                        st.rerun()
        with c3:
            if st.button("Delete Selected Transaction", key="btn_del_txn") and orig_idx is not None:
                st.session_state.transactions.pop(orig_idx)
                st.success("Transaction deleted ✅")
                st.rerun()

        # export
        st.download_button("⬇️ Download Transactions CSV", df_to_csv_bytes(df_view), "transactions.csv", key="dl_txn_csv")
        st.download_button("⬇️ Download Transactions Excel", df_to_excel_bytes(df_view, "Transactions"), "transactions.xlsx", key="dl_txn_xlsx")
    else:
        st.info("No transactions available.")

# ---------------------------
# SUPPLIERS
# ---------------------------
def page_suppliers():
    st.header("🏢 Suppliers")
    with st.form("supplier_add_form", clear_on_submit=True):
        s_date = st.date_input("Date", value=date.today(), key="sup_date")
        s_name = st.text_input("Supplier Name", key="sup_name")
        s_service = st.text_input("Service Type", key="sup_service")
        s_paid = st.number_input("Paid Amount", min_value=0.0, value=0.0, key="sup_paid")
        s_pending = st.number_input("Pending Amount", min_value=0.0, value=0.0, key="sup_pending")
        s_partial = st.number_input("Partial Amount", min_value=0.0, value=0.0, key="sup_partial")
        s_notes = st.text_input("Notes (optional)", key="sup_notes")
        add = st.form_submit_button("Add Supplier")
        if add:
            st.session_state.suppliers.append([
                s_date.strftime("%Y-%m-%d"),
                s_name,
                s_service,
                round(float(s_paid),2),
                round(float(s_pending),2),
                round(float(s_partial),2),
                s_notes
            ])
            st.success("Supplier added ✅")
            st.rerun()

    sup_cols = ["Date","Supplier","Service","Paid Amt","Pending Amt","Partial Amt","Notes"]
    df_sup = to_df(st.session_state.suppliers, sup_cols)
    if df_sup.empty:
        st.info("No suppliers recorded.")
    else:
        st.dataframe(df_sup, use_container_width=True)
        c1, c2 = st.columns([2,1])
        with c1:
            idx = st.number_input("Select supplier row to Edit/Delete", min_value=0, max_value=len(df_sup)-1, step=1, key="sup_idx")
        with c2:
            if st.button("Edit Selected Supplier", key="btn_edit_sup"):
                row = st.session_state.suppliers[idx]
                with st.form(f"sup_edit_form_{idx}", clear_on_submit=False):
                    d = st.date_input("Date", value=pd.to_datetime(row[0]).date(), key=f"edit_sup_date_{idx}")
                    name = st.text_input("Supplier Name", value=row[1], key=f"edit_sup_name_{idx}")
                    service = st.text_input("Service", value=row[2], key=f"edit_sup_service_{idx}")
                    paid = st.number_input("Paid Amount", min_value=0.0, value=float(row[3]), key=f"edit_sup_paid_{idx}")
                    pending = st.number_input("Pending Amount", min_value=0.0, value=float(row[4]), key=f"edit_sup_pending_{idx}")
                    partial = st.number_input("Partial Amount", min_value=0.0, value=float(row[5]), key=f"edit_sup_partial_{idx}")
                    notes = st.text_input("Notes", value=row[6], key=f"edit_sup_notes_{idx}")
                    save = st.form_submit_button("Save Supplier")
                    if save:
                        st.session_state.suppliers[idx] = [d.strftime("%Y-%m-%d"), name, service, round(float(paid),2), round(float(pending),2), round(float(partial),2), notes]
                        st.success("Supplier updated ✅")
                        st.rerun()
            if st.button("Delete Selected Supplier", key="btn_del_sup"):
                st.session_state.suppliers.pop(idx)
                st.success("Supplier deleted ✅")
                st.rerun()

        # export
        st.download_button("⬇️ Download Suppliers CSV", df_to_csv_bytes(df_sup), "suppliers.csv", key="dl_sup_csv")
        st.download_button("⬇️ Download Suppliers Excel", df_to_excel_bytes(df_sup, "Suppliers"), "suppliers.xlsx", key="dl_sup_xlsx")

# ---------------------------
# DAILY DATA LOGGER
# ---------------------------
def page_daily_logger():
    st.header("📅 Daily Data Logger (service-wise totals)")
    df_svc = to_df(st.session_state.services, ["Date","Customer","Service Type","No. of Apps","Govt Amt","Paid Amt","Profit Amt","Notes"])
    if df_svc.empty:
        st.info("No service records.")
        return
    sel_date = st.date_input("Select date to view", date.today(), key="logger_date")
    date_str = sel_date.strftime("%Y-%m-%d")
    df_day = df_svc[df_svc["Date"] == date_str]
    if df_day.empty:
        st.info("No services on selected date.")
        return
    grouped = df_day.groupby("Service Type").agg({
        "No. of Apps":"sum",
        "Govt Amt":"sum",
        "Paid Amt":"sum",
        "Profit Amt":"sum"
    }).reset_index()
    st.subheader(f"Service-wise totals for {date_str}")
    st.dataframe(grouped, use_container_width=True)
    st.write("Totals:")
    totals = grouped[["No. of Apps","Govt Amt","Paid Amt","Profit Amt"]].sum().to_dict()
    st.json({k: float(v) for k,v in totals.items()})

    # export
    st.download_button("⬇️ Download Daily Summary CSV", df_to_csv_bytes(grouped), f"daily_summary_{date_str}.csv", key="dl_daily_csv")
    st.download_button("⬇️ Download Daily Summary Excel", df_to_excel_bytes(grouped, "DailySummary"), f"daily_summary_{date_str}.xlsx", key="dl_daily_xlsx")

# ---------------------------
# REPORTS (with charts & filters)
# ---------------------------
def page_reports():
    st.header("📈 Reports - Daily / Weekly / Monthly / All")
    df_services = to_df(st.session_state.services, ["Date","Customer","Service Type","No. of Apps","Govt Amt","Paid Amt","Profit Amt","Notes"])
    df_exp = to_df(st.session_state.expenses, ["Date","Expense Type","Amount","Notes"])

    if df_services.empty and df_exp.empty:
        st.info("No data to report.")
        return

    range_choice = st.selectbox("Time Range", ["Daily","Weekly","Monthly","Custom","All"], key="rep_range")
    today = date.today()
    if range_choice == "Daily":
        start_date = today
        end_date = today
    elif range_choice == "Weekly":
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_choice == "Monthly":
        start_date = today - timedelta(days=30)
        end_date = today
    elif range_choice == "Custom":
        start_date = st.date_input("Start date", today - timedelta(days=30), key="rep_custom_start")
        end_date = st.date_input("End date", today, key="rep_custom_end")
    else:
        start_date = None
        end_date = None

    def apply_date_filter(df, col="Date"):
        if df.empty or start_date is None:
            return df
        df2 = df.copy()
        df2[col] = pd.to_datetime(df2[col])
        mask = (df2[col] >= pd.to_datetime(start_date)) & (df2[col] <= pd.to_datetime(end_date))
        return df2[mask]

    svc_f = apply_date_filter(df_services) if start_date else df_services
    exp_f = apply_date_filter(df_exp) if start_date else df_exp

    # optional agent filter:
    agent_filter = st.text_input("Filter by Agent/Customer (optional)", key="rep_agent")
    if agent_filter and not svc_f.empty:
        svc_f = svc_f[svc_f["Customer"].str.contains(agent_filter, case=False, na=False)]

    # show totals
    total_govt = float(svc_f["Govt Amt"].sum()) if not svc_f.empty else 0.0
    total_paid = float(svc_f["Paid Amt"].sum()) if not svc_f.empty else 0.0
    total_profit = float(svc_f["Profit Amt"].sum()) if not svc_f.empty else 0.0
    total_expenses = float(exp_f["Amount"].sum()) if not exp_f.empty else 0.0
    net_profit = total_profit - total_expenses

    st.metric("Total Govt Amount (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid by Customers (₹)", f"{total_paid:,.2f}")
    st.metric("Service Profit (₹)", f"{total_profit:,.2f}")
    st.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    st.metric("Net Profit / Loss (₹)", f"{net_profit:,.2f}")

    st.subheader("Service Details")
    st.dataframe(svc_f, use_container_width=True)
    st.subheader("Expense Details")
    st.dataframe(exp_f, use_container_width=True)

    # service-wise profit chart
    if not svc_f.empty:
        grp = svc_f.groupby("Service Type").agg({"No. of Apps":"sum","Govt Amt":"sum","Paid Amt":"sum","Profit Amt":"sum"}).reset_index()
        st.subheader("Service-wise Profit")
        st.bar_chart(grp.set_index("Service Type")["Profit Amt"])

    # monthly trend chart (Profit vs Expenses)
    if not svc_f.empty or not exp_f.empty:
        if not svc_f.empty:
            tmp_s = svc_f.copy()
            tmp_s["Month"] = pd.to_datetime(tmp_s["Date"]).dt.to_period("M").astype(str)
            monthly_profit = tmp_s.groupby("Month")["Profit Amt"].sum().reset_index()
        else:
            monthly_profit = pd.DataFrame(columns=["Month","Profit Amt"])
        if not exp_f.empty:
            tmp_e = exp_f.copy()
            tmp_e["Month"] = pd.to_datetime(tmp_e["Date"]).dt.to_period("M").astype(str)
            monthly_exp = tmp_e.groupby("Month")["Amount"].sum().reset_index()
        else:
            monthly_exp = pd.DataFrame(columns=["Month","Amount"])
        merged = pd.merge(monthly_profit, monthly_exp, left_on="Month", right_on="Month", how="outer").fillna(0).sort_values("Month")
        if not merged.empty:
            merged = merged.rename(columns={"Profit Amt":"Profit","Amount":"Expenses"})
            st.subheader("Monthly Profit vs Expenses")
            st.line_chart(merged.set_index("Month")[["Profit","Expenses"]])

    # exports
    if not svc_f.empty:
        st.download_button("⬇️ Download Report - Services CSV", df_to_csv_bytes(svc_f), "report_services.csv", key="dl_report_svc")
        st.download_button("⬇️ Download Report - Services Excel", df_to_excel_bytes(svc_f, "Services"), "report_services.xlsx", key="dl_report_svc_xlsx")
    if not exp_f.empty:
        st.download_button("⬇️ Download Report - Expenses CSV", df_to_csv_bytes(exp_f), "report_expenses.csv", key="dl_report_exp")
        st.download_button("⬇️ Download Report - Expenses Excel", df_to_excel_bytes(exp_f, "Expenses"), "report_expenses.xlsx", key="dl_report_exp_xlsx")

# ---------------------------
# BALANCES
# ---------------------------
def page_balances():
    st.header("💼 Balances Overview")
    df_svc = to_df(st.session_state.services, ["Date","Customer","Service Type","No. of Apps","Govt Amt","Paid Amt","Profit Amt","Notes"])
    df_exp = to_df(st.session_state.expenses, ["Date","Expense Type","Amount","Notes"])
    total_govt = float(df_svc["Govt Amt"].sum()) if not df_svc.empty else 0.0
    total_paid = float(df_svc["Paid Amt"].sum()) if not df_svc.empty else 0.0
    total_profit = float(df_svc["Profit Amt"].sum()) if not df_svc.empty else 0.0
    total_expenses = float(df_exp["Amount"].sum()) if not df_exp.empty else 0.0
    cash_in_hand = total_paid - total_expenses
    st.metric("Total Govt Amount (₹)", f"{total_govt:,.2f}")
    st.metric("Total Paid by Customers (₹)", f"{total_paid:,.2f}")
    st.metric("Total Service Profit (₹)", f"{total_profit:,.2f}")
    st.metric("Total Expenses (₹)", f"{total_expenses:,.2f}")
    st.metric("Cash in Hand (simplified) (₹)", f"{cash_in_hand:,.2f}")

# ---------------------------
# MAIN
# ---------------------------
def main():
    st.set_page_config(page_title="NANI ASSOCIATES - Tracker", layout="wide")
    init_session_state = init_session_state  # avoid flake warning
    init_session_state()
    if not st.session_state.logged_in:
        login_page()
        return

    st.sidebar.title("📌 Menu")
    st.sidebar.text(f"Logged in as: admin")
    if st.sidebar.button("Logout", key="logout_btn"):
        logout()

    page = st.sidebar.radio("Navigate", [
        "Service Entry",
        "Expense Entry",
        "Transactions",
        "Reports",
        "Daily Data Logger",
        "Suppliers",
        "Balances"
    ], index=0)

    if page == "Service Entry":
        page_service_entry()
    elif page == "Expense Entry":
        page_expense_entry()
    elif page == "Transactions":
        page_transactions()
    elif page == "Reports":
        page_reports()
    elif page == "Daily Data Logger":
        page_daily_logger()
    elif page == "Suppliers":
        page_suppliers()
    elif page == "Balances":
        page_balances()

if __name__ == "__main__":
    main()
