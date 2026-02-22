import pytest
from app.services.rag.splitters.custom_splitter import CustomSplitter

def test_high_risk_splitter():
    content = "这是一个高风险文档。" * 100
    metadata = {"title": "诊断标准"}
    chunks = CustomSplitter.split_document(content, "high", metadata)
    
    assert len(chunks) > 0
    assert chunks[0].metadata["risk_level"] == "high"
    assert chunks[0].metadata["title"] == "诊断标准"
    # 验证 chunk_size 限制
    for chunk in chunks:
        assert len(chunk.page_content) <= 1024

def test_medium_risk_splitter():
    content = "这是一个中风险文档。" * 200
    metadata = {"title": "干预指南"}
    # 中风险默认返回父块
    chunks = CustomSplitter.split_document(content, "medium", metadata)
    
    assert len(chunks) > 0
    assert chunks[0].metadata["risk_level"] == "medium"
    for chunk in chunks:
        assert len(chunk.page_content) <= 2048

def test_low_risk_splitter():
    content = "这是一个低风险文档。" * 50
    metadata = {"title": "科普文章"}
    chunks = CustomSplitter.split_document(content, "low", metadata)
    
    assert len(chunks) > 0
    assert chunks[0].metadata["risk_level"] == "low"
    for chunk in chunks:
        assert len(chunk.page_content) <= 512
