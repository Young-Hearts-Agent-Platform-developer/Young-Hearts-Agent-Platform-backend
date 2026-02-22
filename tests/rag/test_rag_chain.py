import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from app.services.rag.chains.rag_chain import retrieve_context

@patch("app.services.rag.chains.rag_chain.get_retriever")
def test_retrieve_context_below_threshold(mock_get_retriever):
    # 模拟 retriever 和 vectorstore
    mock_retriever = MagicMock()
    mock_vectorstore = MagicMock()
    mock_retriever.vectorstore = mock_vectorstore
    mock_get_retriever.return_value = mock_retriever
    
    # 模拟 similarity_search_with_relevance_scores 返回低于阈值的结果
    mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
        (Document(page_content="test"), 0.5)
    ]
    
    context = retrieve_context("test query", similarity_threshold=0.6)
    assert context is None

@patch("app.services.rag.chains.rag_chain.get_retriever")
def test_retrieve_context_above_threshold(mock_get_retriever):
    # 模拟 retriever 和 vectorstore
    mock_retriever = MagicMock()
    mock_vectorstore = MagicMock()
    mock_retriever.vectorstore = mock_vectorstore
    mock_get_retriever.return_value = mock_retriever
    
    # 模拟 similarity_search_with_relevance_scores 返回高于阈值的结果
    mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
        (Document(page_content="child chunk", metadata={"doc_id": "1"}), 0.8)
    ]
    
    # 模拟 docstore 返回父文档
    mock_retriever.id_key = "doc_id"
    mock_docstore = MagicMock()
    mock_retriever.docstore = mock_docstore
    mock_docstore.mget.return_value = [
        Document(page_content="parent chunk", metadata={"title": "Test Doc", "page": "1"})
    ]
    
    context = retrieve_context("test query", similarity_threshold=0.6)
    assert context is not None
    assert "【来源1】: Test Doc (位置: 1)" in context
    assert "parent chunk" in context

@patch("app.services.rag.chains.rag_chain.get_retriever")
def test_retrieve_context_fallback_to_similarity_search_with_score(mock_get_retriever):
    # 模拟 retriever 和 vectorstore
    mock_retriever = MagicMock()
    mock_vectorstore = MagicMock()
    mock_retriever.vectorstore = mock_vectorstore
    mock_get_retriever.return_value = mock_retriever
    
    # 模拟 similarity_search_with_relevance_scores 抛出异常
    mock_vectorstore.similarity_search_with_relevance_scores.side_effect = NotImplementedError("Not supported")
    
    # 模拟 similarity_search_with_score 返回距离 (距离越小越好，假设 0.2 转换为 0.9)
    mock_vectorstore.similarity_search_with_score.return_value = [
        (Document(page_content="child chunk", metadata={"doc_id": "1"}), 0.2)
    ]
    
    # 模拟 docstore 返回父文档
    mock_retriever.id_key = "doc_id"
    mock_docstore = MagicMock()
    mock_retriever.docstore = mock_docstore
    mock_docstore.mget.return_value = [
        Document(page_content="parent chunk", metadata={"title": "Test Doc", "page": "1"})
    ]
    
    context = retrieve_context("test query", similarity_threshold=0.6)
    assert context is not None
    assert "【来源1】: Test Doc (位置: 1)" in context
    assert "parent chunk" in context
