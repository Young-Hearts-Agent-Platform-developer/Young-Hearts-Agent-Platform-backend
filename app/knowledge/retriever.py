import os
from functools import lru_cache
from typing import List, Dict, Tuple, Optional, Any
from app.core.config import settings  # 假设你有 config.py 管理 env

try:
    from langchain_chroma import Chroma
    # 豆包兼容 OpenAI 接口，所以继续用 OpenAIEmbeddings
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
except ImportError:
    print("Warning: LangChain dependencies not found.")
    Document = Any
    Chroma = Any

# --- 1. 配置管理 (专门适配你的 .env 文件) ---
class RetrieverConfig:
    # 向量数据库保存路径
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma_db_data")
    
    # 检索阈值 (0-1)
    SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", 0.6))
    
    # --- 核心修改：读取 ARK_ 开头的环境变量 ---
    
    # 1. API Key
    # 优先读取 ARK_API_KEY (你的配置文件), 如果没有则读 EMBEDDING_API_KEY
    EMBEDDING_API_KEY: str = os.getenv("ARK_API_KEY", os.getenv("EMBEDDING_API_KEY"))
    
    # 2. Base URL
    # 你的配置文件是: https://ark.cn-beijing.volces.com/api/v3
    EMBEDDING_BASE_URL: str = os.getenv("ARK_BASE_URL", os.getenv("EMBEDDING_BASE_URL"))
    
    # 3. Embedding 模型 ID
    # ⚠️ 注意：这里不能用 Chat 模型 ID (doubao-lite)
    # 建议你在 .env 增加一个 ARK_EMBEDDING_MODEL
    # 如果没找到，代码会尝试读取 ARK_MODEL，但这可能会报错
    EMBEDDING_MODEL: str = os.getenv("ARK_EMBEDDING_MODEL", os.getenv("ARK_MODEL"))

config = RetrieverConfig()

# --- 2. 检索器类 ---

class KnowledgeRetriever:
    def __init__(self):
        # 检查 Key
        if not config.EMBEDDING_API_KEY:
            raise ValueError("未配置 API Key，请检查 .env 文件中的 ARK_API_KEY")

        print(f"[Init] Loading Embedding Model: {config.EMBEDDING_MODEL}")

        # 初始化 Embedding 模型 (火山引擎适配)
        self.embedding_model = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.EMBEDDING_API_KEY,
            openai_api_base=config.EMBEDDING_BASE_URL,
            # 火山引擎不需要自动检查 token 长度，关闭以避免兼容性报错
            check_embedding_ctx_length=False 
        )

        # 初始化向量库连接
        if not os.path.exists(config.CHROMA_PATH):
            print(f"Warning: 数据库路径 {config.CHROMA_PATH} 不存在，检索结果将为空。")

        self.vectorstore = Chroma(
            persist_directory=config.CHROMA_PATH,
            embedding_function=self.embedding_model,
            collection_name="rag_knowledge_base"
        )

    async def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[Document], str]:
        """
        异步检索方法
        """
        if not query.strip():
            return [], "empty_query"

        try:
            # 执行相似度搜索
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query, k=top_k
            )
        except Exception as e:
            print(f"ChromaDB/Embedding Error: {e}")
            # 如果是 Embedding 模型选错，这里通常会报 400 Bad Request
            return [], "db_error"

        filtered_docs = []
        for doc, score in results:
            print(f"[Debug] 片段得分: {score:.4f} (阈值: {config.SCORE_THRESHOLD})")
            
            if score >= config.SCORE_THRESHOLD:
                doc.metadata["relevance_score"] = round(score, 4)
                filtered_docs.append(doc)

        if not filtered_docs:
            return [], "no_relevant_info_found"

        return filtered_docs, "success"

# --- 3. 单例与业务逻辑 ---

@lru_cache()
def get_retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever()

async def search_documents(query: str, top_k: int = 3) -> Dict:
    """API 服务层调用的入口"""
    retriever = get_retriever()
    docs, status = await retriever.retrieve(query, top_k=top_k)

    response = {
        "status": "success",
        "message": "检索成功",
        "documents": []
    }

    if status == "no_relevant_info_found":
        response["status"] = "fallback"
        response["message"] = "暂无相关信息，建议转人工。"
        return response
    
    if status in ["empty_query", "db_error"]:
        response["status"] = "error"
        response["message"] = f"检索失败: {status}"
        return response

    response["documents"] = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source_id", "Unknown"),
            "score": doc.metadata.get("relevance_score", 0),
            "page": doc.metadata.get("page", 1)
        } for doc in docs
    ]
    
    return response