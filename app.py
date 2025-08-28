import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------
# USER LOGIN SYSTEM
# -----------------------------
USER_CREDENTIALS = {"admin": "admin123"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.title("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.success("Login successful ✅")
            st.rerun()
        else:
            st.error("Invalid credentials ❌")

def logout_button():
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# -----------------------------
# DATA STORAGE
# -----------------------------
if "services" not in st.session_state: st.session_state.services = []
if "expenses" not in st.session_state: st.session_state.expenses = []
if "transactions" not in st.session_state: st.session_state.transactions = []
if "suppliers" not in st.session_state: st.session_state.suppliers = []

if "service_id" not in st.session_state: st.session_state.service_id = 1
if "expense_id" not in st.session_state: st.session_state.expense_id = 1
if "transaction_id" not in st.session_state: st.session_state.transaction_id = 1
if "supplier_id" not in st.session_state: st.session_state.supplier_id = 1

# -----------------------------
# HELPER: Edit/Delete + Export
# -----------------------------
def render_table_with_actions(df, key, data_list):
    if not df.empty:
        st.dataframe(df)

        # Export options
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(f"⬇️ Download {key} (CSV)", csv, f"{key.lower()}s.csv", "text/csv")

        excel = pd.ExcelWriter(f"{key.lower()}s.xlsx", engine="openpyxl")
        df.to_excel(excel, index=False, sheet_name=key)
        excel.close()
        with open(f"{key.lower()}s.xlsx", "rb") as f:
            st.download_button(f"⬇️ Download {key} (Excel)", f, f"{key.lower()}s.xlsx")

        # Delete
        delete_id = st.number_input(f"Enter ID to delete from {key}", min_value=1, step=1, key=f"del_{key}")
        if st.button(f"Delete {key}"):
            st.session_state[data_list] = [d for d in st.session_state[data_list] if d["ID"] != delete_id]
            st.success(f"{key} deleted ✅")
            st.rerun()

        # Edit
        edit_id = st.number_input(f"Enter ID to edit from {key}", min_value=1, step=1, key=f"edit_{key}")
        if st.button(f"Edit {key}"):
            record = next((d for d in st.session_state[data_list] if d["ID"] == edit_id), None)
            if record:
                st.write("### Edit Record")
                new_data = {}
                for k, v in record.items():
                    if k == "ID":
                        new_data[k] = v
                    elif isinstance(v, (int, float)):
                        new_data[k] = st.number_input(k, value=float(v), key=f"edit_{key}_{k}")
                    else:
                        new_data[k] = st.text_input(k, value=str(v), key=f"edit_{key}_{k}")
                if st.button("Save Changes"):
                    idx = next(i for i, d in enumerate(st.session_state[data_list]) if d["ID"] == edit_id)
                    st.session_state[data_list][idx] = new_data
                    st.success("Record updated ✅")
                    st.rerun()

# -----------------------------
# MAIN APP
# -----------------------------
def main_app():
    st.sidebar.title("📌 Navigation")
    menu = st.sidebar.radio("Go to", [
        "Service Entry",
        "Expense Entry",
        "Reports",
        "Daily Data Logger",
        "Agent/Customer Transactions",
        "Suppliers",
        "Balances"
    ])
    logout_button()

    # ----------------- SERVICE ENTRY -----------------
    if menu == "Service Entry":
        st.header("📝 Service Entry")
        entry_date = st.date_input("Date", datetime.today())
        customer = st.text_input("Customer/Agent Name")
        service_type = st.selectbox("Service Type", [
            "NEW PAN CARD", "CORRECTION PAN CARD",
            "NEW PASSPORT", "RENEWAL PASSPORT",
            "DIGITAL SIGNATURE", "VOTER ID",
            "NEW AADHAR CARD", "NAME CHANGE AADHAR CARD",
            "ADDRESS CHANGE IN AADHAR CARD", "DOB CHANGE IN AADHAR CARD",
            "AADHAR CARD PRINT", "OTHER ONLINE SERVICES"
        ])
        num_apps = st.number_input("No. of Applications", min_value=1, value=1)
        govt_amt = st.number_input("Govt Amount", min_value=0.0)
        paid_amt = st.number_input("Paid Amount", min_value=0.0)
        profit_amt = paid_amt - govt_amt

        if st.button("Add Service"):
            new_service = {
                "ID": st.session_state.service_id,
                "Date": entry_date.strftime("%Y-%m-%d"),
                "Customer/Agent": customer,
                "Service Type": service_type,
                "No. of Applications": num_apps,
                "Govt Amt": govt_amt,
                "Paid Amt": paid_amt,
                "Profit Amt": profit_amt
            }
            st.session_state.services.append(new_service)
            st.session_state.service_id += 1
            st.success("Service added ✅")

        df = pd.DataFrame(st.session_state.services)
        render_table_with_actions(df, "Service", "services")

    # ----------------- EXPENSE ENTRY -----------------
    elif menu == "Expense Entry":
        st.header("💰 Expense Entry")
        entry_date = st.date_input("Date", datetime.today(), key="exp_date")
        expense_name = st.selectbox("Expense Type", [
            "Salaries", "Office Rent", "Power Bill", "Water Bill",
            "Stationary", "Furniture Repair", "Printing Bill", "Food", "Other"
        ])
        expense_amt = st.number_input("Expense Amount", min_value=0.0)

        if st.button("Add Expense"):
            new_expense = {
                "ID": st.session_state.expense_id,
                "Date": entry_date.strftime("%Y-%m-%d"),
                "Expense Name": expense_name,
                "Amount": expense_amt,
            }
            st.session_state.expenses.append(new_expense)
            st.session_state.expense_id += 1
            st.success("Expense added ✅")

        df = pd.DataFrame(st.session_state.expenses)
        render_table_with_actions(df, "Expense", "expenses")

    # ----------------- REPORTS -----------------
    elif menu == "Reports":
        st.header("📊 Reports")
        df = pd.DataFrame(st.session_state.services)
        if not df.empty:
            filter_type = st.radio("Select Report Type", ["Daily", "Weekly", "Monthly"])
            today = datetime.today()
            if filter_type == "Daily":
                filtered = df[df["Date"] == today.strftime("%Y-%m-%d")]
            elif filter_type == "Weekly":
                week_ago = today - timedelta(days=7)
                filtered = df[df["Date"] >= week_ago.strftime("%Y-%m-%d")]
            else:
                month_ago = today - timedelta(days=30)
                filtered = df[df["Date"] >= month_ago.strftime("%Y-%m-%d")]
            st.write(filtered)

    # ----------------- DAILY DATA LOGGER -----------------
    elif menu == "Daily Data Logger":
        st.header("🗓 Daily Data Logger")
        df = pd.DataFrame(st.session_state.services)
        if not df.empty:
            log_date = st.date_input("Select Date", datetime.today(), key="log_date")
            df_day = df[df["Date"] == log_date.strftime("%Y-%m-%d")]
            if not df_day.empty:
                grouped = df_day.groupby("Service Type").agg({
                    "No. of Applications": "sum",
                    "Govt Amt": "sum",
                    "Paid Amt": "sum",
                    "Profit Amt": "sum"
                }).reset_index()
                st.write("### Service-wise Summary")
                st.dataframe(grouped)

                totals = df_day[["Govt Amt", "Paid Amt", "Profit Amt"]].sum()
                st.write("### Totals")
                st.write(totals)
            else:
                st.info("No services found for this date.")

    # ----------------- TRANSACTIONS -----------------
    elif menu == "Agent/Customer Transactions":
        st.header("🔄 Agent/Customer Transactions")
        entry_date = st.date_input("Date", datetime.today(), key="txn_date")
        name = st.text_input("Customer/Agent Name")
        status = st.selectbox("Status", ["Paid", "Pending", "Partial"])
        amount = st.number_input("Amount", min_value=0.0)

        if st.button("Add Transaction"):
            new_txn = {
                "ID": st.session_state.transaction_id,
                "Date": entry_date.strftime("%Y-%m-%d"),
                "Customer/Agent": name,
                "Status": status,
                "Amount": amount,
            }
            st.session_state.transactions.append(new_txn)
            st.session_state.transaction_id += 1
            st.success("Transaction added ✅")

        df = pd.DataFrame(st.session_state.transactions)
        render_table_with_actions(df, "Transaction", "transactions")

    # ----------------- SUPPLIERS -----------------
    elif menu == "Suppliers":
        st.header("🏢 Suppliers")
        entry_date = st.date_input("Date", datetime.today(), key="sup_date")
        supplier_name = st.text_input("Supplier Name")
        service_type = st.text_input("Service Type")
        paid_amt = st.number_input("Paid Amount", min_value=0.0)
        pending_amt = st.number_input("Pending Amount", min_value=0.0)
        partial_amt = st.number_input("Partial Amount", min_value=0.0)

        if st.button("Add Supplier"):
            new_supplier = {
                "ID": st.session_state.supplier_id,
                "Date": entry_date.strftime("%Y-%m-%d"),
                "Supplier Name": supplier_name,
                "Service Type": service_type,
                "Paid Amt": paid_amt,
                "Pending Amt": pending_amt,
                "Partial Amt": partial_amt,
            }
            st.session_state.suppliers.append(new_supplier)
            st.session_state.supplier_id += 1
            st.success("Supplier added ✅")

        df = pd.DataFrame(st.session_state.suppliers)
        render_table_with_actions(df, "Supplier", "suppliers")

    # ----------------- BALANCES -----------------
    elif menu == "Balances":
        st.header("💵 Balances Overview")
        services_df = pd.DataFrame(st.session_state.services)
        expenses_df = pd.DataFrame(st.session_state.expenses)
        if not services_df.empty:
            total_govt = services_df["Govt Amt"].sum()
            total_paid = services_df["Paid Amt"].sum()
            total_profit = services_df["Profit Amt"].sum()
        else:
            total_govt = total_paid = total_profit = 0
        total_expenses = expenses_df["Amount"].sum() if not expenses_df.empty else 0
        cash_in_hand = total_paid - total_expenses

        st.write(f"**Total Govt Amt:** {total_govt}")
        st.write(f"**Total Paid Amt:** {total_paid}")
        st.write(f"**Total Profit Amt:** {total_profit}")
        st.write(f"**Total Expenses:** {total_expenses}")
        st.write(f"**Cash in Hand:** {cash_in_hand}")

# -----------------------------
# APP RUNNER
# -----------------------------
if st.session_state.logged_in:
    main_app()
else:
    login_screen()
