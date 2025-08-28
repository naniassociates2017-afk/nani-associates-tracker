# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from io import BytesIO
import uuid

# ===============================
# ---------- SETTINGS -----------
# ===============================
APP_TITLE = "📊 NANI ASSOCIATES – BUSINESS TRACKER"
DATA_DIR = "data"
FILES = {
    "services": os.path.join(DATA_DIR, "services.csv"),
    "expenses": os.path.join(DATA_DIR, "expenses.csv"),
    "transactions": os.path.join(DATA_DIR, "transactions.csv"),  # agents/customers
    "suppliers": os.path.join(DATA_DIR, "suppliers.csv"),
    "balances": os.path.join(DATA_DIR, "balances.csv"),
}
DATE_FMT = "%Y-%m-%d"

# Login credentials
VALID_USER = "admin"
VALID_PASS = "admin123"

# ===============================
# ---------- UTILITIES ----------
# ===============================
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_csv(path: str, cols: list) -> pd.DataFrame:
    ensure_data_dir()
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            # make sure any missing expected co
