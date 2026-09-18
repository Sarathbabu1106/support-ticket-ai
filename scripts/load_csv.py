import sqlite3
import pandas as pd

csv_path = "data/support_tickets.csv"
df = pd.read_csv(csv_path)

conn = sqlite3.connect("tickets.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS tickets")

# ✅ Schema aligned with your actual CSV headers
cursor.execute("""
CREATE TABLE tickets (
    ticket_id TEXT PRIMARY KEY,
    created_at TEXT,
    category TEXT,
    priority TEXT,
    status TEXT,
    response_time_hrs REAL,
    resolution_time_hrs REAL,
    agent_id TEXT,
    customer_rating INTEGER,
    issue_summary TEXT
)
""")

# ✅ Insert rows from CSV
df.to_sql("tickets", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print("✅ CSV loaded into tickets.db")
