"""五类意图端到端验证脚本

每条用例断言两件事：判出的 intent 与实际执行的主工具。
两者都从 ReAct 循环里真实的 function call 推导，不看回复文本长什么样。

用法：
    python verify_agent.py
"""
import sys

sys.path.insert(0, '.')

from src.agent.intent import Intent, TOOL_ROUTES
from src.agent.react_agent import ReactCustomerServiceAgent

CASES = [
    ("iPhone 15 Pro Max 256GB 多少钱", Intent.PRODUCT_QUERY, "query_product"),
    ("查一下订单 ORD2024001", Intent.ORDER_QUERY, "query_order"),
    ("ORD2024001 的快递到哪了", Intent.LOGISTICS_QUERY, "query_logistics"),
    ("能七天无理由吗", Intent.POLICY_QUERY, "search_policy"),
    ("你们服务太差了，我要投诉", Intent.FALLBACK, "handoff_to_human"),
]


def run():
    print("=" * 60)
    print("电商客服 ReAct Agent - 五类意图验证")
    print("=" * 60)

    agent = ReactCustomerServiceAgent()
    failures = []

    for index, (message, expected_intent, expected_tool) in enumerate(CASES, 1):
        result = agent.invoke(message, user_id=f"verify-{index}")
        actual_intent = result["intent"]
        actual_tool = result["context"].get("tool")
        reply = result["messages"][-1].content

        ok = actual_intent == expected_intent and actual_tool == expected_tool
        # 意图必须能从 TOOL_ROUTES 反查回同一批工具，路由表才是唯一事实来源
        route_ok = TOOL_ROUTES.get(actual_tool, (None,))[0] == actual_intent

        print(f"\n[{'PASS' if ok and route_ok else 'FAIL'}] {index}/{len(CASES)} {message}")
        print(f"  意图: {actual_intent.value} (期望 {expected_intent.value})")
        print(f"  工具: {actual_tool} (期望 {expected_tool})")
        print(f"  回复: {reply.splitlines()[0][:80]}")
        if not (ok and route_ok):
            failures.append((message, expected_intent, expected_tool, actual_intent, actual_tool))

    print("\n" + "=" * 60)
    if failures:
        print(f"{len(failures)} 条用例未通过：")
        for message, ei, et, ai, at in failures:
            print(f"  {message}: 期望 {ei.value}/{et}，实际 {ai.value}/{at}")
    else:
        print("全部用例通过")
    print("=" * 60)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
