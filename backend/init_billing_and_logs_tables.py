import sqlite3

DB_PATH = 'backend/rag_database.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS chat_logs (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    session_id TEXT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    model_used TEXT,
    token_usage INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

CREATE TABLE IF NOT EXISTS billing_plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    monthly_price INTEGER NOT NULL,
    daily_limit INTEGER,
    features TEXT
);

CREATE TABLE IF NOT EXISTS site_subscriptions (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expire_date DATETIME,
    FOREIGN KEY (site_id) REFERENCES sites(site_id),
    FOREIGN KEY (plan_id) REFERENCES billing_plans(id)
);
""")

conn.commit()
conn.close()
print('✅ chat_logs、billing_plans、site_subscriptions 三张表已创建') 