import chromadb

# 连接到 Docker 中的 ChromaDB
client = chromadb.HttpClient(host="localhost", port=8000)

# 列出所有集合
collections = client.list_collections()
print("已存在的集合：")

if not collections:
    print("  (当前没有任何集合)")

for coll in collections:
    print(f"\n- 集合名称: {coll.name}")
    
    # 获取集合对象
    collection = client.get_collection(name=coll.name)
    
    # 获取集合中的文档数量
    count = collection.count()
    print(f"  文档数量: {count}")
    
    if count > 0:
        # 查看前几个文档
        print("  前 3 个文档示例:")
        results = collection.peek(limit=3)
        
        if results and 'ids' in results:
            for i in range(len(results['ids'])):
                doc_id = results['ids'][i]
                metadata = results['metadatas'][i] if results.get('metadatas') else None
                document = results['documents'][i] if results.get('documents') else None
                
                print(f"    - ID: {doc_id}")
                if metadata:
                    print(f"      Metadata: {metadata}")
                if document:
                    doc_preview = document[:100] + "..." if len(document) > 100 else document
                    print(f"      Document: {doc_preview}")