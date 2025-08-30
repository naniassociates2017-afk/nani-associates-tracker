def init_applications(c):
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

def init_expenses(c):
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

def init_suppliers(c):
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

def init_ledger(c):
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

def init_services(c):
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

def init_db():
    conn = sqlite3.connect("nani_associates.db")
    c = conn.cursor()
    init_applications(c)
    init_expenses(c)
    init_suppliers(c)
    init_ledger(c)
    init_services(c)
    conn.commit()
    conn.close()
