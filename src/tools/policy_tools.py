"""政策查询工具"""

from src.data.policy_data import POLICY_DATA


def query_policy(query: str) -> str:
    """查询政策"""
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


def get_all_policies() -> list[dict]:
    """获取所有政策"""
    return [
        {"key": k, "title": v["title"]}
        for k, v in POLICY_DATA.items()
    ]
