import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- LOGIN / LOGOUT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_button"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()  # Stop execution until login
else:
    st.sidebar.button("Logout", key="logout_button", on_click=lambda: st.session_state.update({"logged_in": False}))
    st.sidebar.write(f"Logged in as admin")

# --- DATA FOLDER SETUP ---
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# --- HELPER FUNCTIONS ---
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
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")])
    today_file = os.path.basename(get_today_file())
    if today_file in all_files:
        all_files.remove(today_file)
    all_files = [today_file] + all_files  # today first

    combined_df = pd.DataFrame(columns=["time", "name", "amount", "date"])
    for file in all_files:
        df = load_data(os.path.join(DATA_FOLDER, file))
        df["date"] = file.replace("data_", "").replace(".csv", "")
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df

# --- MAIN APP ---
st.title("Daily Data Logger")

# Add new entry
st.subheader("Add New Entry")
name = st.text_input("Enter Name", key="entry_name_input")
amount = st.number_input("Enter Amount", min_value=0, key="entry_amount_input")

if st.button("Save Entry", key="save_entry_button"):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "name": name,
        "amount": amount
    }
    save_data(entry)
    st.success("Entry saved!")

# Show today's entries
st.subheader("Today's Entries")
today_df = load_data(get_today_file())
st.dataframe(today_df, use_container_width=True)

# Delete an entry (today only)
st.subheader("Delete an Entry (Today Only)")
if not today_df.empty:
    delete_index = st.selectbox(
        "Select the entry to delete",
        today_df["time"] + " | " + today_df["name"] + " | " + today_df["amount"].astype(str),
        key="delete_entry_selectbox"
    )
    if st.button("Delete Entry", key="delete_button"):
        row_to_delete = today_df.index[
            (today_df["time"] + " | " + today_df["name"] + " | " + today_df["amount"].astype(str)) == delete_index
        ][0]
        today_df = today_df.drop(row_to_delete).reset_index(drop=True)
        today_df.to_csv(get_today_file(), index=False)
        st.success("Entry deleted!")
        st.experimental_rerun()
else:
    st.write("No entries to delete today.")

# View previous days
st.subheader("View Previous Days")
all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")], reverse=True)
if all_files:
    selected_file = st.selectbox("Select Date", all_files, key="view_date_selectbox")
    st.dataframe(load_data(os.path.join(DATA_FOLDER, selected_file)), use_container_width=True)
else:
    st.write("No data files found.")

# Export all data
st.subheader("Export All Data")
combined_df = export_all_data()
if not combined_df.empty:
    csv_bytes = combined_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download All Data as CSV",
        data=csv_bytes,
        file_name="all_data_combined.csv",
        mime="text/csv",
        key="download_button"
    )
else:
    st.write("No data available to export.")
