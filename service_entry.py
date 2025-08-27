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
