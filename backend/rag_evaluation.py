"""Deterministic quality gates for approved RAG evaluation results."""

from typing import Any, Dict, List, Optional

from rag_contract import citation_metrics


def evaluate_cases(cases: List[Dict[str, Any]]) -> Dict[str, float]:
    if not cases:
        raise ValueError("evaluation set must not be empty")
    citation_coverages = []
    citation_precisions = []
    recalls = []
    unsupported = 0
    unanswerable = 0
    for case in cases:
        metrics = citation_metrics(case["answer"], case["sources"])
        citation_coverages.append(metrics["citation_coverage"])
        citation_precisions.append(metrics["citation_precision"])
        expected_ids = set(case.get("expected_source_ids", []))
        retrieved_ids = set(case.get("retrieved_source_ids", [])[:5])
        recalls.append(
            len(expected_ids & retrieved_ids) / len(expected_ids)
            if expected_ids
            else 1.0
        )
        if not case.get("answerable", True):
            unanswerable += 1
            if not case["answer"].startswith("无法根据现有知识库回答该问题"):
                unsupported += 1
    return {
        "citation_coverage": sum(citation_coverages) / len(cases),
        "citation_precision": sum(citation_precisions) / len(cases),
        "unsupported_answer_rate": unsupported / unanswerable if unanswerable else 0.0,
        "recall_at_5": sum(recalls) / len(cases),
        "faithfulness": sum(citation_precisions) / len(cases),
    }


def enforce_quality_gate(
    metrics: Dict[str, float],
    baseline_recall_at_5: Optional[float] = None,
    baseline_faithfulness: Optional[float] = None,
) -> None:
    failures = []
    if metrics["citation_coverage"] < 0.95:
        failures.append("citation coverage is below 95%")
    if metrics["citation_precision"] < 0.95:
        failures.append("citation precision is below 95%")
    if metrics["unsupported_answer_rate"] > 0.02:
        failures.append("unsupported-answer rate exceeds 2%")
    if (
        baseline_recall_at_5 is not None
        and metrics["recall_at_5"] < baseline_recall_at_5 - 0.02
    ):
        failures.append("Recall@5 regressed by more than 2 percentage points")
    if (
        baseline_faithfulness is not None
        and metrics["faithfulness"] < baseline_faithfulness - 0.02
    ):
        failures.append("faithfulness regressed by more than 2 percentage points")
    if failures:
        raise AssertionError("; ".join(failures))
