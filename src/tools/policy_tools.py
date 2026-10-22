"""政策查询工具"""
from langchain_core.tools import tool

from src.data.knowledge_data import KNOWLEDGE_DATA
from src.schemas import PolicyResult


@tool
def search_policy(query: str) -> PolicyResult:
    """查询平台政策与常见规则。

    覆盖配送政策、退换货政策（含七天无理由）、支付政策、会员政策，
    以及运费、积分、修改地址、货到付款、查看物流等常见规则。

    Args:
        query: 用户的问题原文或关键词，例如"能七天无理由吗""运费怎么算"。

    Returns:
        命中的政策条目内容；未命中任何条目时 found 为 False。
    """
    text = (query or "").strip()
    if not text:
        return PolicyResult(
            found=False,
            needs_input=True,
            message="需要知道用户想了解哪方面的政策，请补充问题内容。",
        )

    scored = []
    for entry in KNOWLEDGE_DATA:
        score = sum(1 for kw in entry["keywords"] if kw in text)
        if entry["title"] in text:
            score += 2
        if score > 0:
            scored.append((score, entry))

    if not scored:
        return PolicyResult(
            found=False,
            message="未找到匹配的政策条目。平台可咨询的方向有：配送政策、退换货政策、"
                    "支付政策、会员政策，以及运费、积分、货到付款等常见规则。",
        )

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best = scored[0][1]
    others = [entry for score, entry in scored[1:] if score >= scored[0][0]]

    sections = [f"【{entry['title']}】\n{entry['content']}" for entry in others]
    return PolicyResult(
        found=True,
        title=best["title"],
        content=best["content"],
        sections=sections,
    )
