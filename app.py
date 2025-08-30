def init_db():
    conn = sqlite3.connect("nani_associates.db")
    c = conn.cursor()

    # Correct schema for applications table
    expected_columns = [
        "id", "customer_name", "service_name", "govt_amount", "charged_amount",
        "payment_received", "payment_pending", "profit", "agent_name",
        "created_at", "note"
    ]

    # Check if applications table exists and matches schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
    if c.fetchone():
        c.execute("PRAGMA table_info(applications)")
        existing_cols = [row[1] for row in c.fetchall()]
        if existing_cols != expected_columns:
            # Schema mismatch → drop and recreate
            c.execute("DROP TABLE applications")

    # Create fresh applications table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY,
        customer_name TEXT,
        service_name TEXT,
        govt_amount REAL,
        charged_amount REAL,
        payment_received REAL,
        payment_pending REAL,
        profit REAL,
        agent_name TEXT,
        created_at TEXT,
        note TEXT
    )''')

    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY,
        expense_name TEXT,
        amount REAL,
        created_at TEXT
    )''')

    # Cashbook table
    c.execute('''CREATE TABLE IF NOT EXISTS cashbook(
        id INTEGER PRIMARY KEY,
        type TEXT,
        amount REAL,
        created_at TEXT
    )''')

    # Suppliers table
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY,
        name TEXT,
        contact TEXT
    )''')

    # Ledger table
    c.execute('''CREATE TABLE IF NOT EXISTS ledger(
        id INTEGER PRIMARY KEY,
        supplier_id INTEGER,
        description TEXT,
        debit REAL,
        credit REAL,
        created_at TEXT,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    )''')

    conn.commit()
    conn.close()
