import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from rag_storage_prisma import PrismaRAGStorage


class PrismaRAGStorageSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "rag.db")
        connection = sqlite3.connect(self.database_path)
        try:
            connection.executescript(
                """
                PRAGMA foreign_keys=ON;
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    created_at DATETIME NOT NULL
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
                """
                INSERT INTO users (id, username, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("user-1", "owner", "hash", "2026-01-01T00:00:00"),
            )
            connection.execute(
                "INSERT INTO sites (site_id, user_id) VALUES (?, ?)",
                ("site-1", "user-1"),
            )
            connection.commit()
        finally:
            connection.close()
        self.storage = PrismaRAGStorage(database_path=self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_request_values_are_stored_as_data_not_executed(self):
        marker_path = os.path.join(self.temp_dir.name, "injected.txt")
        payload = (
            "'); require('fs').writeFileSync("
            f"'{marker_path.replace(os.sep, '/')}', 'executed'); //"
        )

        document_id = self.storage.add_document_entry(
            payload,
            payload,
            payload,
            "site-1",
            "2026-08-20T12:00:00Z",
        )
        self.storage.add_embedding(
            document_id,
            "site-1",
            [0.1, 0.2, 0.3],
            "2026-08-20T12:00:00Z",
        )

        with closing(sqlite3.connect(self.database_path)) as connection:
            row = connection.execute(
                "SELECT url, title, content, created_at FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()

        self.assertEqual((payload, payload, payload), row[:3])
        self.assertIsInstance(row[3], int)
        documents, embeddings = self.storage.get_documents_by_site("site-1")
        self.assertEqual("2026-08-20T12:00:00Z", documents[0]["created_at"])
        self.assertEqual([0.1, 0.2, 0.3], embeddings[0].tolist())
        self.assertFalse(os.path.exists(marker_path))
        self.assertFalse(
            os.path.exists(
                os.path.join(
                    Path(__file__).resolve().parents[1],
                    "prisma",
                    "temp_prisma_query.js",
                )
            )
        )

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            self.storage.add_document_entry(
                "https://example.com",
                "title",
                "content",
                "site-1",
                "not-a-date",
            )

    def test_concurrent_ingestion_has_no_shared_query_file(self):
        def create_document(index):
            return self.storage.add_document_entry(
                f"https://example.com/{index}",
                f"title-{index}",
                f"content-{index}",
                "site-1",
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            document_ids = list(executor.map(create_document, range(24)))

        self.assertEqual(24, len(set(document_ids)))
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        self.assertEqual(24, count)


if __name__ == "__main__":
    unittest.main()
