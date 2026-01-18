"""
FaissVectorStore 预留实现，继承 BaseVectorStore。
"""
from .base import BaseVectorStore

class FaissVectorStore(BaseVectorStore):
    def add_vector(self, vector, metadata):
        raise NotImplementedError("FaissVectorStore 尚未实现")

    def search_vector(self, query_vector, top_k=5):
        raise NotImplementedError("FaissVectorStore 尚未实现")
