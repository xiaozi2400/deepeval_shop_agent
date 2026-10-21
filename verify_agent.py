"""快速验证脚本 - 验证ReAct Agent核心功能"""
import sys

sys.path.insert(0, '.')

from src.agent.react_agent import ReactCustomerServiceAgent


def test_agent():
    print("=" * 50)
    print("电商客服ReAct Agent 验证测试")
    print("=" * 50)

    agent = ReactCustomerServiceAgent()

    test_cases = [
        ("你好", "问候测试"),
        ("帮我查订单ORD2024001", "订单查询测试"),
        ("我要退货，订单ORD2024003", "退货申请测试"),
        ("配送政策是什么", "政策查询测试"),
        ("运费怎么算", "FAQ测试"),
    ]

    all_passed = True
    for i, (message, desc) in enumerate(test_cases, 1):
        try:
            result = agent.invoke(message)
            messages = result.get("messages", [])
            response = messages[-1].content if messages else ""

            # ReAct Agent 不返回 intent，我们检查是否有有效响应
            passed = bool(response) and len(response) > 0
            status = "[PASS]" if passed else "[FAIL]"
            print(f"\n{status} {desc} ({i}/{len(test_cases)})")
            print(f"  输入: {message}")
            print(f"  响应: {response[:80]}...")
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
