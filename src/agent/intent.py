"""意图体系

分类表只在这一处落地："意图 → 工具 → 参数名"三者的对应关系由 TOOL_ROUTES
一张表决定，运行时与测试共用同一份定义。

意图不是单独分类出来的，而是从 ReAct 循环里实际发出的 function call 反查得到，
因此"记录的意图"和"执行的工具"永远一致。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langchain_core.messages import BaseMessage


class Intent(str, Enum):
    """用户意图枚举"""

    PRODUCT_QUERY = "product_query"
    ORDER_QUERY = "order_query"
    LOGISTICS_QUERY = "logistics_query"
    POLICY_QUERY = "policy_query"
    FALLBACK = "fallback"


# 工具名 -> (意图, 参数名)
TOOL_ROUTES: dict[str, tuple[Intent, str]] = {
    "query_product": (Intent.PRODUCT_QUERY, "sku_id"),
    "query_order": (Intent.ORDER_QUERY, "order_id"),
    "query_logistics": (Intent.LOGISTICS_QUERY, "order_id"),
    "search_policy": (Intent.POLICY_QUERY, "query"),
    "handoff_to_human": (Intent.FALLBACK, "reason"),
}

# 兜底的两种成因，用 context["fallback_reason"] 区分
FALLBACK_NO_TOOL_CALL = "no_tool_call"
FALLBACK_HANDOFF = "handoff"


@dataclass
class ToolCallRecord:
    """一次函数调用的完整记录"""

    name: str
    args: dict[str, Any]
    intent: Intent
    param_name: str
    result_text: str = ""


@dataclass
class IntentResult:
    """一轮对话的意图判定结果"""

    intent: Intent
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    primary_tool: str | None = None
    fallback_reason: str | None = None

    @property
    def primary(self) -> ToolCallRecord | None:
        """首个函数调用，即本轮的主工具"""
        return self.tool_calls[0] if self.tool_calls else None

    @property
    def extra_tools(self) -> list[str]:
        """主工具之外的其余工具名"""
        return [record.name for record in self.tool_calls[1:]]


def extract_intent(messages: list[BaseMessage]) -> IntentResult:
    """从 agent 返回的消息历史里反查意图

    规则：
    - 有 function call → 意图取第一个调用的工具对应的意图
    - 一个工具都没调 → 兜底，成因是 no_tool_call
    - 调了 handoff_to_human → 兜底，成因是 handoff
    """
    observations = _collect_observations(messages)
    records: list[ToolCallRecord] = []

    for message in messages:
        for tool_call in getattr(message, "tool_calls", None) or []:
            name = tool_call.get("name", "")
            route = TOOL_ROUTES.get(name)
            if route is None:
                continue
            intent, param_name = route
            records.append(
                ToolCallRecord(
                    name=name,
                    args=dict(tool_call.get("args") or {}),
                    intent=intent,
                    param_name=param_name,
                    result_text=observations.get(tool_call.get("id", ""), ""),
                )
            )

    if not records:
        return IntentResult(
            intent=Intent.FALLBACK,
            tool_calls=[],
            primary_tool=None,
            fallback_reason=FALLBACK_NO_TOOL_CALL,
        )

    primary = records[0]
    fallback_reason = FALLBACK_HANDOFF if primary.name == "handoff_to_human" else None
    return IntentResult(
        intent=primary.intent,
        tool_calls=records,
        primary_tool=primary.name,
        fallback_reason=fallback_reason,
    )


def _collect_observations(messages: list[BaseMessage]) -> dict[str, str]:
    """按 tool_call_id 收集工具返回内容"""
    observations: dict[str, str] = {}
    for message in messages:
        tool_call_id = getattr(message, "tool_call_id", None)
        if not tool_call_id:
            continue
        content = getattr(message, "content", "")
        observations[tool_call_id] = content if isinstance(content, str) else str(content)
    return observations
