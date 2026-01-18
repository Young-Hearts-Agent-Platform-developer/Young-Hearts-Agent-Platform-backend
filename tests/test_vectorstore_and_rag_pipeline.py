"""
自动化测试：确保 rag_pipeline.vectorize_knowledge_item 与 BaseVectorStore 可被调用。
"""
import pytest
from app.knowledge.rag_pipeline import vectorize_knowledge_item
from app.knowledge.vectorstore.base import BaseVectorStore

class DummyKnowledgeItem:
    def __init__(self, id, content):
        self.id = id
        self.content = content

class DummyKnowledgeChunk:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# monkeypatch KnowledgeChunk 用于测试
import app.knowledge.rag_pipeline as rag_pipeline
rag_pipeline.KnowledgeChunk = DummyKnowledgeChunk


def test_vectorize_knowledge_item_basic():
    item = DummyKnowledgeItem(id=1, content="第一段\n第二段")
    chunks = vectorize_knowledge_item(item)
    assert isinstance(chunks, list)
    assert len(chunks) == 2
    assert chunks[0].content_chunk == "第一段"
    assert chunks[1].content_chunk == "第二段"


def test_base_vectorstore_interface():
    store = BaseVectorStore()
    with pytest.raises(NotImplementedError):
        store.add_vector([0.1]*10, {"item_id": 1})
    with pytest.raises(NotImplementedError):
        store.search_vector([0.1]*10, top_k=1)
