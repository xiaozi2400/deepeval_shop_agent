"""政策查询工具"""
from langchain_core.tools import tool

from src.data.policy_data import POLICY_DATA


@tool
def query_policy(query: str) -> str:
    """查询电商平台政策，包括配送、退换货、支付、会员政策。

    Args:
        query: 用户查询关键词，如"配送政策"、"退货政策"等

    Returns:
        相关政策内容
    """
    query_lower = query.lower()

    keyword_map = {
        "shipping": ["配送", "发货", "送到", "物流"],
        "return": ["退货", "换货", "退款", "退换"],
        "payment": ["支付", "付款", "退款"],
        "membership": ["会员", "积分", "折扣", "等级"]
    }

    for policy_key, keywords in keyword_map.items():
        if any(kw in query_lower for kw in keywords):
            policy = POLICY_DATA[policy_key]
            return f"【{policy['title']}】\n{policy['content']}"

    return "抱歉，暂未找到相关政策信息。您可以尝试咨询：配送政策、退换货政策、支付政策或会员政策。"


@tool
def get_all_policies() -> str:
    """获取所有政策列表。

    Returns:
        所有政策标题列表
    """
    if not POLICY_DATA:
        return "暂无政策记录"

    result = []
    for key, policy in POLICY_DATA.items():
        result.append(f"- {policy['title']}（{key}）")

    return "可用政策列表：\n" + "\n".join(result)
