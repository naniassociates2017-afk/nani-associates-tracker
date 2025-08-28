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
    st.header("Transactions Report")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    if df.empty:
        st.warning("No transactions found yet.")
    else:
        # --- Debug: Show available columns ---
        # (Uncomment this line if you face errors)
        # st.write("Available columns:", df.columns.tolist())

        # Make sure "date" exists and is datetime
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
            if "application_no" in df.columns:
                df = df[df["application_no"].str.contains(search_app, case=False, na=False)]
            else:
                st.warning("⚠️ No 'application_no' column in table.")

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

            # --- Show Chart (only if report not empty) ---
            if not report.empty:
                st.subheader(f"{period} Chart")
                st.bar_chart(report.set_index(report.columns[0]))
        else:
            st.info("No data available after filters.")
                        # --- Show Report Table ---
            st.subheader(f"{period} Summary")
            st.dataframe(report)

            st.write(f"**Total Amount: {df['amount'].sum()}**")

            # --- Show Chart (only if report not empty) ---
            if not report.empty:
                st.subheader(f"{period} Chart")
                st.bar_chart(report.set_index(report.columns[0]))

                # --- Download Buttons ---
                st.subheader("Download Report")

                # Convert to CSV
                csv = report.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{period.lower()}_report.csv",
                    mime="text/csv",
                )

                # Convert to Excel
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
                page = st.sidebar.selectbox(

)
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

# Function to export all data
def export_all_data():
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")])
    combined_df = pd.DataFrame(columns=["time", "name", "amount"])
    for file in all_files:
        df = load_data(os.path.join(DATA_FOLDER, file))
        df["date"] = file.replace("data_", "").replace(".csv", "")
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df

# --- Streamlit Interface ---
st.title("Daily Data Logger")

# Input for new entry
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
    st.success("Entry saved!")

# Show today's data
st.subheader("Today's Entries")
st.dataframe(load_data(get_today_file()))

# Dropdown to view previous days
st.subheader("View Previous Days")
all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")], reverse=True)

if all_files:
    selected_file = st.selectbox("Select Date", all_files)
    st.dataframe(load_data(os.path.join(DATA_FOLDER, selected_file)))
else:
    st.write("No data files found.")

# Export all data
st.subheader("Export All Data")
if st.button("Download All Data as CSV"):
    combined_df = export_all_data()
    combined_df.to_csv(os.path.join(DATA_FOLDER, "all_data_combined.csv"), index=False)
    st.success("All data exported to 'data/all_data_combined.csv'")
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
        "name": name,
        "amount": amount
    }
    save_data(entry)
    st.success("Entry saved!")

# Show today's data
st.subheader("Today's Entries")
st.dataframe(load_data(get_today_file()))

# Dropdown to view previous days
st.subheader("View Previous Days")
all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")], reverse=True)

if all_files:
    selected_file = st.selectbox("Select Date", all_files)
    st.dataframe(load_data(os.path.join(DATA_FOLDER, selected_file)))
else:
    st.write("No data files found.")
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

# Function to load existing data
def load_data():
    file_path = get_today_file()
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["time", "name", "amount"])

# Function to save new entry
def save_data(entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(get_today_file(), index=False)

# App interface
st.title("Daily Data Logger")

name = st.text_input("Enter Name")
amount = st.number_input("Enter Amount", min_value=0)

if st.button("Save Entry"):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "name": name,
        "amount": amount
    }
    save_data(entry)
    st.success("Entry saved!")

# Show today's data
st.subheader("Today's Entries")
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

# Function to export all data
def export_all_data():
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")])
    combined_df = pd.DataFrame(columns=["time", "name", "amount"])
    for file in all_files:
        df = load_data(os.path.join(DATA_FOLDER, file))
        df["date"] = file.replace("data_", "").replace(".csv", "")
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df

# --- Streamlit Interface ---
st.title("Daily Data Logger")

# Input for new entry
st.subheader("Add New Entry")
name = st.text_input("Enter Name", key="name_input")
amount = st.number_input("Enter Amount", min_value=0, key="amount_input")

if st.button("Save Entry", key="save_entry_button"):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "name": name,
        "amount": amount
    }
    save_data(entry)
    st.success("Entry saved!")

# Show today's data
st.subheader("Today's Entries")
st.dataframe(load_data(get_today_file()), use_container_width=True)

# Dropdown to view previous days
st.subheader("View Previous Days")
all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")], reverse=True)

if all_files:
    selected_file = st.selectbox("Select Date", all_files, key="select_date_dropdown")
    st.dataframe(load_data(os.path.join(DATA_FOLDER, selected_file)), use_container_width=True)
else:
    st.write("No data files found.")

# Export all data
st.subheader("Export All Data")
if st.button("Download All Data as CSV", key="export_button"):
    combined_df = export_all_data()
    export_path = os.path.join(DATA_FOLDER, "all_data_combined.csv")
    combined_df.to_csv(export_path, index=False)
    st.success(f"All data exported to '{export_path}'")
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

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

# Function to export all data as a DataFrame
def export_all_data():
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")])
    combined_df = pd.DataFrame(columns=["time", "name", "amount"])
    for file in all_files:
        df = load_data(os.path.join(DATA_FOLDER, file))
        df["date"] = file.replace("data_", "").replace(".csv", "")
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df

# --- Streamlit Interface ---
st.title("Daily Data Logger")
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

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

# Function to export all data as a DataFrame (today's entries first)
def export_all_data():
    all_files = sorted([f for f in os.listdir(DATA_FOLDER) if f.startswith("data_") and f.endswith(".csv")])
    today_file = os.path.basename(get_today_file())
    if today_file in all_files:
        all_files.remove(today_file)
    all_files = [today_file] + all_files  # today first, then previous days

    combined_df = pd.DataFrame(columns=["time", "name", "amount", "date"])
    for file in all_files:
        df = load_data(os.path.join(DATA_FOLDER, file))
        df["date"] = file.replace("data_", "").replace(".csv", "")
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df

# --- S
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

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

# Function to export all data as a DataFrame (today first)
def export_all_data():
    all_files = sorted([f fo]()_




