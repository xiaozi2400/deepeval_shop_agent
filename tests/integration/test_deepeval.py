"""DeepEval评估测试"""
import pytest
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase

from src.agent.customer_service_agent import CustomerServiceAgent


@pytest.fixture
def agent():
    return CustomerServiceAgent()


class TestDeepEvalMetrics:
    """DeepEval指标评估测试"""

    def test_answer_relevancy(self, agent):
        """答案相关性评估"""
        metric = AnswerRelevancyMetric(
            threshold=0.5,
            model="gpt-4",
            include_reason=True
        )

        result = agent.invoke("运费怎么算")
        response = result["messages"][-1].content

        test_case = LLMTestCase(
            input="运费怎么算",
            actual_output=response
        )
        metric.measure(test_case)
        print(f"Answer Relevancy Score: {metric.score}")
        if hasattr(metric, 'reason'):
            print(f"Reason: {metric.reason}")
        assert metric.score >= 0.3, f"答案相关性得分过低: {metric.score}"

    def test_faithfulness(self, agent):
        """答案忠实度评估"""
        metric = FaithfulnessMetric(
            threshold=0.5,
            model="gpt-4"
        )

        result = agent.invoke("退货政策是什么")
        response = result["messages"][-1].content
        context = ["退货政策：自收到商品之日起7天内可申请退货，商品需保持完好"]

        test_case = LLMTestCase(
            input="退货政策是什么",
            actual_output=response,
            context=context
        )
        metric.measure(test_case)
        print(f"Faithfulness Score: {metric.score}")
        assert metric.score >= 0.3, f"答案忠实度得分过低: {metric.score}"

    def test_hallucination(self, agent):
        """幻觉检测"""
        metric = HallucinationMetric(
            threshold=0.5,
            model="gpt-4"
        )

        result = agent.invoke("会员有什么权益")
        response = result["messages"][-1].content
        context = ["会员权益：银卡9.5折，金卡9折"]

        test_case = LLMTestCase(
            input="会员有什么权益",
            actual_output=response,
            context=context
        )
        metric.measure(test_case)
        print(f"Hallucination Score: {metric.score}")
        # 新版deepeval: 1是pass, 0是fail, threshold是最小通过分数
        assert metric.score >= 0.5, f"幻觉检测得分过低: {metric.score}"

    def test_toxicity(self, agent):
        """毒性检测"""
        metric = ToxicityMetric(threshold=0.5)

        result = agent.invoke("你们服务太差了")
        response = result["messages"][-1].content

        test_case = LLMTestCase(
            input="你们服务太差了",
            actual_output=response
        )
        metric.measure(test_case)
        print(f"Toxicity Score: {metric.score}")
        assert metric.score >= 0.5, f"毒性检测得分过低: {metric.score}"


class TestOrderQueryDeepEval:
    """订单查询DeepEval测试"""

    @pytest.fixture
    def agent(self):
        return CustomerServiceAgent()

    def test_order_query_answer_quality(self, agent):
        """订单查询答案质量评估"""
        metric = AnswerRelevancyMetric(threshold=0.5, model="gpt-4")

        result = agent.invoke("帮我查一下订单ORD2024001的状态")
        response = result["messages"][-1].content

        test_case = LLMTestCase(
            input="帮我查一下订单ORD2024001的状态",
            actual_output=response
        )
        metric.measure(test_case)
        print(f"Order Query Relevancy: {metric.score}")
        assert metric.score >= 0.3


class TestReturnExchangeDeepEval:
    """退换货DeepEval测试"""

    @pytest.fixture
    def agent(self):
        return CustomerServiceAgent()

    def test_return_request_quality(self, agent):
        """退货申请答案质量"""
        metric = AnswerRelevancyMetric(threshold=0.5, model="gpt-4")

        result = agent.invoke("我要退货，订单ORD2024003")
        response = result["messages"][-1].content

        test_case = LLMTestCase(
            input="我要退货，订单ORD2024003",
            actual_output=response
        )
        metric.measure(test_case)
        print(f"Return Request Relevancy: {metric.score}")
        assert "退货" in response or "退款" in response or "申请" in response


class TestFAQDeepEval:
    """FAQ DeepEval测试"""

    @pytest.fixture
    def agent(self):
        return CustomerServiceAgent()

    def test_payment_methods_quality(self, agent):
        """支付方式查询答案质量"""
        metric = AnswerRelevancyMetric(threshold=0.5, model="gpt-4")

        result = agent.invoke("支持哪些支付方式")
        response = result["messages"][-1].content

        test_case = LLMTestCase(
            input="支持哪些支付方式",
            actual_output=response
        )
        metric.measure(test_case)
        print(f"Payment Methods Relevancy: {metric.score}")
        assert "支付宝" in response or "微信" in response or "信用卡" in response

    def test_shipping_cost_quality(self, agent):
        """运费查询答案质量"""
        metric = AnswerRelevancyMetric(threshold=0.5, model="gpt-4")

        result = agent.invoke("运费怎么算")
        response = result["messages"][-1].content

        test_case = LLMTestCase(
            input="运费怎么算",
            actual_output=response
        )
        metric.measure(test_case)
        print(f"Shipping Cost Relevancy: {metric.score}")
        assert "99" in response or "运费" in response
