import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from rag_context import build_context
from rag_storage_prisma import PrismaRAGStorage


class ChunkRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "chunks.db")
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.executescript(
                """
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL
                );
                CREATE TABLE sites (
                    site_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    site_id TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    content TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (site_id) REFERENCES sites(site_id)
                );
                CREATE TABLE embeddings (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    embedding_vector BLOB NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (site_id) REFERENCES sites(site_id)
                );
                """
            )
            connection.execute(
                "INSERT INTO users (id, username) VALUES ('user-1', 'owner')"
            )
            connection.execute(
                "INSERT INTO sites (site_id, user_id) VALUES ('site-1', 'user-1')"
            )
            connection.commit()
        self.storage = PrismaRAGStorage(database_path=self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_beginning_middle_and_end_chunks_reach_recall_at_three(self):
        document_id = self.storage.add_document_entry(
            "https://example.com/guide",
            "Guide",
            "Legacy full document content",
            "site-1",
        )
        dimensions = 12
        for index in range(dimensions):
            vector = [0.0] * dimensions
            vector[index] = 1.0
            self.storage.add_embedding(
                document_id,
                "site-1",
                vector,
                chunk_text=f"exact chunk {index}",
                chunk_index=index,
                embedding_model="test-model-v1",
            )

        documents, embeddings = self.storage.get_documents_by_site("site-1")
        self.assertEqual(
            [f"exact chunk {index}" for index in range(dimensions)],
            [document["content"] for document in documents],
        )
        self.assertTrue(
            all(document["migration_status"] == "ready" for document in documents)
        )
        self.assertTrue(
            all(document["embedding_model"] == "test-model-v1" for document in documents)
        )

        recalled = 0
        for target_index in (0, dimensions // 2, dimensions - 1):
            query = np.zeros(dimensions)
            query[target_index] = 1.0
            scores = [
                float(np.dot(query, embedding))
                for embedding in embeddings
            ]
            top_three = np.argsort(scores)[-3:]
            recalled += int(target_index in top_three)
        self.assertGreaterEqual(recalled / 3, 0.95)

    def test_context_builder_enforces_token_budget(self):
        context = build_context(["A" * 12, "B" * 12], token_budget=5)
        self.assertEqual(20, len(context.replace("\n\n", "")))
        self.assertEqual("A" * 12 + "\n\n" + "B" * 8, context)


if __name__ == "__main__":
    unittest.main()
