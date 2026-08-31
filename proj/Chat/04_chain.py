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

    translate_prompt = ChatPromptTemplate.from_template(
        "请把下面内容翻译成英文：\n\n{text}"
    )

    summary_prompt = ChatPromptTemplate.from_template(
        "请用一句话总结下面内容：\n\n{text}"
    )

    default_prompt = ChatPromptTemplate.from_template(
        "请回答下面问题：\n\n{text}"
    )

    translate_chain = translate_prompt | llm | StrOutputParser()
    summary_chain = summary_prompt | llm | StrOutputParser()
    default_chain = default_prompt | llm | StrOutputParser()

    router_chain = RunnableBranch(
        (lambda x: "翻译" in x["text"], translate_chain),
        (lambda x: "总结" in x["text"], summary_chain),
        default_chain
    )

    result1 = router_chain.invoke({
        "text": "请翻译：今天天气不错"
    })

    result2 = router_chain.invoke({
        "text": "请总结：LangChain 是一个用于构建大语言模型应用的开发框架。"
    })

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
