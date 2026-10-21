import pytest
# 从 deepeval.metrics 导入 评估指标和测试用例
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

# 从项目导入Agent
from src.agent.customer_service_agent import CustomerServiceAgent

@pytest.fixture
def agent():
    """提供一个CustomerServiceAgent实例用于测试"""
    return CustomerServiceAgent()

def test_first_deepeval_shipping_cost(agent):
    """测试运费查询的答案相关性"""
  
    # 第一步：调用Agent处理用户输入
    result = agent.invoke("包邮吗")
    response = result["messages"][-1].content # 获取Agent的最后一条消息内容

    # 第二步：创建一个LLM测试用例
    test_case = LLMTestCase(
        input="包邮吗",      # 用户输入
        actual_output=response  # Agent的实际输出
    )

    # 第三步：创建评估指标
    metric = AnswerRelevancyMetric(
        threshold=0.5, 
        model="MiniMax-M3.1-Flash-Preview",
        # async_mode=False
    )

    # 第四步：使用评估指标对测试用例进行测量
    metric.measure(test_case)

    # 第五步：输出评估结果
    print(f"\n用户问题: {test_case.input}")
    print(f"Agent回答: {test_case.actual_output}")
    print(f"评估分数: {metric.score}")
    if hasattr(metric, 'reason'):
        print(f"Reason: {metric.reason}")

    # 第六步：断言评估得分是否达到阈值
    assert metric.score >= metric.threshold, f"答案相关性得分过低: {metric.score}"