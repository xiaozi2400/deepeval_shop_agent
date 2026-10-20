"""订单查询工具"""

from src.agent.state import OrderInfo, OrderStatus
from src.data.mock_orders import MOCK_ORDERS


def query_order(order_id: str) -> OrderInfo | None:
    """查询订单信息"""
    return MOCK_ORDERS.get(order_id)


def cancel_order(order_id: str) -> dict:
    """取消订单"""
    order = MOCK_ORDERS.get(order_id)
    if not order:
        return {"success": False, "message": "订单不存在"}
    if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        return {"success": False, "message": "已发货或已签收的订单无法取消"}

    order.status = OrderStatus.CANCELLED
    return {"success": True, "message": "订单已取消"}


def get_all_orders(user_id: str | None = None) -> list[OrderInfo]:
    """获取用户所有订单"""
    return list(MOCK_ORDERS.values())


def format_order_info(order: OrderInfo) -> str:
    """格式化订单信息"""
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
