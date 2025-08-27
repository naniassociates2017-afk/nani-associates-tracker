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
    st.header("All Transactions")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    # Agent filter
    agents = df["agent"].unique().tolist()
    agents.sort()
    selected_agent = st.selectbox("Select Agent", ["All"] + agents)

    if selected_agent != "All":
        df = df[df["agent"] == selected_agent]

    st.dataframe(df)

    # Optional: show totals for the filtered data
    total_amount = df["amount"].sum()
    st.write(f"**Total Amount: {total_amount}**")
    if st.session_state.get("logged_in"):
    page = st.sidebar.selectbox("Navigation", ["Add Transaction", "View Transactions", "Manage Agents", "Backup"])

    if page == "Add Transaction":
        # add transaction code here...

    elif page == "View Transactions":
        st.header("All Transactions")
        df = pd.read_sql("SELECT * FROM transactions", conn)
        st.dataframe(df)

