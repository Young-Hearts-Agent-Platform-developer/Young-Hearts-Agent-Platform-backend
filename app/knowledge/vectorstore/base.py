"""
BaseVectorStore 接口定义，便于多后端适配。
"""
from typing import Any, List

class BaseVectorStore:
    def add_vector(self, vector: List[float], metadata: dict) -> Any:
        """
        添加向量到向量库。
        :param vector: 向量数据
        :param metadata: 相关元数据（如 item_id, chunk_id 等）
        :return: 向量ID或相关信息
        """
        raise NotImplementedError("add_vector 方法需由具体实现类完成")

    def search_vector(self, query_vector: List[float], top_k: int = 5) -> List[Any]:
        """
        检索与 query_vector 最相似的 top_k 个向量。
        :param query_vector: 查询向量
        :param top_k: 返回最相似的数量
        :return: 检索结果列表
        """
        raise NotImplementedError("search_vector 方法需由具体实现类完成")
