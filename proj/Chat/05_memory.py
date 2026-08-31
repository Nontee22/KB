import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent


def main():
    load_dotenv()

    # 1. 初始化 LLM，降低 temperature 以避免角色扮演幻觉
    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.3,
        streaming=True
    )

    # 2. 定义系统提示词（直接使用字符串，无需 ChatPromptTemplate）
    system_prompt = (
        "你是一个乐于助人的AI助手。"
        "请始终保持专业、客观的身份，禁止进行任何形式的角色扮演或虚构场景描述。"
    )

    # 3. 使用 LangGraph 的 MemorySaver 进行记忆持久化
    memory = MemorySaver()

    # 4. 使用正确的 system_prompt 参数创建 agent
    app = create_agent(
        model=llm,
        system_prompt=system_prompt,
        checkpointer=memory
    )

    # 5. 配置 thread_id 作为会话标识
    config = {"configurable": {"thread_id": "session_1"}}

    response1 = app.invoke(
        {"messages": [("user", "你好，我的名字叫 Nontee。")]},
        config=config
    )
    print("AI:", response1["messages"][-1].content)

    response2 = app.invoke(
        {"messages": [("user", "请问我的名字是什么？")]},
        config=config
    )
    print("AI:", response2["messages"][-1].content)


if __name__ == "__main__":
    main()