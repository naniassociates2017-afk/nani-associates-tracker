import streamlit as st

# -------------------------
# USER CREDENTIALS
# -------------------------
USER_CREDENTIALS = {
    "nani": "Sony@1430",
    "admin": "admin123"
}

# -------------------------
# LOGIN SYSTEM
# -------------------------
def login_screen():
    st.title("🔐 Login Required")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login successful!")
            st.rerun()  # ✅ fixed (old: st.experimental_rerun)
        else:
            st.error("❌ Invalid username or password")
            st.stop()

# -------------------------
# MAIN APP
# -------------------------
def main_app():
    st.sidebar.success(f"👋 Welcome, {st.session_state.username}")
    st.sidebar.button("Logout", on_click=logout)

    st.title("📊 Nani Associates Tracker")

    st.write("This is your main application after successful login.")
    # 👉 Add your actual app features below
    st.write("✅ App is working fine with the new login system!")

# -------------------------
# LOGOUT FUNCTION
# -------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

# -------------------------
# APP ENTRY POINT
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login_screen()
