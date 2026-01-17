"""Placeholder for knowledge ingestion utilities.

Functions to add:
- load files (markdown, html, txt)
- chunk/split text
- compute embeddings and add to vectorstore
"""

from typing import Iterable


def ingest_documents(docs: Iterable[str], vectorstore, embedder):
    chunks = split_texts(docs)  #文本切片
    embeddings = embedder.embed(chunks) #嵌入计算
    vectorstore.add_documents(chunks, embeddings)
    count = 0
    for _ in docs:
        count += 1
    return {"ingested": len(chunks), "documents": count}
