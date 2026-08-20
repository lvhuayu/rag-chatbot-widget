import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import jwt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from tenant_auth import (
    TenantAuthError,
    authenticate_site_token,
    issue_api_key_token,
    resolve_site_id,
)


class TenantIngestionAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(self.temp_dir.name, "auth.db")
        self.secret = "test-secret"
        self.algorithm = "HS256"
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
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY,
                    site_id TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    allowed_origins TEXT,
                    is_active INTEGER NOT NULL,
                    FOREIGN KEY (site_id) REFERENCES sites(site_id)
                );
                """
            )
            connection.executemany(
                "INSERT INTO users (id, username) VALUES (?, ?)",
                [("user-1", "tenant-one"), ("user-2", "tenant-two")],
            )
            connection.executemany(
                "INSERT INTO sites (site_id, user_id, created_at) VALUES (?, ?, ?)",
                [
                    ("site-1", "user-1", 1),
                    ("site-2", "user-2", 2),
                ],
            )
            connection.executemany(
                """
                INSERT INTO api_keys (
                    id, site_id, api_key, allowed_origins, is_active
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        "key-1",
                        "site-1",
                        "api-key-one",
                        '["https://tenant-one.example"]',
                        1,
                    ),
                    ("key-2", "site-2", "api-key-two", "*", 1),
                ],
            )
            connection.commit()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anonymous_ingestion_is_rejected(self):
        with self.assertRaises(TenantAuthError) as raised:
            authenticate_site_token(
                self.database_path,
                None,
                None,
                self.secret,
                self.algorithm,
            )
        self.assertEqual(401, raised.exception.status_code)

    def test_api_key_token_enforces_origin_and_active_key(self):
        with self.assertRaises(TenantAuthError) as raised:
            issue_api_key_token(
                self.database_path,
                "api-key-one",
                "https://attacker.example",
                self.secret,
                self.algorithm,
            )
        self.assertEqual(403, raised.exception.status_code)

        token, site_id = issue_api_key_token(
            self.database_path,
            "api-key-one",
            "https://tenant-one.example",
            self.secret,
            self.algorithm,
        )
        self.assertEqual("site-1", site_id)
        identity = authenticate_site_token(
            self.database_path,
            token,
            "https://tenant-one.example",
            self.secret,
            self.algorithm,
        )
        self.assertEqual("site-1", identity.site_id)

        with self.assertRaises(TenantAuthError) as raised:
            authenticate_site_token(
                self.database_path,
                token,
                "https://attacker.example",
                self.secret,
                self.algorithm,
            )
        self.assertEqual(403, raised.exception.status_code)

        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("UPDATE api_keys SET is_active = 0 WHERE id = 'key-1'")
            connection.commit()
        with self.assertRaises(TenantAuthError) as raised:
            authenticate_site_token(
                self.database_path,
                token,
                "https://tenant-one.example",
                self.secret,
                self.algorithm,
            )
        self.assertEqual(401, raised.exception.status_code)

    def test_signed_user_identity_derives_tenant_and_blocks_override(self):
        token = jwt.encode({"id": "user-1"}, self.secret, algorithm=self.algorithm)
        identity = authenticate_site_token(
            self.database_path,
            token,
            None,
            self.secret,
            self.algorithm,
        )
        self.assertEqual("site-1", identity.site_id)
        self.assertEqual("site-1", resolve_site_id(identity, None))
        self.assertEqual("site-1", resolve_site_id(identity, "site-1"))

        with self.assertRaises(TenantAuthError) as raised:
            resolve_site_id(identity, "site-2")
        self.assertEqual(403, raised.exception.status_code)

    def test_signed_site_claim_must_belong_to_user(self):
        token = jwt.encode(
            {"id": "user-1", "siteId": "site-2"},
            self.secret,
            algorithm=self.algorithm,
        )
        with self.assertRaises(TenantAuthError) as raised:
            authenticate_site_token(
                self.database_path,
                token,
                None,
                self.secret,
                self.algorithm,
            )
        self.assertEqual(403, raised.exception.status_code)


if __name__ == "__main__":
    unittest.main()
