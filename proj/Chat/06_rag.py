import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def get_llm(temperature=0):
    """构造 ChatOpenAI（SiliconFlow）"""
    return ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=temperature,
    )


def get_embeddings():
    """构造 OpenAIEmbeddings（SiliconFlow 向量接口）"""
    return OpenAIEmbeddings(
        model="BAAI/bge-m3",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
    )


def format_docs(docs):
    """将检索到的 Document 列表格式化为字符串"""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        formatted.append(f"[文档 {i}] (来源: {source})\n{doc.page_content}")
    return "\n\n".join(formatted)


def main():
    load_dotenv()  # 读取 .env 中的 API_KEY

    # 1. 加载已存在的向量数据库
    print("正在加载知识库...")
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory="./rag_chroma_db",
        embedding_function=embeddings
    )

    # 2. 创建检索器
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}  # 每次检索返回最相似的 2 个文档
    )

    # 3. 构建 RAG Prompt
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的知识库问答助手。请根据提供的参考文档来回答用户的问题。
如果参考文档中没有相关信息，请明确告知用户你不知道，不要编造答案。

参考文档：
{context}"""),
        ("human", "{question}")
    ])

    # 4. 获取大模型
    llm = get_llm(temperature=0)

    # 5. 构建 RAG 链
    rag_chain = (
            RunnablePassthrough.assign(
                context=retriever | RunnableLambda(format_docs)
            )
            | rag_prompt
            | llm
            | StrOutputParser()
    )

    # 6. 开始问答
    print("知识库加载完成！开始问答（输入 'quit' 退出）\n")

    while True:
        question = input("你的问题: ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if not question:
            continue

        print("\n正在思考...")
        answer = rag_chain.invoke({"question": question})
        print(f"\nAI 回答:\n{answer}\n")
        print("-" * 50)


if __name__ == "__main__":
    main()