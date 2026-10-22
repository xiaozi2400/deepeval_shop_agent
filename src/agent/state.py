"""状态管理"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypedDict

from src.agent.intent import Intent, ToolCallRecord


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderInfo:
    """订单信息"""
    order_id: str
    status: OrderStatus
    items: list[str]
    total_amount: float
    shipping_address: str
    created_at: datetime


class CustomerServiceState(TypedDict, total=False):
    """一轮对话结束后返回给调用方的状态"""
    messages: list                     # 完整对话历史 + 本轮回复
    intent: Intent | None              # 本轮判定的意图
    tool_calls: list[ToolCallRecord]   # 本轮发生的函数调用
    retrieved_content: str | None      # 工具返回内容，DeepEval context 的来源
    context: dict                      # 工具名、参数、兜底成因等
    user_id: str | None
