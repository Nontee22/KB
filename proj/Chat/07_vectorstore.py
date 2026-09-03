"""
章节 07：向量库从零构建 —— 拆分文档 -> 转向量 -> 入库 -> 检索
================================================
【本章学什么】
1. RecursiveCharacterTextSplitter：把长文本按标点/空格切成小块(chunk)，并留一点重叠
2. Chroma：一个轻量向量数据库，能把文本向量存起来并能做相似度搜索
3. 完整流程：Document -> 切分 -> 向量化入库 -> similarity_search 检索

【和 06 的关系】
06 是"读"一个已经建好的库来问答；本章是"建库"的过程。两者配合才是一个完整的 RAG。

【运行前】同目录需有 .env；依赖：pip install langchain-openai langchain-chroma langchain-text-splitters python-dotenv
"""
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def main():
    load_dotenv()

    # 1. 准备入库的原始文档（Document 是 LangChain 的基础数据单元：正文 + 元信息 metadata）
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
    #    chunk_size=30 每块最多约30字符；chunk_overlap=5 相邻块重叠5字符，避免语义被切断
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=30,
        chunk_overlap=5,
        separators=["。", "，", " "]
    )
    split_docs = splitter.split_documents(docs)

    # 3. 创建向量数据库
    #    OpenAIEmbeddings：把文本转成高维向量；embedding_function 告诉数据库用哪个模型转向量
    embeddings = OpenAIEmbeddings(
        model="BAAI/bge-m3",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
    )
    vector_store = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings,
    )
    # 把切好的文档块转成向量并写进数据库（会在 ./chroma_db 目录生成持久化文件）
    vector_store.add_documents(split_docs)

    # 4. 检索最相似的 2 个片段：把 query 也转成向量，和库里所有向量比相似度，取最高的 k 个
    query = "什么是机器学习？"
    results = vector_store.similarity_search(query, k=2)
    for i, doc in enumerate(results, 1):
        print(f"[文档 {i}] (来源: {doc.metadata.get('source')})\n{doc.page_content}\n")


if __name__ == "__main__":
    main()
