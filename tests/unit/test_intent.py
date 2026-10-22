"""意图体系单元测试"""
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agent.intent import (
    FALLBACK_HANDOFF,
    FALLBACK_NO_TOOL_CALL,
    TOOL_ROUTES,
    Intent,
    extract_intent,
)


def tool_call_ai(name: str, args: dict, call_id: str = "c1") -> AIMessage:
    """构造一条带 function call 的助手消息"""
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


class TestRoutes:
    def test_exactly_five_tools(self):
        assert set(TOOL_ROUTES) == {
            "query_product",
            "query_order",
            "query_logistics",
            "search_policy",
            "handoff_to_human",
        }

    def test_route_mapping(self):
        assert TOOL_ROUTES["query_product"] == (Intent.PRODUCT_QUERY, "sku_id")
        assert TOOL_ROUTES["query_order"] == (Intent.ORDER_QUERY, "order_id")
        assert TOOL_ROUTES["query_logistics"] == (Intent.LOGISTICS_QUERY, "order_id")
        assert TOOL_ROUTES["search_policy"] == (Intent.POLICY_QUERY, "query")
        assert TOOL_ROUTES["handoff_to_human"] == (Intent.FALLBACK, "reason")


class TestExtractIntent:
    def test_single_tool_call(self):
        messages = [
            HumanMessage(content="查一下订单"),
            tool_call_ai("query_order", {"order_id": "ORD2024001"}),
            ToolMessage(content="订单已发货", tool_call_id="c1"),
        ]
        result = extract_intent(messages)

        assert result.intent == Intent.ORDER_QUERY
        assert result.primary_tool == "query_order"
        assert result.primary.args == {"order_id": "ORD2024001"}
        assert result.primary.result_text == "订单已发货"
        assert result.fallback_reason is None

    def test_multiple_tool_calls_keep_primary(self):
        messages = [
            tool_call_ai("query_order", {"order_id": "ORD2024001"}, "c1"),
            ToolMessage(content="订单已发货", tool_call_id="c1"),
            tool_call_ai("query_logistics", {"order_id": "ORD2024001"}, "c2"),
            ToolMessage(content="运输中", tool_call_id="c2"),
        ]
        result = extract_intent(messages)

        assert result.intent == Intent.ORDER_QUERY
        assert result.primary_tool == "query_order"
        assert result.extra_tools == ["query_logistics"]
        assert len(result.tool_calls) == 2

    def test_handoff_is_fallback(self):
        messages = [
            tool_call_ai("handoff_to_human", {"reason": "投诉"}, "c1"),
            ToolMessage(content="已转人工", tool_call_id="c1"),
        ]
        result = extract_intent(messages)

        assert result.intent == Intent.FALLBACK
        assert result.fallback_reason == FALLBACK_HANDOFF

    def test_no_tool_call_is_fallback(self):
        result = extract_intent([HumanMessage(content="你好")])

        assert result.intent == Intent.FALLBACK
        assert result.fallback_reason == FALLBACK_NO_TOOL_CALL
        assert result.tool_calls == []
        assert result.primary_tool is None

    def test_unknown_tool_is_ignored(self):
        messages = [tool_call_ai("some_other_tool", {})]
        result = extract_intent(messages)

        assert result.intent == Intent.FALLBACK
        assert result.fallback_reason == FALLBACK_NO_TOOL_CALL


class TestAgentTrajectory:
    """用假模型驱动真实的 ReAct 循环，验证意图回读不依赖真实 LLM"""

    def test_tool_call_drives_intent_and_context(self, fake_llm):
        from src.agent.react_agent import ReactCustomerServiceAgent

        llm = fake_llm(responses=[
            tool_call_ai("query_order", {"order_id": "ORD2024001"}),
            AIMessage(content="您的订单 ORD2024001 已发货。"),
        ])
        agent = ReactCustomerServiceAgent(llm=llm)
        result = agent.invoke("查一下 ORD2024001")

        assert result["intent"] == Intent.ORDER_QUERY
        assert result["context"]["tool"] == "query_order"
        assert result["context"]["params"] == {"order_id": "ORD2024001"}
        assert "已发货" in result["retrieved_content"]
        assert result["messages"][-1].content == "您的订单 ORD2024001 已发货。"

    def test_missing_param_still_produces_a_tool_call(self, fake_llm):
        from src.agent.react_agent import ReactCustomerServiceAgent

        llm = fake_llm(responses=[
            tool_call_ai("query_order", {"order_id": ""}),
            AIMessage(content="请提供您的订单号，格式如 ORD2024001。"),
        ])
        agent = ReactCustomerServiceAgent(llm=llm)
        result = agent.invoke("我的订单到哪了")

        assert result["intent"] == Intent.ORDER_QUERY
        assert result["context"]["tool"] == "query_order"
        assert "订单号" in result["retrieved_content"]

    def test_history_does_not_leak_into_current_turn(self, fake_llm):
        """第二轮的意图只依据本轮的 function call，不能被上一轮带偏"""
        from src.agent.react_agent import ReactCustomerServiceAgent

        llm = fake_llm(responses=[
            tool_call_ai("query_order", {"order_id": "ORD2024001"}),
            AIMessage(content="已发货。"),
            tool_call_ai("search_policy", {"query": "运费怎么算"}),
            AIMessage(content="满99元免运费。"),
        ])
        agent = ReactCustomerServiceAgent(llm=llm)
        agent.invoke("查一下 ORD2024001", user_id="u1")
        result = agent.invoke("运费怎么算", user_id="u1")

        assert result["intent"] == Intent.POLICY_QUERY
        assert result["context"]["tool"] == "search_policy"
