import sqlite3
import uuid

DB_PATH = 'rag_database.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 获取所有用户id（表名改为users）
cursor.execute('SELECT id FROM users')
users = cursor.fetchall()

count = 0
for (user_id,) in users:
    # 检查该用户是否已有siteId
    cursor.execute('SELECT siteId FROM Site WHERE userId = ?', (user_id,))
    if cursor.fetchone():
        continue  # 已有siteId，跳过
    site_id = str(uuid.uuid4())
    cursor.execute('INSERT INTO Site (siteId, userId) VALUES (?, ?)', (site_id, user_id))
    print(f'User {user_id} -> Site {site_id}')
    count += 1

conn.commit()
conn.close()
print(f'共为 {count} 个用户生成了siteId') 