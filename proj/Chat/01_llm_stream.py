import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def main():
    load_dotenv()

    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=1,
        streaming=True
    )

    messages = [
        SystemMessage(content="你是小N,你喜欢小狗"),
        HumanMessage(content="请用三句话介绍你自己")
    ]

    for chunk in llm.stream(messages):
        print(chunk.content, end="", flush=True)

    # response = llm.invoke(messages)
    #
    # print(response.content)

if __name__ == "__main__":
    main()


