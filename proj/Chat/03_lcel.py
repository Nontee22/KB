import os
import json
from datetime import datetime
from typing import Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


def analyze_response(data: Dict[str, Any]) -> Dict[str, Any]:
    answer = data.get("answer", "")
    char_count = len(answer)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in answer)

    # 简易情感词典（生产环境建议替换为 LLM 判定或专业 NLP 库）
    positive_words = ["优秀", "棒", "爱", "开心", "高兴", "喜欢"]
    negative_words = ["差", "不好", "糟糕", "讨厌", "难过", "不喜欢"]

    sentiment = "中性"
    if any(word in answer for word in positive_words):
        sentiment = "正面"
    elif any(word in answer for word in negative_words):
        sentiment = "负面"

    return {
        **data,
        "char_count": char_count,
        "has_chinese": has_chinese,
        "sentiment": sentiment,
        "analysis_timestamp": datetime.now().isoformat(),
        "response_quality": "详细" if char_count > 100 else "简洁"
    }

def main() -> None:
    """主入口函数"""
    load_dotenv()

    llm = ChatOpenAI(
        model="Qwen/Qwen3-8B",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.7,
        streaming=True
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是{name}，你喜欢小狗，小狗叫小黑。请用{style}风格回答用户问题。"),
        ("human", "{question}")
    ])

    chain = (
        # 1. 生成回答并保留原始输入字段
            RunnablePassthrough.assign(
                answer=prompt | llm | StrOutputParser()
            )
            # 2. 计算基础长度指标
            | RunnablePassthrough.assign(
                answer_length=lambda x: len(x["answer"]),
                first_ten_chars=lambda x: (
                    x["answer"][:10] + "..."
                    if len(x["answer"]) > 10
                    else x["answer"]
                )
            )
            # 3. 执行复杂统计分析
            | RunnableLambda(analyze_response)
            # 4. 组装结构化输出
            | RunnablePassthrough.assign(
                structured_output=lambda x: {
                    "user_info": {
                        "name": x["name"],
                        "style": x.get("style", "友好"),
                        "question": x["question"]
                    },
                    "response": {
                        "content": x["answer"],
                        "length": x["answer_length"],
                        "first_chars": x["first_ten_chars"]
                    },
                    "analysis": {
                        "char_count": x["char_count"],
                        "sentiment": x["sentiment"],
                        "quality": x["response_quality"],
                        "timestamp": x["analysis_timestamp"]
                    },
                    "has_chinese": x["has_chinese"]
                }
            )
            # 5. 序列化为 JSON 字符串
            | RunnablePassthrough.assign(
                json_output=lambda x: json.dumps(
                    x["structured_output"],
                    ensure_ascii=False,
                    indent=2
                )
            )
    )

    input_data = {
        "name": "小N",
        "question": "你是谁？你最喜欢什么？",
        "style": "活泼"
    }

    result = chain.invoke(input_data)
    print(result)


if __name__ == "__main__":
    main()