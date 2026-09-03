"""
章节 06：RAG 知识库问答（检索增强生成）
================================================
【本章学什么】
1. RAG 核心思想：先"检索"和问题相关的资料片段，再把片段一起喂给大模型，让答案有依据
2. 步骤：加载向量库 -> 检索器 retriever -> 组装 prompt -> 交给 LLM -> 输出答案
3. LCEL 中 RunnablePassthrough.assign 与检索器的配合：把检索结果塞进 context 字段供 prompt 用

【前提】本章需要已存在 "rag_chroma_db" 向量库目录。
        该库通常由 07 章（向量库构建）或专门建库脚本生成；若没有请先跑建库脚本。

【运行前】同目录需有 .env；依赖：pip install langchain-openai langchain-chroma langchain-core python-dotenv
"""
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
    """构造 OpenAIEmbeddings（SiliconFlow 向量接口）—— 把文本转成向量做相似度计算"""
    return OpenAIEmbeddings(
        model="BAAI/bge-m3",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
    )


def format_docs(docs):
    """将检索到的 Document 列表格式化为字符串 —— 方便直接塞进 prompt 里的 {context}"""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        formatted.append(f"[文档 {i}] (来源: {source})\n{doc.page_content}")
    return "\n\n".join(formatted)


def main():
    load_dotenv()  # 读取 .env 中的 API_KEY

    # 1. 打开已存在的向量数据库（提供 embedding_function，它入库时就按这个模型算向量）
    print("正在加载知识库...")
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory="./rag_chroma_db",
        embedding_function=embeddings
    )

    # 2. 把向量库变成一个"检索器"，k=2 表示每次取最相似的两段资料
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}  # 每次检索返回最相似的 2 个文档
    )

    # 3. 构建 RAG Prompt：检索来的资料放 {context}，用户问题放 {question}
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的知识库问答助手。请根据提供的参考文档来回答用户的问题。
如果参考文档中没有相关信息，请明确告知用户你不知道，不要编造答案。

参考文档：
{context}"""),
        ("human", "{question}")
    ])

    # 4. 获取大模型（RAG 场景通常 temperature=0，让它更"照章办事"、少胡编）
    llm = get_llm(temperature=0)

    # 5. 构建 RAG 链：
    #    assign(context=retriever|format_docs)：先检索并格式化资料，塞进 context 字段
    #    再把 context+question 交给 prompt -> llm -> 取出文字
    rag_chain = (
            RunnablePassthrough.assign(
                context=retriever | RunnableLambda(format_docs)
            )
            | rag_prompt
            | llm
            | StrOutputParser()
    )

    # 6. 交互式问答循环
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
