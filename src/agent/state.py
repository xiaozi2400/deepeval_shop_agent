"""状态管理"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, TypedDict

from langgraph.graph import add_messages


class Intent(Enum):
    """用户意图枚举"""
    GREETING = "greeting"
    ORDER_QUERY = "order_query"
    RETURN_EXCHANGE = "return_exchange"
    POLICY_QUERY = "policy_query"
    FAQ = "faq"
    FALLBACK = "fallback"
    GOODBYE = "goodbye"


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


@dataclass
class ReturnRequest:
    """退换货请求"""
    order_id: str
    reason: str
    request_type: str
    status: str = "pending"


class CustomerServiceState(TypedDict, total=False):
    """LangGraph共享状态"""
    messages: Annotated[list, add_messages]
    intent: Intent | None
    order_info: OrderInfo | None
    return_request: ReturnRequest | None
    current_node: str
    next_node: str
    context: dict
    user_id: str | None
    # 新增字段
    response_mode: Literal["rule", "llm"] | None  # 响应模式
    retrieved_content: str | None                  # 检索到的内容
