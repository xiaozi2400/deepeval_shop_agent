"""订单查询工具"""
from langchain_core.tools import tool

from src.agent.state import OrderStatus
from src.database.connection import get_session
from src.database.repositories.order_repository import SQLiteOrderRepository
from src.identifiers import normalize_order_id
from src.schemas import OrderResult

STATUS_TEXT = {
    OrderStatus.PENDING: "待发货",
    OrderStatus.SHIPPED: "已发货",
    OrderStatus.DELIVERED: "已签收",
    OrderStatus.CANCELLED: "已取消",
}


@tool
def query_order(order_id: str) -> OrderResult:
    """查询订单的详细信息。

    Args:
        order_id: 订单号，格式如 ORD2024001。传入整句用户输入也能从中解析出订单号。

    Returns:
        订单状态、商品、金额与收货地址；缺订单号时 needs_input 为 True，
        订单不存在时 found 为 False。
    """
    normalized = normalize_order_id(order_id)
    if not normalized:
        return OrderResult(
            found=False,
            needs_input=True,
            message="需要订单号才能查询。请向用户索要订单号，格式如 ORD2024001。",
        )

    with get_session() as session:
        repo = SQLiteOrderRepository(session)
        order = repo.get_by_id(normalized)

        if order is None:
            return OrderResult(
                found=False,
                message=f"未找到订单号 {normalized}。请确认订单号是否正确。",
            )

        return OrderResult(
            found=True,
            order_id=order.order_id,
            status=order.status.value,
            status_text=STATUS_TEXT.get(order.status, "未知"),
            items=order.items,
            total_amount=order.total_amount,
            shipping_address=order.shipping_address,
            created_at=order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "",
        )
