"""FAQ检索工具"""
from langchain_core.tools import tool

from src.data.faq_data import FAQ_DATA


@tool
def search_faq(query: str) -> str:
    """搜索FAQ知识库回答用户问题。

    Args:
        query: 用户问题文本

    Returns:
        匹配到的FAQ内容和答案
    """
    query_lower = query.lower()
    best_match = None
    best_score = 0

    for faq in FAQ_DATA:
        question_words = set(faq["question"].lower().split())
        query_words = set(query_lower.split())
        common_words = question_words & query_words

        if len(common_words) > best_score:
            best_score = len(common_words)
            best_match = faq

    if best_match and best_score > 0:
        return f"根据您的问题，为您找到以下信息：\n\nQ: {best_match['question']}\nA: {best_match['answer']}"

    return "抱歉，暂时没有找到与您问题相关的信息。请问您是否需要转人工客服？"


@tool
def get_all_faqs() -> str:
    """获取所有FAQ问题列表。

    Returns:
        所有FAQ问题的列表
    """
    if not FAQ_DATA:
        return "暂无FAQ记录"

    result = []
    for i, faq in enumerate(FAQ_DATA, 1):
        result.append(f"{i}. {faq['question']}")

    return "常见问题列表：\n" + "\n".join(result)
