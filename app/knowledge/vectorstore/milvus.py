"""
MilvusVectorStore 预留实现，继承 BaseVectorStore。
"""
from .base import BaseVectorStore

class MilvusVectorStore(BaseVectorStore):
    def add_vector(self, vector, metadata):
        raise NotImplementedError("MilvusVectorStore 尚未实现")

    def search_vector(self, query_vector, top_k=5):
        raise NotImplementedError("MilvusVectorStore 尚未实现")
