#!/usr/bin/env python3
"""Parameterized SQLite storage for the Prisma-managed RAG database."""

import logging
import os
import pickle
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrismaRAGStorage:
    """Storage adapter for the SQLite database managed by Prisma."""

    def __init__(
        self,
        prisma_schema_path: str = "../prisma/schema.prisma",
        database_path: Optional[str] = None,
    ):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.prisma_schema_path = os.path.abspath(
            os.path.join(backend_dir, prisma_schema_path)
        )
        self.database_path = database_path or self._resolve_database_path()
        database_dir = os.path.dirname(os.path.abspath(self.database_path))
        os.makedirs(database_dir, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            self._ensure_chunk_columns(connection)
            self._ensure_telemetry_columns(connection)
        logger.info("RAG storage initialized with database: %s", self.database_path)

    @staticmethod
    def _ensure_chunk_columns(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(embeddings)").fetchall()
        }
        additions = {
            "chunk_text": "TEXT",
            "chunk_index": "INTEGER",
            "embedding_model": "TEXT",
            "migration_status": "TEXT NOT NULL DEFAULT 'pending'",
        }
        for column, definition in additions.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE embeddings ADD COLUMN {column} {definition}"
                )

    @staticmethod
    def _ensure_telemetry_columns(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(chat_logs)").fetchall()
        }
        if not columns:
            return
        additions = {
            "input_tokens": "INTEGER",
            "output_tokens": "INTEGER",
            "retrieval_latency_ms": "INTEGER",
            "llm_latency_ms": "INTEGER",
            "tenant_tier": "TEXT",
        }
        for column, definition in additions.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE chat_logs ADD COLUMN {column} {definition}"
                )

    def _resolve_database_path(self) -> str:
        prisma_dir = os.path.dirname(self.prisma_schema_path)
        env_path = os.path.join(prisma_dir, ".env")
        try:
            with open(env_path, "r", encoding="utf-8") as env_file:
                match = re.search(
                    r'DATABASE_URL\s*=\s*["\']file:([^"\']+)["\']',
                    env_file.read(),
                )
            if match:
                return os.path.abspath(os.path.join(prisma_dir, match.group(1)))
        except OSError as error:
            logger.warning("Could not read Prisma environment file: %s", error)
        return os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_database.db")
        )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _timestamp(value: Optional[str]) -> int:
        if value is None:
            parsed = datetime.now(timezone.utc)
        else:
            if not isinstance(value, str):
                raise ValueError("timestamp must be an ISO-8601 string")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError("timestamp must be an ISO-8601 string") from error
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp() * 1000)

    @staticmethod
    def _datetime_value(value: Any) -> Any:
        if isinstance(value, (int, float)):
            return (
                datetime.fromtimestamp(value / 1000, timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        return value

    @staticmethod
    def _limit(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("limit must be a positive integer")
        return value

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "url": row["url"],
            "title": row["title"],
            "content": row["content"],
            "created_at": PrismaRAGStorage._datetime_value(row["created_at"]),
            "site_id": row["site_id"],
        }

    def _get_documents(
        self, where_clause: str = "", params: Tuple[Any, ...] = ()
    ) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        query = """
            SELECT
                d.id,
                d.url,
                d.title,
                d.content AS document_content,
                d.created_at,
                d.site_id,
                e.embedding_vector,
                e.chunk_text,
                e.chunk_index,
                e.embedding_model,
                e.migration_status
            FROM documents AS d
            JOIN sites AS s ON s.site_id = d.site_id
            JOIN users AS u ON u.id = s.user_id
            LEFT JOIN embeddings AS e ON e.document_id = d.id
        """
        if where_clause:
            query += f" WHERE {where_clause}"
        query += """
            ORDER BY
                d.created_at DESC,
                CASE WHEN e.chunk_index IS NULL THEN 1 ELSE 0 END,
                e.chunk_index ASC,
                e.created_at ASC
        """
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        documents = []
        embeddings = []
        for row in rows:
            documents.append(
                {
                    "id": row["id"],
                    "url": row["url"],
                    "title": row["title"],
                    "content": row["chunk_text"] or row["document_content"],
                    "created_at": self._datetime_value(row["created_at"]),
                    "site_id": row["site_id"],
                    "chunk_index": row["chunk_index"],
                    "embedding_model": row["embedding_model"],
                    "migration_status": row["migration_status"] or "pending",
                }
            )
            if row["embedding_vector"] is None:
                embeddings.append(np.array([]))
                continue
            try:
                embeddings.append(pickle.loads(bytes(row["embedding_vector"])))
            except Exception as error:
                logger.warning(
                    "Error loading embedding for document %s chunk %s: %s",
                    row["id"],
                    row["chunk_index"],
                    error,
                )
                embeddings.append(np.array([]))
        return documents, embeddings

    def add_document_entry(
        self,
        url: str,
        title: str,
        content: str,
        site_id: str,
        timestamp: Optional[str] = None,
    ) -> str:
        doc_id = str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (id, site_id, url, title, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, site_id, url, title, content, self._timestamp(timestamp)),
            )
        logger.info(
            "Created document entry: %s (Site: %s, ID: %s)",
            title,
            site_id,
            doc_id,
        )
        return doc_id

    def add_embedding(
        self,
        document_id: str,
        site_id: str,
        embedding: List[float],
        timestamp: Optional[str] = None,
        chunk_text: Optional[str] = None,
        chunk_index: Optional[int] = None,
        embedding_model: Optional[str] = None,
    ) -> str:
        embedding_id = str(uuid.uuid4())
        embedding_blob = pickle.dumps(np.array(embedding))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO embeddings (
                    id, document_id, site_id, embedding_vector, dimension,
                    chunk_text, chunk_index, embedding_model, migration_status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    embedding_id,
                    document_id,
                    site_id,
                    sqlite3.Binary(embedding_blob),
                    len(embedding),
                    chunk_text,
                    chunk_index,
                    embedding_model,
                    "ready" if chunk_text is not None else "pending",
                    self._timestamp(timestamp),
                ),
            )
        logger.info("Added embedding for document: %s", document_id)
        return embedding_id

    def add_document_with_uniqueness(
        self,
        doc_id: Optional[str],
        url: str,
        title: str,
        content: str,
        site_id: str,
        embedding: List[float],
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.warning(
            "add_document_with_uniqueness is deprecated. "
            "Use add_document_entry and add_embedding instead."
        )
        return {
            "success": False,
            "action": "deprecated",
            "doc_id": None,
            "error": "Deprecated method",
        }

    def get_documents_by_user(
        self, user_id: str
    ) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        try:
            result = self._get_documents("u.username = ?", (user_id,))
            logger.info("Retrieved %s documents for user: %s", len(result[0]), user_id)
            return result
        except Exception as error:
            logger.error("Error getting documents for user %s: %s", user_id, error)
            return [], []

    def get_documents_by_site(
        self, site_id: str
    ) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        try:
            result = self._get_documents("d.site_id = ?", (site_id,))
            logger.info("Retrieved %s documents for site: %s", len(result[0]), site_id)
            return result
        except Exception as error:
            logger.error("Error getting documents for site %s: %s", site_id, error)
            return [], []

    def get_all_documents(
        self,
    ) -> Tuple[List[Dict[str, Any]], List[np.ndarray]]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT d.id, d.url, d.title, d.content, d.created_at, d.site_id
                    FROM documents AS d
                    ORDER BY d.created_at DESC
                    """
                ).fetchall()
            documents = [self._document_from_row(row) for row in rows]
            logger.info("Retrieved %s total documents", len(documents))
            return documents, [np.array([]) for _ in documents]
        except Exception as error:
            logger.error("Error getting all documents: %s", error)
            return [], []

    def get_user_documents_list(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        try:
            query = """
                SELECT d.id, d.url, d.title, d.content, d.created_at, d.site_id
                FROM documents AS d
                JOIN sites AS s ON s.site_id = d.site_id
                JOIN users AS u ON u.id = s.user_id
            """
            params: List[Any] = []
            if user_id:
                query += " WHERE u.username = ?"
                params.append(user_id)
            query += " ORDER BY d.created_at DESC LIMIT ?"
            params.append(self._limit(limit))
            with self._connect() as connection:
                rows = connection.execute(query, tuple(params)).fetchall()
            return [self._document_from_row(row) for row in rows]
        except Exception as error:
            logger.error("Error getting documents list: %s", error)
            return []

    def get_user_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            with self._connect() as connection:
                total_documents = connection.execute(
                    "SELECT COUNT(*) FROM documents"
                ).fetchone()[0]
                if user_id:
                    user_documents = connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM documents AS d
                        JOIN sites AS s ON s.site_id = d.site_id
                        JOIN users AS u ON u.id = s.user_id
                        WHERE u.username = ?
                        """,
                        (user_id,),
                    ).fetchone()[0]
                    return {
                        "user_id": user_id,
                        "document_count": user_documents,
                        "total_documents": total_documents,
                    }
                total_users = connection.execute(
                    "SELECT COUNT(*) FROM users"
                ).fetchone()[0]
            return {
                "user_id": "all_users",
                "document_count": total_documents,
                "total_documents": total_documents,
                "unique_users": total_users,
            }
        except Exception as error:
            logger.error("Error getting stats: %s", error)
            return {"error": str(error)}

    def get_database_info(self) -> Dict[str, Any]:
        try:
            with self._connect() as connection:
                total_documents = connection.execute(
                    "SELECT COUNT(*) FROM documents"
                ).fetchone()[0]
                total_embeddings = connection.execute(
                    "SELECT COUNT(*) FROM embeddings"
                ).fetchone()[0]
                total_users = connection.execute(
                    "SELECT COUNT(*) FROM users"
                ).fetchone()[0]
                dimension_row = connection.execute(
                    "SELECT dimension FROM embeddings LIMIT 1"
                ).fetchone()
                pending_chunks = connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM embeddings
                    WHERE migration_status != 'ready' OR chunk_text IS NULL
                    """
                ).fetchone()[0]
            database_size_mb = 0
            if os.path.exists(self.database_path):
                database_size_mb = round(
                    os.path.getsize(self.database_path) / (1024 * 1024), 2
                )
            return {
                "database_path": self.database_path,
                "database_size_mb": database_size_mb,
                "total_documents": total_documents,
                "unique_users": total_users,
                "embedding_dimension": (
                    dimension_row["dimension"] if dimension_row else "N/A"
                ),
                "type": "Prisma SQLite",
                "documents": total_documents,
                "embeddings": total_embeddings,
                "users": total_users,
                "chunks_pending_migration": pending_chunks,
                "schema": "Unified (User Management + RAG)",
            }
        except Exception as error:
            logger.error("Error getting database info: %s", error)
            return {"error": str(error)}

    def clear_documents_by_user(self, user_id: str) -> bool:
        try:
            with self._connect() as connection:
                site_rows = connection.execute(
                    """
                    SELECT s.site_id
                    FROM sites AS s
                    JOIN users AS u ON u.id = s.user_id
                    WHERE u.username = ?
                    """,
                    (user_id,),
                ).fetchall()
                if not site_rows:
                    logger.warning("User %s not found", user_id)
                    return False
                site_ids = [row["site_id"] for row in site_rows]
                placeholders = ",".join("?" for _ in site_ids)
                connection.execute(
                    f"DELETE FROM embeddings WHERE site_id IN ({placeholders})",
                    site_ids,
                )
                connection.execute(
                    f"DELETE FROM documents WHERE site_id IN ({placeholders})",
                    site_ids,
                )
            logger.info("Cleared all documents and embeddings for user: %s", user_id)
            return True
        except Exception as error:
            logger.error("Error clearing documents for user %s: %s", user_id, error)
            return False

    def clear_all_documents(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("DELETE FROM embeddings")
                connection.execute("DELETE FROM documents")
            logger.info("Cleared all documents and embeddings")
            return True
        except Exception as error:
            logger.error("Error clearing all documents: %s", error)
            return False

    def get_all_users(self) -> List[Dict[str, Any]]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, username, email, created_at
                    FROM users
                    ORDER BY created_at DESC
                    """
                ).fetchall()
            return [
                {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "registered": self._datetime_value(row["created_at"]),
                    "status": "active",
                }
                for row in rows
            ]
        except Exception as error:
            logger.error("Error getting all users: %s", error)
            return []

    def update_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        try:
            updates = []
            values = []
            for field in ("username", "email"):
                if field in data:
                    updates.append(f"{field} = ?")
                    values.append(data[field])
            if not updates:
                return False
            values.append(user_id)
            with self._connect() as connection:
                cursor = connection.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                    values,
                )
            return cursor.rowcount > 0
        except Exception as error:
            logger.error("Error updating user %s: %s", user_id, error)
            return False

    def delete_user(self, user_id: str) -> bool:
        try:
            with self._connect() as connection:
                site_rows = connection.execute(
                    "SELECT site_id FROM sites WHERE user_id = ?", (user_id,)
                ).fetchall()
                site_ids = [row["site_id"] for row in site_rows]
                if site_ids:
                    placeholders = ",".join("?" for _ in site_ids)
                    for table in (
                        "embeddings",
                        "documents",
                        "chat_logs",
                        "api_keys",
                        "site_subscriptions",
                    ):
                        connection.execute(
                            f"DELETE FROM {table} WHERE site_id IN ({placeholders})",
                            site_ids,
                        )
                    connection.execute(
                        f"DELETE FROM sites WHERE site_id IN ({placeholders})",
                        site_ids,
                    )
                cursor = connection.execute(
                    "DELETE FROM users WHERE id = ?", (user_id,)
                )
            if cursor.rowcount == 0:
                return False
            logger.info("Deleted user %s", user_id)
            return True
        except Exception as error:
            logger.error("Error deleting user %s: %s", user_id, error)
            return False

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT timestamp, site_id, model_used, question, answer
                    FROM chat_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (self._limit(limit),),
                ).fetchall()
            return [
                {
                    "time": self._datetime_value(row["timestamp"]),
                    "user": row["site_id"],
                    "action": row["model_used"] or "chat",
                    "detail": f"Q: {row['question']}\nA: {row['answer']}",
                }
                for row in rows
            ]
        except Exception as error:
            logger.error("Error getting logs: %s", error)
            return []

    def record_rag_telemetry(
        self,
        site_id: str,
        model: str,
        tenant_tier: str,
        input_tokens: int,
        output_tokens: int,
        retrieval_latency_ms: int,
        llm_latency_ms: int,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_logs (
                    id, site_id, question, answer, model_used, token_usage,
                    input_tokens, output_tokens, retrieval_latency_ms,
                    llm_latency_ms, tenant_tier, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    site_id,
                    "[redacted]",
                    "[redacted]",
                    model,
                    input_tokens + output_tokens,
                    input_tokens,
                    output_tokens,
                    retrieval_latency_ms,
                    llm_latency_ms,
                    tenant_tier,
                    self._timestamp(None),
                ),
            )

    def get_rag_metrics(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    model_used,
                    COALESCE(tenant_tier, 'unknown') AS tenant_tier,
                    input_tokens,
                    output_tokens,
                    retrieval_latency_ms,
                    llm_latency_ms
                FROM chat_logs
                WHERE retrieval_latency_ms IS NOT NULL
                  AND llm_latency_ms IS NOT NULL
                """
            ).fetchall()
        groups: Dict[Tuple[str, str], List[sqlite3.Row]] = {}
        for row in rows:
            key = (row["model_used"] or "unknown", row["tenant_tier"])
            groups.setdefault(key, []).append(row)

        def percentile(values: List[int], percentile_value: float) -> int:
            ordered = sorted(values)
            index = max(0, min(len(ordered) - 1, int(np.ceil(len(ordered) * percentile_value)) - 1))
            return ordered[index]

        metrics = []
        for (model, tenant_tier), group_rows in sorted(groups.items()):
            metrics.append(
                {
                    "model": model,
                    "tenant_tier": tenant_tier,
                    "request_count": len(group_rows),
                    "p95_retrieval_latency_ms": percentile(
                        [row["retrieval_latency_ms"] for row in group_rows], 0.95
                    ),
                    "p95_llm_latency_ms": percentile(
                        [row["llm_latency_ms"] for row in group_rows], 0.95
                    ),
                    "input_tokens": sum(
                        row["input_tokens"] or 0 for row in group_rows
                    ),
                    "output_tokens": sum(
                        row["output_tokens"] or 0 for row in group_rows
                    ),
                }
            )
        return metrics


def get_prisma_storage() -> PrismaRAGStorage:
    """Get a storage instance."""
    return PrismaRAGStorage()


def init_prisma_storage() -> PrismaRAGStorage:
    """Initialize a storage instance."""
    return PrismaRAGStorage()
