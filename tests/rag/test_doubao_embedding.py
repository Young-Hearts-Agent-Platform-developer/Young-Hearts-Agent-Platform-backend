import pytest
from app.services.rag.embeddings.doubao import DoubaoEmbeddings
from app.core.config import settings
import requests

def test_doubao_embeddings_init_with_settings():
    emb = DoubaoEmbeddings()
    assert emb.api_key == settings.DOUBAO_EMBEDDING_API_KEY
    assert emb.base_url == settings.DOUBAO_EMBEDDING_BASE_URL
    assert emb.model == settings.DOUBAO_EMBEDDING_MODEL

def test_embed_documents_success():
    emb = DoubaoEmbeddings()
    result = emb.embed_documents(["测试文本1", "测试文本2"])
    # print("Embedding result:", result)
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], list)
    assert len(result[0]) > 0
    assert isinstance(result[0][0], float)

def test_embed_query_success():
    emb = DoubaoEmbeddings()
    result = emb.embed_query("测试文本")
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert isinstance(result[0], float)

