import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from app.services.rag.embeddings.doubao import DoubaoEmbeddings
from app.core.config import settings


def get_chroma_collection(collection_name: str):
    embedding = DoubaoEmbeddings()
    
    # 使用 chromadb.HttpClient 连接远程 ChromaDB
    client = chromadb.HttpClient(
        host=settings.CHROMADB_HOST,
        port=settings.CHROMADB_PORT,
        settings=Settings(
            allow_reset=True,  # 允许重置集合，适用于测试环境
            anonymized_telemetry=False  # 禁止匿名数据收集，保护隐私
        )
    )
    
    chroma = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedding
    )
    return chroma
