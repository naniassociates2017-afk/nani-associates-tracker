import pandas as pd

FILE_NAME = "data.csv"

def load_data():
    try:
        return pd.read_csv(FILE_NAME)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Date", "Type", "Customer", "Service", "Expense", "Income",
            "Profit", "Payment Status", "Amount Received", "Pending Amount", "Remarks"
        ])

def save_data(df):
    df.to_csv(FILE_NAME, index=False)
