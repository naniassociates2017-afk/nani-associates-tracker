
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from pathlib import Path

DB_PATH = "nani_associates.db"

SERVICES = ["PAN Card", "Passport", "Aadhaar Card", "Digital Signature", "Other Online Service"]

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            t_date TEXT NOT NULL,
            service TEXT NOT NULL,
            customer_name TEXT,
            contact_no TEXT,
            transaction_id TEXT,
            service_charge REAL DEFAULT 0,
            govt_fee REAL DEFAULT 0,
            other_expenses REAL DEFAULT 0,
            remarks TEXT
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS business_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            firm_name TEXT,
            address TEXT,
            proprietor TEXT,
            phone TEXT
        );
    """)
    # ensure single row for business info
    conn.execute("INSERT OR IGNORE INTO business_info (id, firm_name, address, proprietor, phone) VALUES (1, '', '', '', '')")
    conn.commit()
    return conn

def rupees(x):
    try:
        return f"₹{float(x):,.2f}"
    except:
        return "₹0.00"

def add_transaction(conn, data):
    conn.execute("""
        INSERT INTO transactions (t_date, service, customer_name, contact_no, transaction_id,
                                  service_charge, govt_fee, other_expenses, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["t_date"], data["service"], data.get("customer_name",""), data.get("contact_no",""),
        data.get("transaction_id",""), float(data.get("service_charge",0) or 0),
        float(data.get("govt_fee",0) or 0), float(data.get("other_expenses",0) or 0),
        data.get("remarks","")
    ))
    conn.commit()

def update_transaction(conn, tid, data):
    conn.execute("""
        UPDATE transactions
        SET t_date=?, service=?, customer_name=?, contact_no=?, transaction_id=?,
            service_charge=?, govt_fee=?, other_expenses=?, remarks=?
        WHERE id=?
    """, (
        data["t_date"], data["service"], data.get("customer_name",""), data.get("contact_no",""),
        data.get("transaction_id",""), float(data.get("service_charge",0) or 0),
        float(data.get("govt_fee",0) or 0), float(data.get("other_expenses",0) or 0),
        data.get("remarks",""), tid
    ))
    conn.commit()

def delete_transaction(conn, tid):
    conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit()

def fetch_df(conn, where_clause="", params=()):
    query = f"""
        SELECT
            id,
            t_date as Date,
            service as Service,
            customer_name as "Customer Name",
            contact_no as "Contact No",
            transaction_id as "Transaction ID",
            service_charge as "Service Charge (₹)",
            govt_fee as "Govt. Fee (₹)",
            other_expenses as "Other Expenses (₹)",
            (service_charge) as "Total Income (₹)",
            (service_charge - (govt_fee + other_expenses)) as "Profit (₹)",
            remarks as Remarks
        FROM transactions
        {where_clause}
        ORDER BY datetime(t_date) DESC, id DESC
    """
    return pd.read_sql_query(query, conn, params=params)

def month_name(m):
    return date(1900, m, 1).strftime("%B")

def export_to_excel(conn, path):
    df = fetch_df(conn)
    df_no_id = df.drop(columns=["id"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_no_id.to_excel(writer, sheet_name="Daily Transactions", index=False)
        # Monthly summary
        if not df_no_id.empty:
            df_no_id["Date"] = pd.to_datetime(df_no_id["Date"]).dt.date
            df_no_id["Month"] = pd.to_datetime(df_no_id["Date"]).dt.to_period("M").dt.to_timestamp()
            monthly = df_no_id.groupby("Month").agg(
                **{
                    "Total Income (₹)": ("Total Income (₹)", "sum"),
                    "Total Expenses (₹)": (["Govt. Fee (₹)", "Other Expenses (₹)"], "sum"),
                    "Net Profit (₹)": ("Profit (₹)", "sum")
                }
            )
        else:
            monthly = pd.DataFrame(columns=["Total Income (₹)", "Total Expenses (₹)", "Net Profit (₹)"])
        # Fix multiindex if created
        if isinstance(monthly.columns, pd.MultiIndex):
            monthly.columns = ["Total Income (₹)", "Total Expenses (₹)", "Net Profit (₹)"]
        monthly = monthly.reset_index()
        monthly["Month"] = monthly["Month"].dt.strftime("%Y-%m")
        monthly.to_excel(writer, sheet_name="Monthly Summary", index=False)

        # Service-wise
        service = df_no_id.groupby("Service").agg(
            **{
                "Total Transactions": ("Service", "count"),
                "Total Income (₹)": ("Total Income (₹)", "sum"),
                "Total Expenses (₹)": (["Govt. Fee (₹)", "Other Expenses (₹)"], "sum"),
                "Net Profit (₹)": ("Profit (₹)", "sum")
            }
        )
        if isinstance(service.columns, pd.MultiIndex):
            service.columns = ["Total Transactions", "Total Income (₹)", "Total Expenses (₹)", "Net Profit (₹)"]
        service = service.reset_index()
        service.to_excel(writer, sheet_name="Service-wise Report", index=False)

st.set_page_config(page_title="NANI ASSOCIATES - Business Tracker", layout="wide")

st.title("🧾 NANI ASSOCIATES – Income & Expense Tracker")
conn = get_conn()

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", [
    "Add Transaction",
    "View Transactions",
    "Monthly Summary",
    "Service-wise Report",
    "Export",
    "Settings"
])

