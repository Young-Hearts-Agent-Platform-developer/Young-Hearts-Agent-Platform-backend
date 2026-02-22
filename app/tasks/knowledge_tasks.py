import logging
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.knowledge import KnowledgeItem
from app.services.rag.splitters.custom_splitter import CustomSplitter
from app.services.rag.vectorstore.chroma import get_chroma_collection
from langchain_classic.storage import LocalFileStore
from langchain_classic.retrievers import ParentDocumentRetriever
import os

logger = logging.getLogger(__name__)

def parse_document_content(content: str, doc_type: str) -> str:
    """
    解析文档内容。预留多模态文件处理接口。
    如果 content 是文件路径或 URL，根据 doc_type 进行解析。
    """
    # 如果 content 是一个存在的文件路径
    if os.path.isfile(content):
        if doc_type == "txt":
            try:
                with open(content, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read txt file {content}: {e}")
                return content
        elif doc_type in ["pdf", "image", "audio", "video", "png", "jpg", "jpeg", "mp3", "mp4"]:
            logger.info(f"Processing multimodal file type: {doc_type}")
            # TODO: 接入 OCR、版面分析或语音识别等模型
            # return extract_text_from_multimodal(content, doc_type)
            return f"Extracted text from {content} (Placeholder for {doc_type})"
        else:
            # 尝试作为纯文本读取
            try:
                with open(content, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {content}: {e}")
                return content

    # 预留多模态处理逻辑 (如果 content 不是文件路径，但 doc_type 是多模态类型)
    if doc_type in ["pdf", "image", "audio", "video"]:
        logger.info(f"Processing multimodal content type: {doc_type}")
        # TODO: 接入 OCR、版面分析或语音识别等模型
        return content  # 暂且返回原内容或占位符
    
    # 默认作为纯文本处理
    return content

@celery_app.task(name="process_knowledge_document")
def process_knowledge_document(doc_id: int):
    """
    异步处理知识库文档：解析、切片、向量化、入库
    """
    db = SessionLocal()
    doc = None
    try:
        # 1. 获取文档
        doc = db.query(KnowledgeItem).filter(KnowledgeItem.id == doc_id).first()
        if not doc:
            logger.error(f"Document {doc_id} not found.")
            return
        
        doc_risk_level = getattr(doc, "risk_level", "low")
        logger.info(f"Start processing document {doc_id}, risk_level: {doc_risk_level}")
        
        # 2. 解析内容（预留多模态处理）
        doc_content = getattr(doc, "content", "")
        doc_type = getattr(doc, "document_type", "text")
        parsed_content = parse_document_content(str(doc_content), str(doc_type) if doc_type else "text")
        
        # 3. 准备元数据
        doc_title = getattr(doc, "title", "")
        doc_category = getattr(doc, "category", "unknown")
        doc_risk_level = getattr(doc, "risk_level", "low")
        doc_target_audience = getattr(doc, "target_audience", [])
        doc_applicable_age = getattr(doc, "applicable_age", [])
        
        metadata = {
            "source_id": doc.id,
            "title": str(doc_title),
            "category": str(doc_category) if doc_category else "unknown",
            "risk_level": str(doc_risk_level) if doc_risk_level else "low",
            "document_type": str(doc_type) if doc_type else "text",
            "target_audience": ",".join(doc_target_audience) if isinstance(doc_target_audience, list) else "",
            "applicable_age": ",".join(doc_applicable_age) if isinstance(doc_applicable_age, list) else ""
        }
        
        # 4. 获取 Chroma 集合
        vectorstore = get_chroma_collection("knowledge_base")
        
        # 5. 根据风险等级进行切片和入库
        risk_level = str(doc_risk_level) if doc_risk_level else "low"
        if risk_level == "medium":
            # 中风险：使用 ParentDocumentRetriever 逻辑
            # 存储父文档的 Store
            store_path = "./data/parent_docs"
            os.makedirs(store_path, exist_ok=True)
            
            import json
            from langchain_core.documents import Document
            from langchain_classic.storage import EncoderBackedStore, LocalFileStore
            
            def serialize_doc(doc: Document) -> bytes:
                return json.dumps({"page_content": doc.page_content, "metadata": doc.metadata}).encode("utf-8")
                
            def deserialize_doc(data: bytes) -> Document:
                obj = json.loads(data.decode("utf-8"))
                return Document(page_content=obj["page_content"], metadata=obj["metadata"])
                
            fs = LocalFileStore(store_path)
            store = EncoderBackedStore(
                store=fs,
                key_encoder=lambda x: str(x),
                value_serializer=serialize_doc,
                value_deserializer=deserialize_doc
            )
            
            parent_splitter = CustomSplitter.get_medium_risk_parent_splitter()
            child_splitter = CustomSplitter.get_medium_risk_child_splitter()
            
            retriever = ParentDocumentRetriever(
                vectorstore=vectorstore,
                docstore=store,
                child_splitter=child_splitter,
                parent_splitter=parent_splitter,
            )
            
            # ParentDocumentRetriever 会自动调用 parent 和 child splitter，并将子块存入 Chroma，父块存入 Store
            from langchain_core.documents import Document
            full_doc = Document(page_content=parsed_content, metadata=metadata)
            retriever.add_documents([full_doc], ids=None)
            
        else:
            # 高/低风险：直接切片并存入 ChromaDB
            chunks = CustomSplitter.split_document(parsed_content, risk_level, metadata)
            if chunks:
                vectorstore.add_documents(chunks)
        
        # 6. 更新状态为已发布
        setattr(doc, "status", "published")
        db.commit()
        logger.info(f"Document {doc_id} processed successfully.")
        
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {str(e)}")
        db.rollback()
        if doc is not None:
            setattr(doc, "status", "failed")
            db.commit()
        raise e
    finally:
        db.close()
