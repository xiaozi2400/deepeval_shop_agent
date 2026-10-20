"""FAQ检索工具"""

from src.data.faq_data import FAQ_DATA


def search_faq(query: str) -> str:
    """关键词匹配FAQ"""
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


def get_all_faqs() -> list[dict]:
    """获取所有FAQ"""
    return FAQ_DATA
