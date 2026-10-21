"""Agent Flow Integration Tests"""
import pytest

from src.agent.customer_service_agent import CustomerServiceAgent


class TestAgentFlow:
    @pytest.fixture
    def agent(self):
        return CustomerServiceAgent()

    def test_greeting(self, agent):
        result = agent.invoke("Hello")
        assert result["intent"].value == "greeting"
        assert len(result["messages"]) == 2

    def test_goodbye(self, agent):
        result = agent.invoke("Bye")
        assert result["intent"].value == "goodbye"

    def test_order_query_with_id(self, agent):
        result = agent.invoke("查一下订单ORD2024001")
        assert result["intent"].value == "order_query"
        assert "ORD2024001" in result["messages"][-1].content

    def test_order_query_shipped_status(self, agent):
        result = agent.invoke("ORD2024001发货没")
        assert result["intent"].value == "order_query"

    def test_order_query_delivered(self, agent):
        result = agent.invoke("订单ORD2024002收到没")
        assert result["intent"].value == "order_query"
        assert "已签收" in result["messages"][-1].content

    def test_return_request(self, agent):
        result = agent.invoke("退货订单ORD2024003")
        assert result["intent"].value == "return_exchange"
        assert "退货" in result["messages"][-1].content or "退款" in result["messages"][-1].content

    def test_exchange_request(self, agent):
        result = agent.invoke("换货ORD2024001")
        assert result["intent"].value == "return_exchange"
        assert "换货" in result["messages"][-1].content or "申请" in result["messages"][-1].content

    def test_shipping_policy_query(self, agent):
        result = agent.invoke("配送政策是什么")
        assert result["intent"].value == "policy_query"
        assert "发货" in result["messages"][-1].content

    def test_return_policy_query(self, agent):
        result = agent.invoke("退货政策")
        assert result["intent"].value == "policy_query"

    def test_faq_shipping_cost(self, agent):
        result = agent.invoke("运费如何计算")
        assert result["intent"].value == "faq"

    def test_faq_payment_methods(self, agent):
        result = agent.invoke("支持哪些支付方式")
        assert result["intent"].value == "faq"
        assert "支付宝" in result["messages"][-1].content or "微信" in result["messages"][-1].content

    def test_faq_contact_service(self, agent):
        result = agent.invoke("如何联系人工客服")
        assert result["intent"].value == "faq"
        assert "400" in result["messages"][-1].content or "在线咨询" in result["messages"][-1].content

    def test_membership_policy(self, agent):
        result = agent.invoke("会员政策是什么")
        assert result["intent"].value == "policy_query"

    def test_full_conversation_flow(self, agent):
        result1 = agent.invoke("你好")
        assert result1["intent"].value == "greeting"

        result2 = agent.invoke("帮我查订单ORD2024001")
        assert result2["intent"].value == "order_query"

        result3 = agent.invoke("退货政策")
        assert result3["intent"].value == "policy_query"

        result4 = agent.invoke("谢谢再见")
        assert result4["intent"].value == "goodbye"


class TestResponseMode:
    """测试响应模式和新字段"""

    @pytest.fixture
    def agent_rule(self):
        """纯规则模式Agent"""
        return CustomerServiceAgent(use_llm_routing=False, use_llm_response=False)

    @pytest.fixture
    def agent_llm(self):
        """LLM模式Agent（如果可用）"""
        try:
            return CustomerServiceAgent(use_llm_routing=True, use_llm_response=True)
        except ValueError:
            pytest.skip("LLM not configured")

    def test_faq_response_mode_rule(self, agent_rule):
        """FAQ节点规则模式"""
        result = agent_rule.invoke("运费如何计算")
        assert result["response_mode"] == "rule"
        assert result["retrieved_content"] is not None

    def test_order_response_mode_rule(self, agent_rule):
        """订单节点规则模式"""
        result = agent_rule.invoke("查一下订单ORD2024001")
        assert result["response_mode"] == "rule"
        assert result["retrieved_content"] is not None
        assert "ORD2024001" in result["retrieved_content"]

    def test_policy_response_mode_rule(self, agent_rule):
        """政策节点规则模式"""
        result = agent_rule.invoke("配送政策是什么")
        assert result["response_mode"] == "rule"
        assert result["retrieved_content"] is not None

    def test_return_response_mode_rule(self, agent_rule):
        """退换货节点规则模式"""
        result = agent_rule.invoke("退货订单ORD2024003")
        assert result["response_mode"] == "rule"
        assert result["return_request"] is not None

    def test_greeting_no_retrieved_content(self, agent_rule):
        """问候节点无retrieved_content"""
        result = agent_rule.invoke("你好")
        assert result["retrieved_content"] is None
        assert result["response_mode"] == "rule"

    def test_faq_response_mode_llm(self, agent_llm):
        """FAQ节点LLM模式"""
        result = agent_llm.invoke("运费如何计算")
        assert result["response_mode"] == "llm"
        assert result["retrieved_content"] is not None

    def test_order_response_mode_llm(self, agent_llm):
        """订单节点LLM模式"""
        result = agent_llm.invoke("查一下订单ORD2024001")
        assert result["response_mode"] == "llm"
        assert result["retrieved_content"] is not None
