from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class CustomSplitter:
    """
    定制化切片策略：
    - 高风险文档：严格结构切片（100-1024 token，20%重叠）
    - 中风险文档：混合分层切片（父块 512-2048 token，子块 128-512 token，10%-15%重叠）
    - 低风险文档：语义切片（64-512 token，5%-10%重叠）
    """

    @staticmethod
    def get_high_risk_splitter() -> RecursiveCharacterTextSplitter:
        # 严格结构切片
        return RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=200,  # 约 20%
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )

    @staticmethod
    def get_medium_risk_parent_splitter() -> RecursiveCharacterTextSplitter:
        # 父块
        return RecursiveCharacterTextSplitter(
            chunk_size=2048,
            chunk_overlap=0,
            separators=["\n\n", "\n", "。", " ", ""]
        )

    @staticmethod
    def get_medium_risk_child_splitter() -> RecursiveCharacterTextSplitter:
        # 子块
        return RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,  # 约 10%
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )

    @staticmethod
    def get_low_risk_splitter() -> RecursiveCharacterTextSplitter:
        # 语义切片
        return RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,  # 约 10%
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    @classmethod
    def split_document(cls, content: str, risk_level: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        根据风险等级切分文档，并附加标准化元信息。
        注意：中风险文档的父子块切分逻辑通常由 ParentDocumentRetriever 内部处理，
        这里仅提供基础切分或为非 ParentDocumentRetriever 场景提供备用。
        """
        # 确保元数据中包含风险等级
        metadata["risk_level"] = risk_level
        doc = Document(page_content=content, metadata=metadata)
        
        if risk_level == "high":
            splitter = cls.get_high_risk_splitter()
            return splitter.split_documents([doc])
        elif risk_level == "medium":
            # 对于中风险文档，如果直接调用此方法，我们返回父块切分结果
            # 实际使用中，ParentDocumentRetriever 会自己调用 parent_splitter 和 child_splitter
            splitter = cls.get_medium_risk_parent_splitter()
            return splitter.split_documents([doc])
        else:
            # 默认为低风险
            splitter = cls.get_low_risk_splitter()
            return splitter.split_documents([doc])
