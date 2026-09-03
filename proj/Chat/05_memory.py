"""
章节 05：让 Agent 带上"记忆" —— 用 MemorySaver 记住多轮对话
================================================
【本章学什么】
1. LangChain 高层 Agent 封装：create_agent()（来自 langchain.agents）
2. 用 LangGraph 的 MemorySaver() 记住对话历史
3. 用 config 里的 thread_id 区分"不同会话"，同一个 thread_id 才共享记忆

【本章和 08 的区别】
- 05 用 create_agent()（LangChain 高层封装，一行开箱即用）
- 08 用 StateGraph() 自己搭图（底层、可定制）—— 两者都能做"带记忆的聊天"

【运行前】同目录需有 .env；依赖：pip install langgraph langchain-openai langchain python-dotenv
（注意：create_agent 需要较新的 langchain 版本，若报 ImportError 请先升级）

【小知识】messages 里的 ("user", 内容) 是元组写法，等价于 HumanMessage(内容)。
"""
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
    #    checkpointer=memory 让 agent 能把每一轮对话存起来、并在下一轮读回来
    app = create_agent(
        model=llm,
        system_prompt=system_prompt,
        checkpointer=memory
    )

    # 5. 配置 thread_id 作为会话标识：同一 thread_id = 同一段记忆
    config = {"configurable": {"thread_id": "session_1"}}

    # 第1轮：告诉模型你的名字。messages 里用 ("user", 内容) 的元组形式表示用户发言
    response1 = app.invoke(
        {"messages": [("user", "你好，我的名字叫 Nontee。")]},
        config=config
    )
    print("AI:", response1["messages"][-1].content)   # [-1] 取最后一条消息，即 AI 的回复

    # 第2轮：没有重新说名字，但因为共享同一个 thread_id，模型还记得
    response2 = app.invoke(
        {"messages": [("user", "请问我的名字是什么？")]},
        config=config
    )
    print("AI:", response2["messages"][-1].content)


if __name__ == "__main__":
    main()
