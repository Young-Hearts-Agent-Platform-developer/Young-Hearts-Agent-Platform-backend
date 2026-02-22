import pytest
from app.services.rag.vectorstore.chroma import get_chroma_collection
from app.core.config import settings

def test_get_chroma_collection():
    collection_name = "test_collection"
    vectorstore = get_chroma_collection(collection_name)
    
    assert vectorstore is not None
    
    # Test adding and querying a document
    test_text = "这是一个测试文档，用于验证ChromaDB连接和Doubao Embedding模型。"
    vectorstore.add_texts([test_text])
    
    results = vectorstore.similarity_search("测试文档", k=1)
    assert len(results) > 0
    assert "测试文档" in results[0].page_content
    
    # Clean up
    vectorstore.delete_collection()

