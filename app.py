import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -------------------
# LOGIN / LOGOUT
# -------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":   # ✅ credentials here
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# Logout button
st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
st.sidebar.write("✅ Logged in as admin")

# -------------------
# DATA FOLDER
# -------------------
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def get_today_file():
    today_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DATA_FOLDER, f"data_{today_str}.csv")

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["time", "name", "amount"])

def save_data(entry):
    df = load_data(get_today_file())
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(get_today_file(), index=False)

def export_all_data():
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")], reverse=True)
    combined_df = pd.DataFrame(columns=["time", "name", "amount", "date"])
    for file in all_files:
        df = load_data(os.path.join(DATA_FOLDER, file))
        df["date"] = file.replace("data_", "").replace(".csv", "")
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df

# -------------------
# MAIN MENU
# -------------------
menu = ["Service Entry", "Expense Entry", "Reports", "Daily Data Logger"]
choice = st.sidebar.radio("📂 Menu", menu)

# -------------------
# SERVICE ENTRY (placeholder)
# -------------------
if choice == "Service Entry":
    st.title("📝 Service Entry")
    st.info("This section will handle Service Entry. (Placeholder)")

# -------------------
# EXPENSE ENTRY (placeholder)
# -------------------
elif choice == "Expense Entry":
    st.title("💰 Expense Entry")
    st.info("This section will handle Expense Entry. (Placeholder)")

# -------------------
# REPORTS (placeholder)
# -------------------
elif choice == "Reports":
    st.title("📊 Reports")
    st.info("This section will handle Reports. (Placeholder)")

# -------------------
# DAILY DATA LOGGER
# -------------------
elif choice == "Daily Data Logger":
    st.title("📒 Daily Data Logger")

    # Add new entry
    st.subheader("Add New Entry")
    name = st.text_input("Enter Name")
    amount = st.number_input("Enter Amount", min_value=0)

    if st.button("Save Entry"):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "name": name,
            "amount": amount
        }
        save_data(entry)
        st.success("✅ Entry saved!")

    # Show today's entries
    st.subheader("Today's Entries")
    today_df = load_data(get_today_file())
    st.dataframe(today_df, use_container_width=True)

    # Delete an entry
    if not today_df.empty:
        st.subheader("Delete an Entry (Today Only)")
        delete_index = st.selectbox(
            "Select entry",
            today_df["time"] + " | " + today_df["name"] + " | " + today_df["amount"].astype(str),
        )
        if st.button("Delete Entry"):
            row_to_delete = today_df.index[
                (today_df["time"] + " | " + today_df["name"] + " | " + today_df["amount"].astype(str)) == delete_index
            ][0]
            today_df = today_df.drop(row_to_delete).reset_index(drop=True)
            today_df.to_csv(get_today_file(), index=False)
            st.success("Entry deleted!")
            st.rerun()

    # View previous days
    st.subheader("View Previous Days")
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")], reverse=True)
    if all_files:
        selected_file = st.selectbox("Select Date", all_files)
        st.dataframe(load_data(os.path.join(DATA_FOLDER, selected_file)), use_container_width=True)
    else:
        st.write("No data files found.")

    # Export all data
    st.subheader("Export All Data")
    combined_df = export_all_data()
    if not combined_df.empty:
        csv_bytes = combined_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download All Data as CSV",
            data=csv_bytes,
            file_name="all_data_combined.csv",
            mime="text/csv"
        )
    else:
        st.write("No data available to export.")
        elif menu == "Reports":
    st.header("📊 Reports")

    st.subheader("Filter Transactions")

    # Date filter
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    # Agent filter
    agent = st.text_input("Agent Name (optional)")

    if st.button("View Report"):
        all_files = sorted([f for f in os.listdir("transactions") if f.endswith(".csv")])
        if not all_files:
            st.warning("No transactions found yet.")
        else:
            import pandas as pd
            df_list = [pd.read_csv(os.path.join("transactions", f)) for f in all_files]
            df = pd.concat(df_list, ignore_index=True)

            # Convert date column if present
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # Apply filters
            if start_date:
                df = df[df["Date"] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df["Date"] <= pd.to_datetime(end_date)]
            if agent:
                df = df[df["Agent"].str.contains(agent, case=False, na=False)]

            if df.empty:
                st.warning("No records match your filters.")
            else:
                st.success(f"Found {len(df)} records.")
                st.dataframe(df)

                # Charts
                st.subheader("📈 Charts")
                if "Amount" in df.columns and "Agent" in df.columns:
                    chart_data = df.groupby("Agent")["Amount"].sum().reset_index()
                    st.bar_chart(chart_data.set_index("Agent"))

                # Download options
                st.subheader("⬇️ Download")
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "report.csv", "text/csv")

                # Excel
                from io import BytesIO
                import pandas as pd
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Report")
                excel_data = output.getvalue()
                st.download_button("Download Excel", excel_data, "report.xlsx")

                # PDF (simple text export)
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                pdf_file = BytesIO()
                c = canvas.Canvas(pdf_file, pagesize=letter)
                text = c.beginText(50, 750)
                text.setFont("Helvetica", 10)
                for row in df.to_string(index=False).split("\n"):
                    text.textLine(row)
                c.drawText(text)
                c.showPage()
                c.save()
                st.download_button("Download PDF", pdf_file.getvalue(), "report.pdf")

