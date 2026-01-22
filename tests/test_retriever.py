import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
from app.knowledge import retriever
from langchain_core.documents import Document

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_chroma():
    """Mock langchain_chroma.Chroma"""
    with patch("app.knowledge.retriever.Chroma") as mock:
        yield mock

@pytest.fixture
def mock_embeddings():
    """Mock langchain_openai.OpenAIEmbeddings"""
    with patch("app.knowledge.retriever.OpenAIEmbeddings") as mock:
        yield mock

@pytest.fixture
def setup_config():
    """临时修改全局 config 对象，确保测试时由 Key"""
    original_api_key = retriever.config.EMBEDDING_API_KEY
    original_model = retriever.config.EMBEDDING_MODEL
    original_path = retriever.config.CHROMA_PATH
    original_threshold = retriever.config.SCORE_THRESHOLD

    # 设置测试用的虚假配置
    retriever.config.EMBEDDING_API_KEY = "sk-test-key"
    retriever.config.EMBEDDING_MODEL = "test-embedding-model"
    retriever.config.CHROMA_PATH = "./test_db"
    retriever.config.SCORE_THRESHOLD = 0.6

    yield

    # 还原
    retriever.config.EMBEDDING_API_KEY = original_api_key
    retriever.config.EMBEDDING_MODEL = original_model
    retriever.config.CHROMA_PATH = original_path
    retriever.config.SCORE_THRESHOLD = original_threshold


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_init_without_api_key(mock_chroma, mock_embeddings):
    """测试如果没有 API Key，初始化应该报错"""
    # 覆盖 config.EMBEDDING_API_KEY 为 None
    with patch.object(retriever.config, "EMBEDDING_API_KEY", None):
        with pytest.raises(ValueError, match="未配置 API Key"):
            retriever.KnowledgeRetriever()

def test_init_success(mock_chroma, mock_embeddings, setup_config):
    """测试正常初始化"""
    kr = retriever.KnowledgeRetriever()
    assert kr.embedding_model is not None
    assert kr.vectorstore is not None
    
    # 验证是否调用了 Chroma 和 OpenAIEmbeddings
    mock_embeddings.assert_called_once()
    mock_chroma.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_empty_query(mock_chroma, mock_embeddings, setup_config):
    """测试空查询"""
    kr = retriever.KnowledgeRetriever()
    docs, status = await kr.retrieve("   ")
    assert docs == []
    assert status == "empty_query"


@pytest.mark.asyncio
async def test_retrieve_db_error(mock_chroma, mock_embeddings, setup_config):
    """测试数据库抛出异常"""
    kr = retriever.KnowledgeRetriever()
    
    # 模拟 vectorstore 抛错
    kr.vectorstore.similarity_search_with_relevance_scores.side_effect = Exception("DB Connection Fail")
    
    docs, status = await kr.retrieve("test")
    assert docs == []
    assert status == "db_error"


@pytest.mark.asyncio
async def test_retrieve_success_filter_score(mock_chroma, mock_embeddings, setup_config):
    """测试检索成功，并根据分数过滤"""
    kr = retriever.KnowledgeRetriever()
    
    # 构造两个结果，一个高分(>0.6)，一个低分(<0.6)
    doc_high = Document(page_content="High score content", metadata={"source": "A"})
    doc_low = Document(page_content="Low score content", metadata={"source": "B"})
    
    # 返回 (doc, score)
    # config.SCORE_THRESHOLD 默认我们在 setup_config 设为了 0.6
    mock_results = [
        (doc_high, 0.85),
        (doc_low, 0.4)
    ]
    kr.vectorstore.similarity_search_with_relevance_scores.return_value = mock_results
    
    docs, status = await kr.retrieve("some query")
    
    assert status == "success"
    assert len(docs) == 1
    assert docs[0].page_content == "High score content"
    assert docs[0].metadata["relevance_score"] == 0.85


@pytest.mark.asyncio
async def test_retrieve_no_relevant_info(mock_chroma, mock_embeddings, setup_config):
    """测试所有结果都低于阈值"""
    kr = retriever.KnowledgeRetriever()
    
    doc_low = Document(page_content="Low content", metadata={})
    # 全都低于 0.6
    mock_results = [(doc_low, 0.5)]
    kr.vectorstore.similarity_search_with_relevance_scores.return_value = mock_results
    
    docs, status = await kr.retrieve("some query")
    
    assert docs == []
    assert status == "no_relevant_info_found"


@pytest.mark.asyncio
async def test_search_documents_wrapper(mock_chroma, mock_embeddings, setup_config):
    """测试 search_documents 包装函数"""
    
    # 清除 lru_cache 保证 get_retriever 重新创建实例并使用我们的 mocks
    retriever.get_retriever.cache_clear()
    
    # Mock retrieve 方法的行为，避免深入到 vectorstore
    with patch("app.knowledge.retriever.KnowledgeRetriever.retrieve", new_callable=AsyncMock) as mock_retrieve:
        # Case 1: 成功
        doc = Document(page_content="Content", metadata={"source_id": "src1", "relevance_score": 0.9})
        mock_retrieve.return_value = ([doc], "success")
        
        resp = await retriever.search_documents("query")
        assert resp["status"] == "success"
        assert len(resp["documents"]) == 1
        assert resp["documents"][0]["score"] == 0.9

        # Case 2: Fallback
        mock_retrieve.return_value = ([], "no_relevant_info_found")
        resp = await retriever.search_documents("query")
        assert resp["status"] == "fallback"
        assert "转人工" in resp["message"]

        # Case 3: Error
        mock_retrieve.return_value = ([], "db_error")
        resp = await retriever.search_documents("query")
        assert resp["status"] == "error"
