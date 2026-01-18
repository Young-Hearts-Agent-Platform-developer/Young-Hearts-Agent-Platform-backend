"""Simple RAG pipeline placeholder.

Combines retrieval results with an LLM client (to be implemented).
"""


from typing import List, Dict
from app.models.knowledge import KnowledgeItem  # 假定已定义
from app.models.knowledge import KnowledgeChunk  # 假定已定义

from app.knowledge.retriever import retrieve



def answer_query(query: str, top_k: int = 3) -> Dict:
    docs = retrieve(query, top_k=top_k)
    # fake LLM response for now
    response = {
        "query": query,
        "answer": "这是一个占位回答；真实实现会调用模型并附带来源",
        "sources": docs,
    }
    return response


def vectorize_knowledge_item(item: KnowledgeItem) -> List[KnowledgeChunk]:
    """
    将 KnowledgeItem 内容切分并向量化，返回 KnowledgeChunk 列表。
    切分方式可按段落或窗口滑动，向量生成可 mock。
    """
    # 内容切分（简单按换行分段）
    chunks = item.content.split('\n') if hasattr(item, 'content') else []
    knowledge_chunks = []
    for idx, chunk in enumerate(chunks):
        # mock 向量生成（用长度填充）
        vector = [float(len(chunk))] * 10  # mock 10维向量
        # mock vector_id
        vector_id = f"vec_{item.id}_{idx}"
        # 构造 KnowledgeChunk
        knowledge_chunk = KnowledgeChunk(
            id=None,
            item_id=item.id,
            content_chunk=chunk,
            vector_id=vector_id,
            sequence=idx,
            source=None,
            reference=None
        )
        knowledge_chunks.append(knowledge_chunk)
    return knowledge_chunks
