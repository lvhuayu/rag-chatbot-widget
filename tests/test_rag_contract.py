import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from rag_contract import build_grounded_context, citation_metrics, sse_event
from rag_evaluation import enforce_quality_gate, evaluate_cases
from rag_storage_prisma import PrismaRAGStorage


class RAGContractTests(unittest.TestCase):
    def test_approved_golden_set_meets_release_thresholds(self):
        fixture_path = Path(__file__).with_name("rag_golden_set.json")
        cases = json.loads(fixture_path.read_text(encoding="utf-8"))
        metrics = evaluate_cases(cases)
        enforce_quality_gate(
            metrics,
            baseline_recall_at_5=1.0,
            baseline_faithfulness=1.0,
        )
        self.assertEqual(1.0, metrics["citation_coverage"])
        self.assertEqual(0.0, metrics["unsupported_answer_rate"])

    def test_grounded_context_and_sse_contract(self):
        context, sources = build_grounded_context(
            [
                {
                    "id": "doc-1",
                    "title": "Guide",
                    "url": "https://example.com",
                    "content": "Grounded fact.",
                    "chunk_index": 2,
                }
            ],
            token_budget=100,
        )
        self.assertIn("[1]", context)
        self.assertEqual("doc-1:2", sources[0]["source_id"])
        self.assertEqual(
            {"citation_coverage": 1.0, "citation_precision": 1.0},
            citation_metrics("Grounded fact.[1]", sources),
        )
        self.assertTrue(sse_event("sources", {"sources": sources}).startswith("event: sources\n"))

    def test_metrics_report_p95_by_model_and_tenant_tier(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "metrics.db")
            with closing(sqlite3.connect(database_path)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE embeddings (
                        id TEXT PRIMARY KEY,
                        document_id TEXT,
                        site_id TEXT,
                        embedding_vector BLOB,
                        dimension INTEGER,
                        created_at DATETIME
                    );
                    CREATE TABLE chat_logs (
                        id TEXT PRIMARY KEY,
                        site_id TEXT,
                        session_id TEXT,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        model_used TEXT,
                        token_usage INTEGER,
                        timestamp DATETIME NOT NULL
                    );
                    """
                )
                connection.commit()
            storage = PrismaRAGStorage(database_path=database_path)
            for latency in range(1, 21):
                storage.record_rag_telemetry(
                    site_id="site-1",
                    model="gpt-test",
                    tenant_tier="pro",
                    input_tokens=10,
                    output_tokens=5,
                    retrieval_latency_ms=latency,
                    llm_latency_ms=latency * 10,
                )
            metrics = storage.get_rag_metrics()
            self.assertEqual(1, len(metrics))
            self.assertEqual(19, metrics[0]["p95_retrieval_latency_ms"])
            self.assertEqual(190, metrics[0]["p95_llm_latency_ms"])
            self.assertEqual(200, metrics[0]["input_tokens"])
            self.assertEqual(100, metrics[0]["output_tokens"])


if __name__ == "__main__":
    unittest.main()
