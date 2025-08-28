import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Create a data folder if it doesn't exist
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# File path
DATA_FILE = os.path.join(DATA_FOLDER, "data.csv")

# Function to load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["date", "name", "amount"])

# Function to save new entry
def save_data(entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# App interface
st.title("Daily Data Logger")

name = st.text_input("Enter Name")
amount = st.number_input("Enter Amount", min_value=0)

if st.button("Save Entry"):
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "amount": amount
    }
    save_data(entry)
    st.success("Entry saved!")

# Show all data
st.subheader("All Entries")
st.dataframe(load_data())
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Create a data folder if it doesn't exist
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Function to get today's file path
def get_today_file():
    today_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DATA_FOLDER, f"data_{today_str}.csv")

# Function to load data from a specific file
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["time", "name", "amount"])

# Function to save new entry
def save_data(entry):
    df = load_data(get_today_file())
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(get_today_file(), index=False)

# App interface
st.title("Daily Data Logger")

# Input for new entry
st.subheader("Add New Entry")
name = st.text_input("Enter Name")
amount = st.number_input("Enter Amount", min_value=0)

if st.button("Save Entry"):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),

