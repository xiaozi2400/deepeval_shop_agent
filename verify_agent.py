"""快速验证脚本 - 验证Agent核心功能"""
import sys

sys.path.insert(0, '.')

from src.agent.customer_service_agent import CustomerServiceAgent
from src.agent.state import Intent


def test_agent():
    print("=" * 50)
    print("电商客服Agent 验证测试")
    print("=" * 50)

    agent = CustomerServiceAgent()

    test_cases = [
        ("你好", Intent.GREETING, "问候测试"),
        ("帮我查订单ORD2024001", Intent.ORDER_QUERY, "订单查询测试"),
        ("我要退货，订单ORD2024003", Intent.RETURN_EXCHANGE, "退货申请测试"),
        ("配送政策是什么", Intent.POLICY_QUERY, "政策查询测试"),
        ("运费怎么算", Intent.FAQ, "FAQ测试"),
        ("谢谢，再见", Intent.GOODBYE, "告别测试"),
    ]

    all_passed = True
    for i, (message, expected_intent, desc) in enumerate(test_cases, 1):
        try:
            result = agent.invoke(message)
            actual_intent = result["intent"]
            passed = actual_intent == expected_intent
            status = "[PASS]" if passed else "[FAIL]"
            print(f"\n{status} {desc} ({i}/{len(test_cases)})")
            print(f"  输入: {message}")
            print(f"  预期: {expected_intent.value}")
            print(f"  实际: {actual_intent.value if actual_intent else 'None'}")
            print(f"  响应: {result['messages'][-1].content[:50]}...")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n[FAIL] {desc} - Error: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed, please check.")
    print("=" * 50)

if __name__ == "__main__":
    test_agent()
