# NANI ASSOCIATES – Business Tracker (Streamlit)

A simple desktop/web app to record daily transactions and get monthly & service-wise profit/loss.

## Features
- Add, edit, delete transactions
- Auto-calculated profit per entry
- Filters by date and service
- Monthly P&L and service-wise report tables
- Export to Excel (3 sheets)
- Save business info (name, address, proprietor, phone)
- Data stored locally in SQLite (`nani_associates.db`)

## How to run
1. Install Python 3.9+
2. Open terminal in this folder and run:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Your browser will open at `http://localhost:8501`

## Default Services
- PAN Card
- Passport
- Aadhaar Card
- Digital Signature
- Other Online Service

You can modify the list in `app.py` (variable `SERVICES`).
