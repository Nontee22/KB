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

    # prompt = ChatPromptTemplate.from_template(
    #     "你是{name}，你喜欢小狗，小狗叫小黑"
    # )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是{name}，你喜欢小狗，小狗叫小黑"),
            ("human", "{question}")
        ]
    )

    chain = prompt | llm | StrOutputParser()

    for chunk in chain.stream({"name": "小N", "question": "你是谁"}):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    main()


