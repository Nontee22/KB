"""
章节 02：用 ChatPromptTemplate 管理提示词（Prompt）
================================================
【本章学什么】
1. 为什么用 Prompt 模板：把"提示词"和"变量"分离，方便复用和动态换内容
2. ChatPromptTemplate.from_messages()：用 [(角色, 内容), ...] 的形式定义多段消息
3. 模板占位符 {name} / {question}：调用时用字典传入具体值，自动替换

【与 01 的区别】
01 是手动构造 SystemMessage/HumanMessage；
本章改成"模板"，之后变量可以在调用时动态注入，更适合做成聊天机器人。

【运行前】同目录需有 .env；依赖：pip install langchain-openai langchain-core python-dotenv
"""
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def main():
    load_dotenv()

    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.7,
        streaming=True
    )

    # 方式一：from_template()，适合"只有一段纯文本"的简单模板（这里先注释掉）
    # prompt = ChatPromptTemplate.from_template(
    #     "你是{name}，你喜欢小狗，小狗叫小黑"
    # )

    # 方式二（本章重点）：from_messages()，按"消息角色"写模板
    # ("system", ...) 是系统设定；("human", ...) 是用户输入
    # {name} / {question} 是占位符，调用时用字典传入真实值
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是{name}，你喜欢小狗，小狗叫小黑"),
            ("human", "{question}")
        ]
    )

    # LCEL 管道符 | 把组件串成一条流水线：
    # prompt(拼好提示词) -> llm(交给模型) -> StrOutputParser(只取文字部分)
    chain = prompt | llm | StrOutputParser()

    # 传入字典，模板里的 {name} 和 {question} 会被替换成这里的值
    # stream() 流式打印，和 01 一样是逐字输出
    for chunk in chain.stream({"name": "小N", "question": "你是谁"}):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    main()
