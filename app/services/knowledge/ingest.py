"""Placeholder for knowledge ingestion utilities.

Functions to add:
- load files (markdown, html, txt)
- chunk/split text
- compute embeddings and add to vectorstore
"""

from typing import Iterable


def ingest_documents(docs: Iterable[str]):
    """Stub: accept iterable of strings and return count."""
    count = 0
    for _ in docs:
        count += 1
    return {"ingested": count}
