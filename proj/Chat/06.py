import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def main():
    load_dotenv()

    # 1. 准备入库的原始文档
    docs = [
        Document(
            page_content="机器学习是人工智能的一个分支，它让计算机从数据中学习规律。",
            metadata={"source": "机器学习.md"},
        ),
        Document(
            page_content="深度学习是机器学习的一种方法，它使用多层神经网络提取特征。",
            metadata={"source": "深度学习.md"},
        ),
    ]

    # 2. 先拆分文档，再向量化入库（原来 splitter 定义在入库之后，等于没用到）
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=30,
        chunk_overlap=5,
        separators=["。", "，", " "]
    )
    split_docs = splitter.split_documents(docs)

    # 3. 创建向量数据库
    embeddings = OpenAIEmbeddings(
        model="BAAI/bge-m3",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
    )
    vector_store = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
    )
    vector_store.add_documents(split_docs)

    # 4. 检索最相似的 2 个片段
    query = "什么是机器学习？"
    results = vector_store.similarity_search(query, k=2)
    for i, doc in enumerate(results, 1):
        print(f"[文档 {i}] (来源: {doc.metadata.get('source')})\n{doc.page_content}\n")


if __name__ == "__main__":
    main()
