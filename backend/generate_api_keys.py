import sqlite3
import uuid
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'rag_database.db'))

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ensure api_keys table exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    allowed_origins TEXT DEFAULT '*',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Get all site_ids
cursor.execute('SELECT site_id FROM sites')
sites = cursor.fetchall()

count = 0
for (site_id,) in sites:
    # Check if this site already has an apiKey
    cursor.execute('SELECT 1 FROM api_keys WHERE site_id = ?', (site_id,))
    if cursor.fetchone():
        continue
    api_key = str(uuid.uuid4())
    cursor.execute('INSERT INTO api_keys (id, site_id, api_key, allowed_origins, is_active) VALUES (?, ?, ?, ?, ?)',
                   (str(uuid.uuid4()), site_id, api_key, '*', 1))
    print(f'Site {site_id} -> apiKey: {api_key}')
    count += 1

conn.commit()
conn.close()
print(f'✅ 共为 {count} 个站点分配了 apiKey') 