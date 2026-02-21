import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# 1. 加载文档
def load_documents(file_path):
    loader = TextLoader(file_path, encoding="utf-8")
    return loader.load()
# loader = TextLoader("knowledge_base.txt")
# documents = loader.load()

# 2. 文本切分
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(documents)


# 3. 向量化并存储
def store_embeddings(splits):
    embeddings = OpenAIEmbeddings(
        api_key="sk-vN1JPLmnkjp740WRDyDQBWEOqagOpVL14ZPG0kAWF1HRISsW",
        base_url="https://sg.uiuiapi.com/v1",
        model="text-embedding-ada-002",
        # model_kwargs={"do_tokenize": False}  # 如果支持此参数
    )
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db",
    )
    print(f"成功将 {len(splits)} 个文本块存入向量数据库")
    return vectorstore

    
if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    kb_path = os.path.join(base_dir, "knowledge_base.txt")
    documents = load_documents(kb_path)
    splits = split_documents(documents)
    store_embeddings(splits)
    print("当前工作目录：", os.getcwd())