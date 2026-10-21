"""LangChain ReAct 架构的电商客服 Agent"""
import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agent.state import CustomerServiceState
from src.database.connection import init_db

load_dotenv()


# 工具列表
def get_tools():
    """获取所有工具"""
    from src.tools.faq_tools import search_faq, get_all_faqs
    from src.tools.order_tools import query_order, cancel_order, get_valid_order_ids, get_all_orders
    from src.tools.policy_tools import query_policy, get_all_policies
    from src.tools.return_tools import process_return_request, check_return_status, validate_return_eligibility

    return [
        search_faq,
        get_all_faqs,
        query_order,
        cancel_order,
        get_valid_order_ids,
        get_all_orders,
        query_policy,
        get_all_policies,
        process_return_request,
        check_return_status,
        validate_return_eligibility,
    ]


# 系统提示词
SYSTEM_PROMPT = """你是一个电商客服助手。你的目标是帮助用户解答问题、处理订单查询、退换货申请和政策咨询。

你可以通过以下工具来帮助用户：
- search_faq: 搜索FAQ知识库回答常见问题
- query_order: 查询订单详细信息
- cancel_order: 取消未发货的订单
- get_all_orders: 获取用户所有订单
- query_policy: 查询平台政策（配送、退换货、支付、会员）
- process_return_request: 处理退换货申请
- check_return_status: 查询退换货状态
- validate_return_eligibility: 验证退换货资格

请根据用户的问题，选择合适的工具来回答。如果需要用户提供更多信息，请友好地询问。

回复时使用友好、专业的语气。"""


class ReactCustomerServiceAgent:
    """基于 LangChain ReAct 架构的客服 Agent"""

    def __init__(
        self,
        model_provider: Literal["openai", "anthropic"] = "openai",
        model_name: str = None,
        temperature: float = 0,
    ):
        """
        初始化 ReAct Agent

        Args:
            model_provider: 模型提供商 ("openai" 或 "anthropic")
            model_name: 模型名称，默认根据 provider 使用合适的模型
            temperature: 模型温度参数
        """
        self.model_provider = model_provider
        self.temperature = temperature

        # 设置默认模型
        if model_name is None:
            model_name = os.getenv("MODEL_NAME")
        # 初始化 LLM
        self._init_llm(model_provider, model_name)

        # 获取工具列表
        self.tools = get_tools()

        # 初始化数据库
        init_db()

        # 构建 Agent
        self._build_agent()

    def _init_llm(self, provider: str, model_name: str):
        """初始化 LLM"""
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")

            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=self.temperature
            )
        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    def _build_agent(self):
        """构建 ReAct Agent"""
        from langchain.agents import create_agent

        # 使用 langchain 1.x 的 create_agent
        self.agent = create_agent(
            self.llm,
            self.tools,
            system_prompt=SYSTEM_PROMPT
        )

    def invoke(
        self,
        user_message: str,
        user_id: str | None = None,
    ) -> CustomerServiceState:
        """
        处理用户消息

        Args:
            user_message: 用户输入消息
            user_id: 用户ID（可选）

        Returns:
            Agent 执行结果
        """
        # 构建输入
        input_messages = [HumanMessage(content=user_message)]

        # 执行 Agent
        result = self.agent.invoke({"messages": input_messages})

        # 提取最终响应
        messages = result.get("messages", [])
        final_message = messages[-1] if messages else None

        return {
            "messages": [final_message] if final_message else [],
            "intent": None,
            "order_info": None,
            "return_request": None,
            "current_node": "react_agent",
            "next_node": "",
            "context": {},
            "user_id": user_id,
            "response_mode": "llm",
            "retrieved_content": None
        }

    def stream(
        self,
        user_message: str,
        user_id: str | None = None,
    ):
        """
        流式处理用户消息

        Args:
            user_message: 用户输入消息
            user_id: 用户ID（可选）

        Yields:
            Agent 执行过程中的输出
        """
        input_messages = [HumanMessage(content=user_message)]

        for event in self.agent.stream({"messages": input_messages}):
            yield event
