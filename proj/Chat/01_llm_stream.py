"""
章节 01：连接大模型并流式输出回答
================================================
【本章学什么】
1. 用 ChatOpenAI 对接 SiliconFlow（OpenAI 兼容接口）
2. 用 SystemMessage + HumanMessage 构造消息：
   SystemMessage = "角色设定"（告诉模型你是谁）
   HumanMessage   = "用户提问"
3. 对比 llm.stream()（打字机式，逐字输出）与 llm.invoke()（等全部生成完再返回）

【运行前】
- 同目录需有 .env 文件，内容至少一行：
  API_KEY=你的SiliconFlow密钥
- 依赖安装：pip install langchain-openai langchain-core python-dotenv

【小知识】
temperature 越大回答越"放飞"，越小越"规矩"，范围一般 0~2，常用 0.3~1.0。
"""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def main():
    # 读取同目录下的 .env，把里面的 API_KEY 等变量加载进环境变量
    load_dotenv()

    # 创建"大模型客户端"对象
    # - model：要对话的模型名（这里用的硅基流动 SiliconFlow 提供的 Qwen3-8B）
    # - api_key / base_url：SiliconFlow 走 OpenAI 兼容协议，所以填它的密钥和接口地址
    # - temperature：随机性，1.0 表示回答比较发散
    # - streaming=True：配合下面的 stream() 实现逐字输出
    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=1,
        streaming=True
    )

    # 一次对话 = 一个"消息列表"，按顺序发给模型
    messages = [
        SystemMessage(content="你是小N,你喜欢小狗"),   # 系统角色设定
        HumanMessage(content="请用三句话介绍你自己")    # 用户提问
    ]

    # stream() 是流式：一次返回一块内容(chunk)，边生成边打印，适合做打字机效果
    for chunk in llm.stream(messages):
        print(chunk.content, end="", flush=True)  # flush=True 让这块内容立刻刷到屏幕，不攒着

    # 对比：invoke() 是非流式，要等模型把整段话生成完才一次性返回（下面这段被注释掉）
    # response = llm.invoke(messages)
    #
    # print(response.content)


if __name__ == "__main__":
    main()
