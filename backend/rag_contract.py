"""Grounding, citation, SSE, and evaluation helpers for RAG responses."""

import json
import math
import re
from typing import Any, Dict, Iterable, List

def source_id(document: Dict[str, Any]) -> str:
    chunk_index = document.get("chunk_index")
    suffix = chunk_index if chunk_index is not None else "legacy"
    return f"{document['id']}:{suffix}"


def build_grounded_context(
    ranked_documents: Iterable[Dict[str, Any]], token_budget: int
) -> tuple[str, List[Dict[str, Any]]]:
    sources = []
    snippets = []
    remaining_chars = token_budget * 4
    if remaining_chars < 1:
        raise ValueError("token_budget must be positive")
    for index, document in enumerate(ranked_documents, start=1):
        snippet = (
            f"[{index}] {document.get('title') or 'Untitled'}\n"
            f"{document.get('content') or ''}"
        ).strip()
        if not snippet or remaining_chars <= 0:
            break
        if len(snippet) > remaining_chars:
            snippet = snippet[:remaining_chars]
        sources.append(
            {
                "citation": index,
                "source_id": source_id(document),
                "title": document.get("title"),
                "url": document.get("url"),
                "chunk_index": document.get("chunk_index"),
            }
        )
        snippets.append(snippet)
        remaining_chars -= len(snippet)
    return "\n\n".join(snippets), sources


def citation_metrics(answer: str, sources: List[Dict[str, Any]]) -> Dict[str, float]:
    citations = [int(value) for value in re.findall(r"\[(\d+)\]", answer or "")]
    valid = {source["citation"] for source in sources}
    if citations:
        precision = sum(citation in valid for citation in citations) / len(citations)
    else:
        precision = 1.0 if not valid else 0.0
    factual_sentences = [
        sentence.strip()
        for sentence in re.findall(
            r"[^.!?。！？]+[.!?。！？]?(?:\[\d+\])*", answer or ""
        )
        if sentence.strip() and not sentence.strip().startswith("无法根据")
    ]
    cited_sentences = sum(
        bool(re.search(r"\[\d+\]", sentence)) for sentence in factual_sentences
    )
    coverage = (
        cited_sentences / len(factual_sentences) if factual_sentences else 1.0
    )
    return {"citation_coverage": coverage, "citation_precision": precision}


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


def sse_event(event: str, data: Any) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    lines = payload.splitlines() or [""]
    return f"event: {event}\n" + "".join(f"data: {line}\n" for line in lines) + "\n"
