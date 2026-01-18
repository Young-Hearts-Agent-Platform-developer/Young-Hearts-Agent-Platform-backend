
"""
向量存储适配器抽象接口与占位实现。
本包将承载FAISS/Chroma/Redis等后端适配器。
"""

from abc import ABC, abstractmethod
from typing import List, Any

class VectorStore(ABC):
	@abstractmethod
	def add_documents(self, chunks: List[str], embeddings: List[Any]):
		"""向量入库，占位方法。"""
		pass

	@abstractmethod
	def search(self, query_embedding: Any, top_k: int = 5) -> List[dict]:
		"""向量检索，占位方法。"""
		pass

	@abstractmethod
	def persist(self):
		"""持久化存储（如保存到磁盘/远端），占位方法。"""
		pass

	@abstractmethod
	def load(self):
		"""加载持久化数据，占位方法。"""
		pass

__all__ = ["VectorStore"]

__all__ = []
