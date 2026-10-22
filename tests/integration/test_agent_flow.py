"""Agent 流程集成测试

需要真实 LLM，缺少 OPENAI_API_KEY 时自动跳过。
"""
import os

import pytest

from src.agent.intent import Intent
from src.agent.react_agent import ReactCustomerServiceAgent
from src.identifiers import normalize_order_id

pytestmark = pytest.mark.llm


@pytest.fixture(scope="module")
def agent():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY 未配置，跳过集成测试")
    return ReactCustomerServiceAgent()


class TestIntentRouting:
    """断言的不再是回复文本长什么样，而是轨迹对不对"""

    def test_product_query(self, agent):
        result = agent.invoke("iPhone 15 Pro Max 256GB 多少钱", user_id="case-product")
        assert result["intent"] == Intent.PRODUCT_QUERY
        assert result["context"]["tool"] == "query_product"
        assert result["retrieved_content"]

    def test_order_query(self, agent):
        result = agent.invoke("查一下订单 ORD2024001", user_id="case-order")
        assert result["intent"] == Intent.ORDER_QUERY
        assert result["context"]["tool"] == "query_order"
        assert "ORD2024001" in result["retrieved_content"]

    def test_logistics_query(self, agent):
        result = agent.invoke("ORD2024001 的快递到哪了", user_id="case-logistics")
        assert result["intent"] == Intent.LOGISTICS_QUERY
        assert result["context"]["tool"] == "query_logistics"

    def test_policy_query(self, agent):
        result = agent.invoke("能七天无理由吗", user_id="case-policy")
        assert result["intent"] == Intent.POLICY_QUERY
        assert result["context"]["tool"] == "search_policy"

    def test_complaint_falls_back(self, agent):
        result = agent.invoke("你们服务太差了，我要投诉", user_id="case-complaint")
        assert result["intent"] == Intent.FALLBACK
        assert result["context"]["tool"] == "handoff_to_human"
        assert result["context"]["fallback_reason"] == "handoff"

    def test_action_request_falls_back(self, agent):
        result = agent.invoke("帮我取消订单 ORD2024003", user_id="case-action")
        assert result["intent"] == Intent.FALLBACK
        assert result["context"]["tool"] == "handoff_to_human"


class TestParameterHandling:
    def test_missing_order_id_still_calls_the_tool(self, agent):
        """分类表规定一轮一意图，所以缺参数时也要产生 tool call"""
        result = agent.invoke("我的订单到哪了", user_id="case-missing-param")
        assert result["intent"] == Intent.ORDER_QUERY
        assert result["context"]["tool"] == "query_order"
        assert not normalize_order_id(result["context"]["params"]["order_id"]).startswith("ORD")
        assert "订单号" in result["messages"][-1].content

    def test_order_id_lands_in_the_right_parameter(self, agent):
        result = agent.invoke("帮我查一下 ORD2024001", user_id="case-param")
        assert result["context"]["params"]["order_id"] == "ORD2024001"


class TestMultiTurn:
    def test_product_context_carries_over(self, agent):
        agent.invoke("iPhone 15 Pro Max 256GB 多少钱", user_id="multi-turn")
        result = agent.invoke("这个还有货吗", user_id="multi-turn")

        assert result["intent"] == Intent.PRODUCT_QUERY
        assert result["context"]["tool"] == "query_product"
        assert "SKU-IPHONE-15-PROMAX-256" in result["retrieved_content"]
