def service_entry_page():
    st.header("📝 Service Entry Form")

    services = [
        "NEW PAN CARD", "CORRECTION PAN CARD", "THUMB PAN CARD", "GAZZETED PAN CARD",
        "BIRTH CERTIFICATES", "NEW PASSPORT", "MINOR PASSPORT", "REISSUE PASSPORT",
        "DIGITAL SIGNATURE", "NEW AADHAR CARD", "ADDRESS CHANGE", "DATE OF BIRTH CHANGE",
        "NAME CHANGE", "GENDER CHANGE", "NEW VOTER ID", "CORRECTION VOTER ID",
        "AADHAR PRINT", "ONLINE SERVICES"
    ]

    # Inputs
    entry_date = st.date_input("Date", value=date.today())
    customer = st.text_input("Customer Name")  # ✅ New Field
    service = st.selectbox("Service Type", services)
    expense = st.number_input("Expense (₹)", min_value=0.0, format="%.2f")
    income = st.number_input("Income (₹)", min_value=0.0, format="%.2f")
    remarks = st.text_area("Remarks")

    if st.button("💾 Save Entry"):
        profit = income - expense
        df = load_data()
        new_entry = {
            "Date": entry_date,
            "Customer": customer,   # ✅ Add to record
            "Service": service,
            "Expense": expense,
            "Income": income,
            "Profit": profit,
            "Remarks": remarks
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Entry saved successfully!")

    # Show entries
    st.subheader("📊 All Service Entries")
    df = load_data()
    st.dataframe(df)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Customer", "Service", "Expense", "Income", "Profit", "Remarks"])
        def service_entry_page():
    st.header("📝 Service Entry Form")

    services = [
        "NEW PAN CARD", "CORRECTION PAN CARD", "THUMB PAN CARD", "GAZZETED PAN CARD",
        "BIRTH CERTIFICATES", "NEW PASSPORT", "MINOR PASSPORT", "REISSUE PASSPORT",
        "DIGITAL SIGNATURE", "NEW AADHAR CARD", "ADDRESS CHANGE", "DATE OF BIRTH CHANGE",
        "NAME CHANGE", "GENDER CHANGE", "NEW VOTER ID", "CORRECTION VOTER ID",
        "AADHAR PRINT", "ONLINE SERVICES"
    ]

    entry_date = st.date_input("Date", value=date.today())
    customer = st.text_input("Customer Name")   # ✅ NEW FIELD
    service = st.selectbox("Service Type", services)
    expense = st.number_input("Expense (₹)", min_value=0.0, format="%.2f")
    income = st.number_input("Income (₹)", min_value=0.0, format="%.2f")
    remarks = st.text_area("Remarks")

    if st.button("💾 Save Entry"):
        profit = income - expense
        df = load_data()
        new_entry = {
            "Date": entry_date,
            "Customer": customer,   # ✅ Store Customer Name
            "Service": service,
            "Expense": expense,
            "Income": income,
            "Profit": profit,
            "Remarks": remarks
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Entry saved successfully!")

    st.subheader("📊 All Service Entries")
    df = load_data()
    st.dataframe(df)
    def service_entry_page():
    st.header("📝 Service Entry Form")

    date = st.date_input("Date")
    service_type = st.selectbox("Service Type", SERVICES)
    customer = st.text_input("Customer Name")
    expense = st.number_input("Expense (₹)", min_value=0.0, step=0.1)
    income = st.number_input("Income (₹)", min_value=0.0, step=0.1)
    remarks = st.text_area("Remarks")

    # 🔹 New Field: Payment Status
    payment_status = st.selectbox("Payment Status", ["Paid", "Pending", "Partial"])

    if st.button("Save Entry"):
        df = load_data()

        # Calculate Profit
        profit = income - expense

        new_entry = {
            "Date": str(date),
            "Service": service_type,
            "Customer": customer,
            "Expense": expense,
            "Income": income,
            "Profit": profit,
            "Remarks": remarks,
            "Payment Status": payment_status   # ✅ Save payment status
        }

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("✅ Entry Saved Successfully!")


