import streamlit as st
from service_entry import service_entry_page
from expense_entry import expense_entry_page
from reports import reports_page

def main():
    st.title("📊 NANI ASSOCIATES BUSINESS TRACKER")

    menu = ["Service Entry", "Expense Entry", "Reports"]
    choice = st.sidebar.radio("📂 Menu", menu)

    if choice == "Service Entry":
        service_entry_page()
    elif choice == "Expense Entry":
        expense_entry_page()
    elif choice == "Reports":
        reports_page()

if __name__ == "__main__":
    main()
elif page == "View Transactions":
    st.header("Transactions Report")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    if df.empty:
        st.warning("No transactions found yet.")
    else:
        # --- Debug: Show available columns ---
        # (Uncomment this line if you face errors)
        # st.write("Available columns:", df.columns.tolist())

        # Make sure "date" exists and is datetime
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        else:
            st.error("❌ 'date' column not found in transactions table.")
            st.stop()

        # --- Filters ---
        agents = df["agent"].dropna().unique().tolist()
        agents.sort()
        selected_agent = st.selectbox("Select Agent", ["All"] + agents)
        if selected_agent != "All":
            df = df[df["agent"] == selected_agent]

        products = df["product"].dropna().unique().tolist()
        products.sort()
        selected_product = st.selectbox("Select Product", ["All"] + products)
        if selected_product != "All":
            df = df[df["product"] == selected_product]

        suppliers = df["supplier"].dropna().unique().tolist()
        suppliers.sort()
        selected_supplier = st.selectbox("Select Supplier", ["All"] + suppliers)
        if selected_supplier != "All":
            df = df[df["supplier"] == selected_supplier]

        # --- Application Number Search ---
        search_app = st.text_input("Search by Application Number")
        if search_app:
            if "application_no" in df.columns:
                df = df[df["application_no"].str.contains(search_app, case=False, na=False)]
            else:
                st.warning("⚠️ No 'application_no' column in table.")

        # --- Period Selection ---
        period = st.radio("Select Period", ["Daily", "Weekly", "Monthly"])

        if not df.empty:
            if period == "Daily":
                report = df.groupby(df["date"].dt.date).agg({"amount": "sum"}).reset_index()
                report.rename(columns={"date": "Date", "amount": "Total Amount"}, inplace=True)

            elif period == "Weekly":
                report = df.groupby(df["date"].dt.to_period("W")).agg({"amount": "sum"}).reset_index()
                report["date"] = report["date"].astype(str)
                report.rename(columns={"date": "Week", "amount": "Total Amount"}, inplace=True)

            elif period == "Monthly":
                report = df.groupby(df["date"].dt.to_period("M")).agg({"amount": "sum"}).reset_index()
                report["date"] = report["date"].astype(str)
                report.rename(columns={"date": "Month", "amount": "Total Amount"}, inplace=True)

            # --- Show Report Table ---
            st.subheader(f"{period} Summary")
            st.dataframe(report)

            st.write(f"**Total Amount: {df['amount'].sum()}**")

            # --- Show Chart (only if report not empty) ---
            if not report.empty:
                st.subheader(f"{period} Chart")
                st.bar_chart(report.set_index(report.columns[0]))
        else:
            st.info("No data available after filters.")
                        # --- Show Report Table ---
            st.subheader(f"{period} Summary")
            st.dataframe(report)

            st.write(f"**Total Amount: {df['amount'].sum()}**")

            # --- Show Chart (only if report not empty) ---
            if not report.empty:
                st.subheader(f"{period} Chart")
                st.bar_chart(report.set_index(report.columns[0]))

                # --- Download Buttons ---
                st.subheader("Download Report")

                # Convert to CSV
                csv = report.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{period.lower()}_report.csv",
                    mime="text/csv",
                )

                # Convert to Excel
                import io
                from openpyxl import Workbook

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    report.to_excel(writer, index=False, sheet_name="Report")
                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"{period.lower()}_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                page = st.sidebar.selectbox(

)


