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

              
