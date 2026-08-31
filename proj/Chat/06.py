from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def main():
    # 模拟从 Loader 加载出来的 Document
    doc = Document(
        page_content="LangChain 提供了丰富的组件。包括模型调用、提示词模板、记忆机制等。这些组件可以灵活组合，满足各种业务需求。",
        metadata={"source": "langchain_intro.txt", "author": "Nontee"}
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=30,
        chunk_overlap=5,
        separators=["。", "，", " "]
    )vector_store.similarity_search(query, k=2)

    # 注意这里使用的是 split_documents，传入的是一个列表
    docs = splitter.split_documents([doc])

    print(f"原始文档被切分成了 {len(docs)} 个 Document 对象：\n")
    for i, d in enumerate(docs):
        print(f"--- Document {i+1} ---")
        print("内容:", d.page_content)
        print("元数据:", d.metadata)
        print()

if __name__ == "__main__":
    main()