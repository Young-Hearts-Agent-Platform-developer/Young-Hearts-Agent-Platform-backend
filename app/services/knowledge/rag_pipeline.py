"""Simple RAG pipeline placeholder.

Combines retrieval results with an LLM client (to be implemented).
"""

from typing import Dict

from app.services.knowledge.retriever import retrieve


def answer_query(query: str, top_k: int = 3) -> Dict:
    docs = retrieve(query, top_k=top_k)
    # fake LLM response for now
    response = {
        "query": query,
        "answer": "这是一个占位回答；真实实现会调用模型并附带来源",
        "sources": docs,
    }
    return response
