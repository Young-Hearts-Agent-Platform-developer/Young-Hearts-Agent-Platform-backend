import os
import tempfile
import shutil
import pytest
from app.knowledge import ingest

class DummyEmbedder(ingest.Embedder):
    def embed(self, texts):
        # 返回与输入等长的假向量
        return [[float(i)] * 3 for i, _ in enumerate(texts)]

class DummyVectorStore:
    def __init__(self):
        self.data = []
    def add_documents(self, chunks, embeddings):
        for c, e in zip(chunks, embeddings):
            self.data.append((c, e))
    def search(self, query_embedding, top_k=5):
        return self.data[:top_k]
    def persist(self):
        pass
    def load(self):
        pass

def test_ingest_documents_with_texts():
    texts = ["第一段。第二段。", "第三段。第四段。"]
    embedder = DummyEmbedder()
    vectorstore = DummyVectorStore()
    result = ingest.ingest_documents(texts, vectorstore, embedder)
    assert result["documents"] == 2
    assert result["ingested"] > 0
    assert len(vectorstore.data) == result["ingested"]

def test_ingest_documents_with_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("A。B。C。\n\nD。E。")
    embedder = DummyEmbedder()
    vectorstore = DummyVectorStore()
    result = ingest.ingest_documents(str(file_path), vectorstore, embedder)
    assert result["documents"] == 1
    assert result["ingested"] > 0
    assert len(vectorstore.data) == result["ingested"]

def test_ingest_documents_with_dir(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("foo。bar。baz。")
    (d / "b.txt").write_text("hello。world。\n\nnew。line。")
    embedder = DummyEmbedder()
    vectorstore = DummyVectorStore()
    result = ingest.ingest_documents(str(d), vectorstore, embedder)
    assert result["documents"] == 2
    assert result["ingested"] > 0
    assert len(vectorstore.data) == result["ingested"]
