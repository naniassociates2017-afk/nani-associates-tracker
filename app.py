ALTER TABLE applications RENAME TO applications_old;

CREATE TABLE applications(
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
);

INSERT INTO applications (customer_name, service_name, govt_amount, charged_amount, payment_received, payment_pending, profit, agent_name, created_at, note)
SELECT customer_name, service_name, govt_amount, charged_amount, payment_received, payment_pending, profit, agent_name, created_at, note
FROM applications_old;
