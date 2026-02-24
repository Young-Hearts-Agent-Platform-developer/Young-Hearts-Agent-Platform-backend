import chromadb
import sys


# 删除 ChromaDB 中名为 "knowledge_base" 的集合中所有数据
def main():
    client = chromadb.HttpClient(host="localhost", port=8001)
    collection_name = "knowledge_base"

    # 检查集合是否存在
    collections = client.list_collections()
    existing_names = [c.name for c in collections]

    if collection_name not in existing_names:
        print(f"集合 '{collection_name}' 不存在。")
        return

    # 优先尝试直接删除整个集合（如果客户端支持）
    try:
        if hasattr(client, "delete_collection"):
            client.delete_collection(name=collection_name)
            print(f"已删除集合 '{collection_name}' 及其所有数据。")
            return
    except Exception as e:
        print("直接删除集合失败，准备逐条删除文档，错误：", e)

    # 回退到逐条删除文档
    collection = client.get_collection(name=collection_name)
    count = collection.count()

    if count == 0:
        print("集合为空，无需删除。")
        return

    confirm = input(f"确定要删除集合 '{collection_name}' 中的 {count} 条文档吗？输入 'yes' 确认: ")
    if confirm.strip().lower() != 'yes':
        print("已取消操作。")
        return

    # 获取所有文档 id 并分批删除
    try:
        results = collection.peek(limit=count)
        ids = results.get('ids', []) if results else []
    except Exception:
        ids = []

    if not ids:
        try:
            # 尝试调用无参数的 delete（部分实现可能支持）
            collection.delete()
            print("已调用 collection.delete() 清空集合（若此接口受支持）。")
        except Exception as ex:
            print("未能获取到文档 id，且调用 collection.delete() 失败：", ex)
        return

    batch_size = 1000
    total_deleted = 0
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        try:
            collection.delete(ids=batch)
            total_deleted += len(batch)
            print(f"删除了 {len(batch)} 条文档（累计 {total_deleted}）。")
        except Exception as ex:
            print(f"删除批次失败（{i} 到 {i+batch_size}）：", ex)

    print(f"操作完成，已尝试删除 {total_deleted} 条文档。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        try:
            import posthog

            if getattr(posthog, 'default_client', None) is not None:
                try:
                    posthog.shutdown()
                except Exception:
                    pass
        except Exception:
            pass
