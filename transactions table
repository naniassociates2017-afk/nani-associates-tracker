import streamlit as st
import pandas as pd
import sqlite3

# --- Database connection ---
conn = sqlite3.connect("services.db", check_same_thread=False)
c = conn.cursor()

# --- Create Transactions Table ---
c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    application_no TEXT,
    product TEXT,
    supplier TEXT,
    amount REAL NOT NULL,
    type TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
