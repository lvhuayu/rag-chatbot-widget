#!/usr/bin/env python3
"""
历史数据迁移脚本：将 rag_database.db 里的所有文档自动分段、用新 embedding 重新批量入库到新系统（/add-documents）。
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.rag_storage_prisma import PrismaRAGStorage
from backend.rag_server_prisma import split_text, generate_simple_embedding
import sqlite3

# 旧数据库路径
OLD_DB_PATH = os.path.join(os.path.dirname(__file__), 'rag_database.db')

# 目标存储（Prisma）
storage = PrismaRAGStorage()

# 读取旧数据库（假设为 SQLite）
conn = sqlite3.connect(OLD_DB_PATH)
cursor = conn.cursor()

# 读取所有文档
cursor.execute('SELECT url, title, content, timestamp, user_id FROM documents')
documents = cursor.fetchall()

print(f"读取到 {len(documents)} 条历史文档，开始迁移...")

for idx, (url, title, content, timestamp, user_id) in enumerate(documents):
    user_id = user_id or 'default_user'
    segments = split_text(content, max_length=300)
    print(f"[{idx+1}/{len(documents)}] {title} 分段数: {len(segments)}")
    for seg_idx, chunk in enumerate(segments):
        embedding = generate_simple_embedding(chunk)
        result = storage.add_document_with_uniqueness(
            doc_id=None,
            url=url,
            title=title,
            content=chunk,
            user_id=user_id,
            embedding=embedding,
            timestamp=timestamp
        )
        print(f"  - 段{seg_idx+1}/{len(segments)} 入库: {result.get('action')} (doc_id={result.get('doc_id')})")

print("历史数据迁移完成！")