# Settings page - business info
if page == "Settings":
    st.subheader("Business Information")
    cur = conn.execute("SELECT firm_name, address, proprietor, phone FROM business_info WHERE id=1")
    firm_name, address, proprietor, phone = cur.fetchone()
    with st.form("biz_info"):
        firm_name = st.text_input("Firm Name", value=firm_name or "NANI ASSOCIATES")
        address = st.text_area("Address", value=address or "Shop No 13, SC Complex, Station Road, Narasaraopet, Palnadu Dist, AP - 522601")
        proprietor = st.text_input("Proprietor", value=proprietor or "Chirumilla Mallikarjunarao")
        phone = st.text_input("Contact Number", value=phone or "8143014218")
        submitted = st.form_submit_button("Save")
        if submitted:
            conn.execute("""
                INSERT INTO business_info (id, firm_name, address, proprietor, phone)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET firm_name=excluded.firm_name,
                                             address=excluded.address,
                                             proprietor=excluded.proprietor,
                                             phone=excluded.phone;
            """, (firm_name, address, proprietor, phone))
            conn.commit()
            st.success("Saved!")

# Add transaction
if page == "Add Transaction":
    st.subheader("Record a Transaction")
    with st.form("txn_form", clear_on_submit=True):
        t_date = st.date_input("Date", value=date.today())
        service = st.selectbox("Service", SERVICES, index=0)
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name")
        with col2:
            contact_no = st.text_input("Contact No")
        col3, col4 = st.columns(2)
        with col3:
            transaction_id = st.text_input("Transaction ID / Ref No")
            service_charge = st.number_input("Service Charge (₹)", min_value=0.0, value=0.0, step=10.0)
        with col4:
            govt_fee = st.number_input("Govt. Fee (₹)", min_value=0.0, value=0.0, step=10.0)
            other_expenses = st.number_input("Other Expenses (₹)", min_value=0.0, value=0.0, step=10.0)
        remarks = st.text_area("Remarks")
        submitted = st.form_submit_button("Save Transaction")
        if submitted:
            add_transaction(conn, {
                "t_date": t_date.isoformat(),
                "service": service,
                "customer_name": customer_name,
                "contact_no": contact_no,
                "transaction_id": transaction_id,
                "service_charge": service_charge,
                "govt_fee": govt_fee,
                "other_expenses": other_expenses,
                "remarks": remarks
            })
            st.success("Transaction saved!")

