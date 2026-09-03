"""
章节 03：LCEL 链式组合 —— 一次调用做多步处理并输出结构化结果
================================================
【本章学什么】
1. LCEL（LangChain Expression Language）：用 | 管道符把多个"组件"串成一条处理链
2. RunnablePassthrough：既"透传"原始输入，又能往数据里"塞"新字段（用 assign）
3. RunnableLambda：把任意 Python 函数包装成处理链里的一环
4. 整条链最终产出：原始回答 + 长度统计 + 情感分析 + 结构化 JSON 字符串

【术语速记】
- RunnablePassthrough.assign(新字段=表达式)：保留旧字段，并新增/覆盖字段
- RunnableLambda(函数)：把普通函数放进链里；函数吃一个 dict、吐一个 dict
- | ：管道符，前一步的返回结果自动成为下一步的输入

【运行前】同目录需有 .env；依赖：pip install langchain-openai langchain-core python-dotenv
"""
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
    """自定义分析函数：拿到前面传过来的 dict（其中含 answer），再补充几个统计字段"""
    answer = data.get("answer", "")
    char_count = len(answer)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in answer)  # 回答中是否含中文

    # 简易情感词典（生产环境建议替换为 LLM 判定或专业 NLP 库）
    positive_words = ["优秀", "棒", "爱", "开心", "高兴", "喜欢"]
    negative_words = ["差", "不好", "糟糕", "讨厌", "难过", "不喜欢"]

    sentiment = "中性"
    if any(word in answer for word in positive_words):
        sentiment = "正面"
    elif any(word in answer for word in negative_words):
        sentiment = "负面"

    # **data 表示"把之前所有字段原样保留"，再追加新的统计字段
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

    # 整条链 = 一串用 | 连接的步骤，数据从前往后流动
    chain = (
        # 步骤1：调用模型得到回答，并保留原始输入字段（name/style/question）
            RunnablePassthrough.assign(
                answer=prompt | llm | StrOutputParser()
            )
            # 步骤2：基于已有字段，算出回答长度和开头10个字
            | RunnablePassthrough.assign(
                answer_length=lambda x: len(x["answer"]),
                first_ten_chars=lambda x: (
                    x["answer"][:10] + "..."
                    if len(x["answer"]) > 10
                    else x["answer"]
                )
            )
            # 步骤3：调用自定义分析函数，往 dict 里新增情感/长度等字段
            | RunnableLambda(analyze_response)
            # 步骤4：把散落的字段"组装"成一个结构化字典，方便后续使用
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
            # 步骤5：把结构化对象转成带缩进的 JSON 字符串，方便人读
            | RunnablePassthrough.assign(
                json_output=lambda x: json.dumps(
                    x["structured_output"],
                    ensure_ascii=False,
                    indent=2
                )
            )
    )

    # 喂给链的输入：模板里用到的 name/question/style 都要给
    input_data = {
        "name": "小N",
        "question": "你是谁？你最喜欢什么？",
        "style": "活泼"
    }

    result = chain.invoke(input_data)
    print(result)   # 结果里的 json_output 字段就是格式化好的 JSON 字符串


if __name__ == "__main__":
    main()
