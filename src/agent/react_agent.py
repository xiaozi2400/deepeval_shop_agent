"""LangChain ReAct 架构的电商客服 Agent"""
import os
import uuid
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage

from src.agent.intent import IntentResult, extract_intent
from src.agent.llm_guard import GuardedChatOpenAI
from src.agent.state import CustomerServiceState
from src.database.connection import init_db
from src.prompts.system_prompts import AGENT_SYSTEM_PROMPT

load_dotenv()


# 工具列表
def get_tools():
    """获取工具列表：五个意图各对应一个工具"""
    from src.tools.handoff_tools import handoff_to_human
    from src.tools.logistics_tools import query_logistics
    from src.tools.order_tools import query_order
    from src.tools.policy_tools import search_policy
    from src.tools.product_tools import query_product

    return [
        query_product,
        query_order,
        query_logistics,
        search_policy,
        handoff_to_human,
    ]


class ReactCustomerServiceAgent:
    """基于 LangChain ReAct 架构的客服 Agent

    每一轮对话的意图由 ReAct 循环里实际发出的 function call 决定，
    再由 TOOL_ROUTES 反查得到，因此记录的意图与执行的工具永远一致。
    """

    def __init__(
        self,
        model_provider: Literal["openai", "anthropic"] = "openai",
        model_name: str | None = None,
        temperature: float = 0,
        llm=None,
    ):
        """
        初始化 ReAct Agent

        Args:
            model_provider: 模型提供商 ("openai" 或 "anthropic")
            model_name: 模型名称，默认取环境变量 MODEL_NAME
            temperature: 模型温度参数
            llm: 自定义模型实例，传入时不再从环境变量构造（测试用假模型注入）
        """
        self.model_provider = model_provider
        self.temperature = temperature

        if llm is not None:
            self.llm = llm
        else:
            if model_name is None:
                model_name = os.getenv("MODEL_NAME")
            self._init_llm(model_provider, model_name or None)

        self.tools = get_tools()

        init_db()

        self._build_agent()

    def _init_llm(self, provider: str, model_name: str | None):
        """初始化 LLM"""
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")

            # 环境变量为空字符串时按未配置处理。CI 里未配置的 secret 会被展开成
            # 空字符串而不是不设该变量，若原样传给 ChatOpenAI，base_url 会变成
            # 空 URL，所有请求直接失败。
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

            # GuardedChatOpenAI 会在上游返回业务错误时抛 UpstreamLLMError，
            # 而不是让流式响应带着空内容混过去。
            self.llm = GuardedChatOpenAI(
                model=model_name or "gpt-3.5-turbo",
                api_key=api_key,
                base_url=base_url or None,
                temperature=self.temperature
            )
        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    def _build_agent(self):
        """构建 ReAct Agent，挂上 checkpointer 以支持多轮对话"""
        from langchain.agents import create_agent
        from langgraph.checkpoint.memory import InMemorySaver

        self.checkpointer = InMemorySaver()
        self._default_thread_id = f"default-{uuid.uuid4()}"

        self.agent = create_agent(
            self.llm,
            self.tools,
            system_prompt=AGENT_SYSTEM_PROMPT,
            checkpointer=self.checkpointer,
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
            user_id: 用户ID，用作会话 thread_id，缺省时共用一个默认会话

        Returns:
            Agent 执行结果，含本轮意图、函数调用记录与工具返回内容
        """
        sent = HumanMessage(content=user_message, id=f"user-{uuid.uuid4()}")

        result = self.agent.invoke(
            {"messages": [sent]},
            config={"configurable": {"thread_id": user_id or self._default_thread_id}},
        )

        messages = list(result.get("messages", []))
        intent_result = extract_intent(self._current_turn(messages, sent.id))

        return self._build_state(messages, intent_result, user_id)

    def stream(
        self,
        user_message: str,
        user_id: str | None = None,
    ):
        """
        流式处理用户消息

        Args:
            user_message: 用户输入消息
            user_id: 用户ID，用作会话 thread_id

        Yields:
            助手回复的文本片段
        """
        sent = HumanMessage(content=user_message, id=f"user-{uuid.uuid4()}")

        current_id = None
        buffer: list[str] = []
        has_tool_call = False

        for chunk in self.agent.stream(
            {"messages": [sent]},
            config={"configurable": {"thread_id": user_id or self._default_thread_id}},
            stream_mode="messages",
        ):
            message = chunk[0] if isinstance(chunk, tuple) else chunk
            if not isinstance(message, AIMessageChunk):
                continue

            if message.id != current_id:
                # 上一条模型消息已完整：带工具调用的那一轮是过程语，不进正文
                if buffer and not has_tool_call:
                    yield "".join(buffer)
                current_id = message.id
                buffer = []
                has_tool_call = False

            if message.tool_calls:
                has_tool_call = True
            content = getattr(message, "content", "")
            if isinstance(content, str) and content:
                buffer.append(content)

        if buffer and not has_tool_call:
            yield "".join(buffer)

    def _current_turn(self, messages: list[BaseMessage], sent_id: str) -> list[BaseMessage]:
        """截取本轮产生的消息，排除历史轮次

        checkpointer 会把整个会话历史都放进结果里，
        而意图只应依据本轮发出的 function call 判定。
        """
        for index, message in enumerate(messages):
            if getattr(message, "id", None) == sent_id:
                return messages[index + 1:]
        return []

    def _build_state(
        self,
        messages: list[BaseMessage],
        intent_result: IntentResult,
        user_id: str | None,
    ) -> CustomerServiceState:
        """把执行结果整理成对外的状态"""
        observations = [r.result_text for r in intent_result.tool_calls if r.result_text]
        retrieved_content = "\n\n".join(observations) if observations else None

        context: dict = {}
        if intent_result.primary_tool:
            context["tool"] = intent_result.primary_tool
        primary = intent_result.primary
        if primary is not None:
            context["params"] = primary.args
        if intent_result.extra_tools:
            context["extra_tools"] = intent_result.extra_tools
        if intent_result.fallback_reason:
            context["fallback_reason"] = intent_result.fallback_reason

        return {
            "messages": messages,
            "intent": intent_result.intent,
            "tool_calls": intent_result.tool_calls,
            "retrieved_content": retrieved_content,
            "context": context,
            "user_id": user_id,
        }
