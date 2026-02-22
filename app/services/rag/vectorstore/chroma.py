import chromadb
from langchain_chroma import Chroma
from app.services.rag.embeddings.doubao import DoubaoEmbeddings
from app.core.config import settings


def get_chroma_collection(collection_name: str):
    embedding = DoubaoEmbeddings()
    
    # 使用 chromadb.HttpClient 连接远程 ChromaDB
    client = chromadb.HttpClient(
        host=settings.CHROMADB_HOST,
        port=settings.CHROMADB_PORT
    )
    
    chroma = Chroma(
        collection_name=collection_name,
        embedding_function=embedding,
        client=client
    )
    return chroma
