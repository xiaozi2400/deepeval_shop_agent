"""电商客服Agent核心类"""
import os
from functools import partial

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    faq_node,
    goodbye_node,
    greeting_node,
    order_query_node,
    policy_query_node,
    return_exchange_node,
    routing_node,
)
from src.agent.state import CustomerServiceState

load_dotenv()


class CustomerServiceAgent:
    """电商客服Agent"""
    def __init__(self, use_llm_routing: bool = True, use_llm_response: bool = True):
        """
        初始化Agent

        Args:
            use_llm_routing: 是否使用LLM进行路由（需要配置API）
            use_llm_response: 是否使用LLM生成回答（需要配置API）
        """
        self.use_llm_routing = use_llm_routing
        self.use_llm_response = use_llm_response

        if use_llm_routing or use_llm_response:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            model_name = os.getenv("MODEL_NAME", "gpt-4o")

            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=0
            )
        else:
            self.llm = None

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建LangGraph"""
        builder = StateGraph(CustomerServiceState)

        # 使用partial将llm绑定到各节点
        routing_with_llm = partial(routing_node, llm=self.llm)
        faq_with_llm = partial(faq_node, llm=self.llm)
        policy_with_llm = partial(policy_query_node, llm=self.llm)
        order_with_llm = partial(order_query_node, llm=self.llm)
        return_with_llm = partial(return_exchange_node, llm=self.llm)

        # 添加节点
        builder.add_node("routing", routing_with_llm)
        builder.add_node("faq", faq_with_llm)
        builder.add_node("order_query", order_with_llm)
        builder.add_node("return_exchange", return_with_llm)
        builder.add_node("policy_query", policy_with_llm)
        builder.add_node("greeting", greeting_node)
        builder.add_node("goodbye", goodbye_node)

        # 设置入口点
        builder.add_edge(START, "routing")

        # 路由到各功能节点
        builder.add_conditional_edges(
            "routing",
            lambda x: x["next_node"],
            {
                "faq_node": "faq",
                "order_query_node": "order_query",
                "return_exchange_node": "return_exchange",
                "policy_query_node": "policy_query",
                "greeting_node": "greeting",
                "goodbye_node": "goodbye"
            }
        )

        # 所有功能节点结束到END
        for node in ["faq", "order_query", "return_exchange", "policy_query", "greeting", "goodbye"]:
            builder.add_edge(node, END)

        return builder.compile()

    def invoke(self, user_message: str, user_id: str | None = None) -> CustomerServiceState:
        """处理用户消息"""
        from langchain_core.messages import HumanMessage

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "intent": None,
            "order_info": None,
            "return_request": None,
            "current_node": "start",
            "next_node": "",
            "context": {},
            "user_id": user_id,
            "response_mode": None,
            "retrieved_content": None
        }
        return self.graph.invoke(initial_state)

    def stream(self, user_message: str, user_id: str | None = None):
        """流式处理"""
        from langchain_core.messages import HumanMessage

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "intent": None,
            "order_info": None,
            "return_request": None,
            "current_node": "start",
            "next_node": "",
            "context": {},
            "user_id": user_id,
            "response_mode": None,
            "retrieved_content": None
        }
        yield from self.graph.stream(initial_state)

    def route_with_llm(self, user_message: str) -> str:
        """
        使用LLM进行意图识别和路由

        Args:
            user_message: 用户消息

        Returns:
            下一节点名称
        """
        if not self.llm:
            raise ValueError("LLM not configured, set use_llm_routing=True")

        prompt = f"""你是一个电商客服意图分类器。请根据用户消息判断用户意图。

用户消息: {user_message}

可选意图:
- greeting_node: 用户在问候或打招呼
- order_query_node: 用户在查询订单状态
- return_exchange_node: 用户在申请退换货
- policy_query_node: 用户在询问政策（如配送政策、退换货政策、会员政策）
- faq_node: 用户在咨询常见问题（如运费、支付方式、联系客服）
- goodbye_node: 用户在说再见或结束对话

请只返回一个意图名称，不要其他内容。"""

        response = self.llm.invoke(prompt)
        intent = response.content.strip().lower()

        # 验证返回的意图是否有效
        valid_intents = ["greeting_node", "order_query_node", "return_exchange_node",
                         "policy_query_node", "faq_node", "goodbye_node"]

        if intent not in valid_intents:
            intent = "faq_node"

        return intent
