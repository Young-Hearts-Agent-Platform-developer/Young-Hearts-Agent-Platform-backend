import os
import json
from typing import List, Tuple, Optional
from langchain_core.documents import Document
from langchain_classic.storage import EncoderBackedStore, LocalFileStore
from langchain_classic.retrievers import ParentDocumentRetriever
from app.services.rag.vectorstore.chroma import get_chroma_collection
from app.services.rag.splitters.custom_splitter import CustomSplitter

def get_docstore(store_path: str = "./data/parent_docs"):
    os.makedirs(store_path, exist_ok=True)
    
    def serialize_doc(doc: Document) -> bytes:
        return json.dumps({"page_content": doc.page_content, "metadata": doc.metadata}).encode("utf-8")
        
    def deserialize_doc(data: bytes) -> Document:
        obj = json.loads(data.decode("utf-8"))
        return Document(page_content=obj["page_content"], metadata=obj["metadata"])
        
    fs = LocalFileStore(store_path)
    store = EncoderBackedStore(
        store=fs,
        key_encoder=lambda x: str(x),
        value_serializer=serialize_doc,
        value_deserializer=deserialize_doc
    )
    return store

def get_retriever():
    vectorstore = get_chroma_collection("knowledge_base")
    store = get_docstore()
    
    parent_splitter = CustomSplitter.get_medium_risk_parent_splitter()
    child_splitter = CustomSplitter.get_medium_risk_child_splitter()
    
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    return retriever

def retrieve_context(query: str, similarity_threshold: float = 0.6, top_k: int = 4) -> Optional[str]:
    """
    检索相关文档片段，并组装上下文。
    如果最高相似度低于阈值，返回 None。
    """
    retriever = get_retriever()
    vectorstore = retriever.vectorstore
    
    # 1. 先通过 vectorstore 获取子块及其相似度得分
    # 注意：Chroma 默认返回距离，similarity_search_with_relevance_scores 会将其转换为相似度得分
    try:
        docs_and_scores = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception as e:
        # 如果不支持 relevance_scores，回退到 similarity_search_with_score
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=top_k)
        # 假设距离越小越好，这里简单转换（仅作示例，实际需根据距离度量调整）
        # Chroma 默认 L2 距离，距离越小越相似
        docs_and_scores = [(doc, max(0.0, 1.0 - score / 2.0)) for doc, score in docs_and_scores]
    
    if not docs_and_scores:
        return None
        
    # 2. 检查最高相似度是否达到阈值
    highest_score = docs_and_scores[0][1]
    if highest_score < similarity_threshold:
        return None
        
    # 3. 获取满足阈值的子块
    valid_docs = [doc for doc, score in docs_and_scores if score >= similarity_threshold]
    
    # 4. 获取父文档
    ids = []
    for d in valid_docs:
        doc_id = d.metadata.get(retriever.id_key)
        if doc_id and doc_id not in ids:
            ids.append(doc_id)
            
    retrieved_docs = []
    if ids:
        parent_docs = retriever.docstore.mget(ids)
        retrieved_docs = [d for d in parent_docs if d is not None]
    
    # 如果没有父文档（例如高/低风险文档直接存入 Chroma），则直接使用 valid_docs
    if not retrieved_docs:
        retrieved_docs = valid_docs
    
    # 5. 组装上下文
    context_parts = []
    for i, doc in enumerate(retrieved_docs):
        source = doc.metadata.get("title", "未知来源")
        page = doc.metadata.get("page", "未知位置")
        content = doc.page_content
        context_parts.append(f"【来源{i+1}】: {source} (位置: {page})\n{content}")
        
    return "\n\n".join(context_parts)
