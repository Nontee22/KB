"""
章节 08：用 LangGraph 手动搭图 —— 带记忆的聊天机器人（底层版）
================================================
【本章学什么】
1. StateGraph：把聊天流程画成一个"图"，节点是普通函数，边是流转方向
2. Annotated[list, add_messages]：告诉 LangGraph 这个字段要"追加"，而不是整体覆盖
3. MemorySaver + thread_id：用同一个 ID 记住多轮对话

【和 05 的区别】
- 05 用 create_agent() 高层封装，一行就能带记忆
- 本章用 StateGraph 自己定义节点和边，看得更明白、也更好定制

【运行前】同目录需有 .env；依赖：pip install langgraph langchain-openai python-dotenv
"""
# ============ 完整可跑的小例子：带记忆的聊天机器人 ============
# pip install langgraph langchain-openai
import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# ---------- 1. State：公共大字典 ----------
# messages 字段用 Annotated[list, add_messages] 标注：
# 每次写入会"追加"到历史里，而不是整体覆盖 —— 这是记忆能一直累积的关键
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # 聊天记录，自动追加

load_dotenv()
# ---------- 2. 节点：普通函数 ----------
# 节点就是一个"吃 dict、吐 dict"的函数，图上节点之间传递的就是这个 dict
llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.7,
        streaming=True
    )

def 聊天(state):
    result = llm.invoke(state["messages"])    # 读：历史自动在messages里
    return {"messages": [result]}             # 写：返回 AIMessage 对象，add_messages 才能正确追加

# ---------- 3. 建图 ----------
# 定义图：添加节点"聊天"，并连接 起点(START) -> 聊天 -> 终点(END)
graph = StateGraph(AgentState)
graph.add_node("聊天", 聊天)
graph.add_edge(START, "聊天")
graph.add_edge("聊天", END)

# ---------- 4. 编译（挂上记忆）----------
# checkpointer=memory：每轮运行结束把状态(对话历史)存起来，下一轮继续用
memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# ---------- 5. 运行 ----------
config = {"configurable": {"thread_id": "会话1"}}   # 同一个ID = 同一段记忆

# 第1轮
result = app.invoke({"messages": [("user", "我叫小明")]}, config)
print(result["messages"][-1].content)   # [-1] 取最后一条消息，即 AI 的回复

# 第2轮：不传历史，看它记不记得！（依赖上面的 thread_id 和 add_messages 累积的历史）
result = app.invoke({"messages": [("user", "我叫什么？")]}, config)
print(result["messages"][-1].content)   # ← 会答出"小明"，说明State记住了
