"""Context selection helpers for bounded RAG prompts."""

from typing import List


def build_context(snippets: List[str], token_budget: int) -> str:
    if token_budget < 1:
        raise ValueError("token_budget must be positive")
    remaining_chars = token_budget * 4
    selected = []
    for snippet in snippets:
        text = (snippet or "").strip()
        if not text or remaining_chars <= 0:
            continue
        if len(text) > remaining_chars:
            text = text[:remaining_chars]
        selected.append(text)
        remaining_chars -= len(text)
    return "\n\n".join(selected)
