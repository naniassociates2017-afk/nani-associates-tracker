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
