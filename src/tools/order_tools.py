"""订单查询工具"""
from langchain_core.tools import tool

from src.agent.state import OrderInfo, OrderStatus
from src.database.connection import get_session
from src.database.repositories.order_repository import SQLiteOrderRepository


@tool
def query_order(order_id: str) -> str:
    """根据订单号查询订单详细信息。

    Args:
        order_id: 订单号，格式如 ORD2024001

    Returns:
        订单详细信息，包括状态、商品、金额、地址等
    """
    with get_session() as session:
        repo = SQLiteOrderRepository(session)
        order = repo.get_by_id(order_id)

        if not order:
            return f"未找到订单号 {order_id}，请确认订单号是否正确。"

        status_map = {
            OrderStatus.PENDING: "待发货",
            OrderStatus.SHIPPED: "已发货",
            OrderStatus.DELIVERED: "已签收",
            OrderStatus.CANCELLED: "已取消"
        }
        status_str = status_map.get(order.status, "未知")
        items_str = "、".join(order.items)

        return f"""订单号：{order.order_id}
状态：{status_str}
商品：{items_str}
总金额：¥{order.total_amount:.2f}
收货地址：{order.shipping_address}"""


@tool
def cancel_order(order_id: str) -> str:
    """取消未发货的订单。

    Args:
        order_id: 订单号

    Returns:
        取消结果信息
    """
    with get_session() as session:
        repo = SQLiteOrderRepository(session)
        order = repo.get_by_id(order_id)
        if not order:
            return "订单不存在"
        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            return "已发货或已签收的订单无法取消"

        repo.update_status(order_id, OrderStatus.CANCELLED)
        return "订单已取消成功"


@tool
def get_all_orders(user_id: str | None = None) -> str:
    """获取用户所有订单。

    Args:
        user_id: 用户ID（可选）

    Returns:
        订单列表信息
    """
    with get_session() as session:
        repo = SQLiteOrderRepository(session)
        orders = repo.get_all(user_id)

        if not orders:
            return "暂无订单记录"

        result = []
        for order in orders:
            status_map = {
                OrderStatus.PENDING: "待发货",
                OrderStatus.SHIPPED: "已发货",
                OrderStatus.DELIVERED: "已签收",
                OrderStatus.CANCELLED: "已取消"
            }
            status_str = status_map.get(order.status, "未知")
            items_str = "、".join(order.items)
            result.append(
                f"订单号：{order.order_id} | 状态：{status_str} | "
                f"商品：{items_str} | 金额：¥{order.total_amount:.2f}"
            )

        return "您的订单列表：\n" + "\n".join(result)


@tool
def get_valid_order_ids() -> str:
    """获取当前系统中所有有效的订单号。

    Returns:
        逗号分隔的有效订单号字符串
    """
    with get_session() as session:
        repo = SQLiteOrderRepository(session)
        order_ids = repo.get_valid_order_ids()
        return ", ".join(sorted(order_ids)) if order_ids else "系统中暂无有效订单"