# View transactions with filters and edit/delete
if page == "View Transactions":
    st.subheader("Transactions")
    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            from_date = st.date_input("From Date", value=date.today().replace(day=1))
        with c2:
            to_date = st.date_input("To Date", value=date.today())
        with c3:
            service_filter = st.multiselect("Service", SERVICES, default=[])

    where = "WHERE date(t_date) BETWEEN ? AND ?"
    params = [from_date.isoformat(), to_date.isoformat()]
    if service_filter:
        placeholders = ",".join(["?"]*len(service_filter))
        where += f" AND service IN ({placeholders})"
        params.extend(service_filter)

    df = fetch_df(conn, where, tuple(params))
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)

    # Edit/Delete
    st.markdown("**Edit / Delete**")
    if not df.empty:
        ids = df["id"].tolist()
        selected_id = st.selectbox("Select transaction ID", ids)
        selected_row = df[df["id"] == selected_id].iloc[0]
        with st.form("edit_form"):
            t_date = st.date_input("Date", value=pd.to_datetime(selected_row["Date"]).date())
            service = st.selectbox("Service", SERVICES, index=SERVICES.index(selected_row["Service"]) if selected_row["Service"] in SERVICES else 0)
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name", value=selected_row["Customer Name"] or "")
            with col2:
                contact_no = st.text_input("Contact No", value=selected_row["Contact No"] or "")
            col3, col4 = st.columns(2)
            with col3:
                transaction_id = st.text_input("Transaction ID / Ref No", value=selected_row["Transaction ID"] or "")
                service_charge = st.number_input("Service Charge (₹)", min_value=0.0, value=float(selected_row["Service Charge (₹)"] or 0), step=10.0)
            with col4:
                govt_fee = st.number_input("Govt. Fee (₹)", min_value=0.0, value=float(selected_row["Govt. Fee (₹)"] or 0), step=10.0)
                other_expenses = st.number_input("Other Expenses (₹)", min_value=0.0, value=float(selected_row["Other Expenses (₹)"] or 0), step=10.0)
            remarks = st.text_area("Remarks", value=selected_row["Remarks"] or "")
            colA, colB = st.columns(2)
            with colA:
                save_btn = st.form_submit_button("Save Changes")
            with colB:
                del_btn = st.form_submit_button("Delete Transaction")
            if save_btn:
                update_transaction(conn, int(selected_id), {
                    "t_date": t_date.isoformat(),
                    "service": service,
                    "customer_name": customer_name,
                    "contact_no": contact_no,
                    "transaction_id": transaction_id,
                    "service_charge": service_charge,
                    "govt_fee": govt_fee,
                    "other_expenses": other_expenses,
                    "remarks": remarks
                })
                st.success("Updated! Refresh the page to see changes.")
            if del_btn:
                delete_transaction(conn, int(selected_id))
                st.success("Deleted! Refresh the page to update the table.")

# Monthly Summary
if page == "Monthly Summary":
    st.subheader("Monthly Profit & Loss")
    df_all = fetch_df(conn)
    if df_all.empty:
        st.info("No data yet. Add transactions first.")
    else:
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        df_all["Month"] = df_all["Date"].dt.to_period("M").astype(str)
        monthly = df_all.groupby("Month").agg(
            **{
                "Total Income (₹)": ("Total Income (₹)", "sum"),
                "Total Expenses (₹)": (["Govt. Fee (₹)", "Other Expenses (₹)"], "sum"),
                "Net Profit (₹)": ("Profit (₹)", "sum")
            }
        )
        if isinstance(monthly.columns, pd.MultiIndex):
            monthly.columns = ["Total Income (₹)", "Total Expenses (₹)", "Net Profit (₹)"]
        monthly = monthly.reset_index()
        st.dataframe(monthly, use_container_width=True)

# Service-wise report
if page == "Service-wise Report":
    st.subheader("Service-wise Performance")
    df_all = fetch_df(conn)
    if df_all.empty:
        st.info("No data yet. Add transactions first.")
    else:
        service = df_all.groupby("Service").agg(
            **{
                "Total Transactions": ("Service", "count"),
                "Total Income (₹)": ("Total Income (₹)", "sum"),
                "Total Expenses (₹)": (["Govt. Fee (₹)", "Other Expenses (₹)"], "sum"),
                "Net Profit (₹)": ("Profit (₹)", "sum")
            }
        )
        if isinstance(service.columns, pd.MultiIndex):
            service.columns = ["Total Transactions", "Total Income (₹)", "Total Expenses (₹)", "Net Profit (₹)"]
        service = service.reset_index()
        st.dataframe(service, use_container_width=True)

# Export
if page == "Export":
    st.subheader("Export Data")
    df = fetch_df(conn)
    st.write(f"Total transactions: **{len(df)}**")
    xlsx_name = "NANI_Associates_Business_Tracker.xlsx"
    export_to_excel(conn, xlsx_name)
    with open(xlsx_name, "rb") as f:
        st.download_button("Download Excel", f, file_name=xlsx_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("Excel includes Daily Transactions, Monthly Summary, and Service-wise Report.")
