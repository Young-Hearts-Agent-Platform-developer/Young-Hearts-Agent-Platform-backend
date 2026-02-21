"""Placeholder retriever module.

Implement different retrieval strategies (dense, sparse, hybrid) here.
"""

from typing import List, Dict


def retrieve(query: str, top_k: int = 5) -> List[Dict]:
    """Return list of fake documents for now."""
    return [{"id": i, "text": f"Fake doc {i}", "score": 1.0} for i in range(top_k)]
