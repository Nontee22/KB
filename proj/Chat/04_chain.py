"""
章节 04：用 RunnableBranch 做"条件路由" —— 根据输入自动选不同的处理链
================================================
【本章学什么】
1. 把同一个 llm 配成三种不同 prompt 的链：翻译 / 总结 / 普通问答
2. RunnableBranch( (条件1, 链1), (条件2, 链2), 兜底链 )：
   从上到下依次判断，条件为真就走对应链；都不满足就走最后一个兜底链

【流程示意】
输入 {"text": "..."}
   -> 文本含"翻译"？ -> 走翻译链
   -> 文本含"总结"？ -> 走总结链
   -> 以上都不是     -> 走兜底问答链

【运行前】同目录需有 .env；依赖：pip install langchain-openai langchain-core python-dotenv
"""
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


def main():
    load_dotenv()

    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.7,
        streaming=True
    )

    # 用 from_template() 定义三种"单段文本"模板（{text} 是占位符）
    translate_prompt = ChatPromptTemplate.from_template(
        "请把下面内容翻译成英文：\n\n{text}"
    )

    summary_prompt = ChatPromptTemplate.from_template(
        "请用一句话总结下面内容：\n\n{text}"
    )

    default_prompt = ChatPromptTemplate.from_template(
        "请回答下面问题：\n\n{text}"
    )

    # 每条链 = 模板 |> LLM |> 只取文字部分
    translate_chain = translate_prompt | llm | StrOutputParser()
    summary_chain = summary_prompt | llm | StrOutputParser()
    default_chain = default_prompt | llm | StrOutputParser()

    # RunnableBranch：条件用 lambda 判断，命中就走对应链；最后的 default_chain 是兜底
    router_chain = RunnableBranch(
        (lambda x: "翻译" in x["text"], translate_chain),
        (lambda x: "总结" in x["text"], summary_chain),
        default_chain
    )

    # 测试1：文本里含"翻译"，走翻译链
    result1 = router_chain.invoke({
        "text": "请翻译：今天天气不错"
    })

    # 测试2：文本里含"总结"，走总结链
    result2 = router_chain.invoke({
        "text": "请总结：LangChain 是一个用于构建大语言模型应用的开发框架。"
    })

    # 测试3：都不含，走兜底问答链
    result3 = router_chain.invoke({
        "text": "什么是向量数据库？"
    })

    print("翻译任务结果：")
    print(result1)

    print("\n总结任务结果：")
    print(result2)

    print("\n普通问答结果：")
    print(result3)


if __name__ == "__main__":
    main()
