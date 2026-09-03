# ============ 完整可跑的小例子：带记忆的聊天机器人 ============
# pip install langgraph langchain-openai
import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

# ---------- 1. State：公共大字典 ----------
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # 聊天记录，自动追加

# ---------- 2. 节点：普通函数 ----------
llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.7,
        streaming=True
    )

def 聊天(state):
    result = llm.invoke(state["messages"])    # 读：历史自动在messages里
    return {"messages": [result.content]}     # 写：自动追加进历史

# ---------- 3. 建图 ----------
graph = StateGraph(AgentState)
graph.add_node("聊天", 聊天)
graph.add_edge(START, "聊天")
graph.add_edge("聊天", END)

# ---------- 4. 编译（挂上记忆）----------
memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# ---------- 5. 运行 ----------
config = {"configurable": {"thread_id": "会话1"}}   # 同一个ID = 同一段记忆

# 第1轮
result = app.invoke({"messages": ["我叫小明"]}, config)
print(result["messages"][-1].content)

# 第2轮：不传历史，看它记不记得！
result = app.invoke({"messages": ["我叫什么？"]}, config)
print(result["messages"][-1].content)   # ← 会答出"小明"，说明State记住了
