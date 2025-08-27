import streamlit as st

# -------------------- LOGIN FUNCTION --------------------
def login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:   # Show login form only if not logged in
        st.sidebar.subheader("🔑 Login")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login", key="login_button"):
            if username == "admin" and password == "admin123":  # change credentials here
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.sidebar.success(f"Welcome, {username}")
            else:
                st.sidebar.error("Invalid username or password")
    else:
        st.sidebar.success(f"✅ Logged in as {st.session_state['username']}")
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""


# -------------------- MAIN FUNCTION --------------------
def main():
    st.sidebar.title("📂 Menu")

    # Call login function
    login()

    # Show menu only if logged in
    if st.session_state.get("logged_in", False):
        choice = st.sidebar.radio("Navigation", ["Service Entry", "Expense Entry", "Reports"])

        if choice == "Service Entry":
            st.title("📝 Service Entry")
            # your service entry code here

        elif choice == "Expense Entry":
            st.title("💰 Expense Entry")
            # your expense entry code here

        elif choice == "Reports":
            st.title("📊 Reports")
            # your reports code here


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    main()
