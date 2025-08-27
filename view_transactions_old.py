elif page == "View Transactions":
    st.header("Transactions Report")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    if df.empty:
        st.warning("No transactions found yet.")
    else:
        # Ensure date column exists and is datetime
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
            df = df[df["application_no"].str.contains(search_app, case=False, na=False)]

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

            # --- Chart ---
            if not report.empty:
                st.subheader(f"{period} Chart")
                st.bar_chart(report.set_index(report.columns[0]))

                # --- Download Report ---
                csv = report.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{period.lower()}_report.csv",
                    mime="text/csv",
                )

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
        else:
            st.info("No data available after filters.")
