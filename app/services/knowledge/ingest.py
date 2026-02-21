from abc import ABC, abstractmethod

# 嵌入模型抽象基类
class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list:
        """将文本列表转为向量（占位方法）。"""
        pass

"""
知识库数据注入工具：
- 支持目录递归与多格式自动识别（md/html/txt）
- 按语义分片（占位实现）
- 嵌入计算与向量存储（依赖抽象接口）
"""


import os
from typing import Iterable, List, Union


def load_files_from_dir(path: str, exts=(".md", ".txt", ".html")) -> List[str]:
    """
    递归加载目录下所有指定格式文件，返回文本内容列表（占位实现）。
    """
    docs = []
    for root, _, files in os.walk(path):
        for fname in files:
            if fname.lower().endswith(exts):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        docs.append(f.read())
                except Exception:
                    pass  # 占位：实际应有日志
    return docs

def split_texts(docs: Iterable[str], chunk_size: int = 500) -> List[str]:
    """
    按语义分片（占位实现：简单按段落或句号分割，后续可接入更智能分割器）。
    """
    chunks = []
    for doc in docs:
        # 占位：优先按段落分割，否则按句号分割
        for para in doc.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            if len(para) > chunk_size:
                # 简单按句号分割
                sentences = para.split("。")
                buf = ""
                for sent in sentences:
                    if not sent.strip():
                        continue
                    if len(buf) + len(sent) < chunk_size:
                        buf += sent + "。"
                    else:
                        chunks.append(buf)
                        buf = sent + "。"
                if buf:
                    chunks.append(buf)
            else:
                chunks.append(para)
    return [c for c in chunks if c.strip()]

def ingest_documents(
    source: Union[str, Iterable[str]],
    vectorstore,
    embedder,
    file_exts=(".md", ".txt", ".html"),
    chunk_size: int = 500
) -> dict:
    """
    数据注入主流程：支持目录/文件路径或直接传文本，自动识别格式，分片、嵌入、入库。
    """
    # 1. 加载文本
    if isinstance(source, str) and os.path.isdir(source):
        docs = load_files_from_dir(source, exts=file_exts)
    elif isinstance(source, str) and os.path.isfile(source):
        try:
            with open(source, "r", encoding="utf-8") as f:
                docs = [f.read()]
        except Exception:
            docs = []
    else:
        docs = list(source)
    doc_count = len(docs)
    # 2. 分片
    chunks = split_texts(docs, chunk_size=chunk_size)
    # 3. 嵌入计算
    embeddings = embedder.embed(chunks)  # 占位：embedder 需实现 embed(list[str])
    # 4. 入库
    vectorstore.add_documents(chunks, embeddings)  # 占位：vectorstore 需实现 add_documents
    return {"ingested": len(chunks), "documents": doc_count}
