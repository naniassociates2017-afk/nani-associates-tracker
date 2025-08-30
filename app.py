import sqlite3, os, csv, datetime

def backup_and_restore_table(c, table_name, expected_columns, create_sql):
    """Back up old table data, drop table, recreate with correct schema, and restore."""
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if c.fetchone():
        # Compare schema
        c.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [row[1] for row in c.fetchall()]
        if existing_cols != expected_columns:
            # Backup
            c.execute(f"SELECT * FROM {table_name}")
            rows = c.fetchall()
            if rows:
                backup_file = f"{table_name}_backup.csv"
                with open(backup_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(existing_cols)
                    writer.writerows(rows)
                print(f"⚠️ {table_name}: Schema mismatch, old data saved to {backup_file}")

            # Drop old table
            c.execute(f"DROP TABLE {table_name}")

    # Create correct schema
    c.execute(create_sql)

    # Restore if backup exists
    backup_file = f"{table_name}_backup.csv"
    if os.path.exists(backup_file):
        with open(backup_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            restored = 0
            for row in reader:
                # Map available fields safely
                data = [row.get(col, None) for col in expected_columns]
                try:
                    placeholders = ",".join("?" * len(expected_columns))
                    c.execute(f"INSERT INTO {table_name}({','.join(expected_columns)}) VALUES ({placeholders})", data)
                    restored += 1
                except Exception as e:
                    print(f"⚠️ Could not restore row in {table_name}:", row, e)
            if restored > 0:
                print(f"✅ {restored} records restored into {table_name}")


def init_db():
    conn = sqlite3.connect("nani_associates.db")
    c = conn.cursor()

    # Applications
    backup_and_restore_table(
        c,
        "applications",
        ["id","customer_name","service_name","govt_amount","charged_amount",
         "payment_received","payment_pending","profit","agent_name","created_at","note"],
        '''CREATE TABLE IF NOT EXISTS applications(
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
        )'''
    )

    # Expenses
    backup_and_restore_table(
        c,
        "expenses",
        ["id","expense_name","amount","created_at"],
        '''CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY,
            expense_name TEXT,
            amount REAL,
            created_at TEXT
        )'''
    )

    # Suppliers
    backup_and_restore_table(
        c,
        "suppliers",
        ["id","name","contact"],
        '''CREATE TABLE IF NOT EXISTS suppliers(
            id INTEGER PRIMARY KEY,
            name TEXT,
            contact TEXT
        )'''
    )

    # Ledger
    backup_and_restore_table(
        c,
        "ledger",
        ["id","supplier_id","description","debit","credit","created_at"],
        '''CREATE TABLE IF NOT EXISTS ledger(
            id INTEGER PRIMARY KEY,
            supplier_id INTEGER,
            description TEXT,
            debit REAL,
            credit REAL,
            created_at TEXT,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )'''
    )

    # Services
    backup_and_restore_table(
        c,
        "services",
        ["id","main_category","sub_category","product_name","govt_amount"],
        '''CREATE TABLE IF NOT EXISTS services(
            id INTEGER PRIMARY KEY,
            main_category TEXT,
            sub_category TEXT,
            product_name TEXT,
            govt_amount REAL
        )'''
    )

    conn.commit()
    conn.close()
