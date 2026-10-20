"""模拟订单数据"""
from datetime import datetime, timedelta

from src.agent.state import OrderInfo, OrderStatus

MOCK_ORDERS = {
    "ORD2024001": OrderInfo(
        order_id="ORD2024001",
        status=OrderStatus.SHIPPED,
        items=["iPhone 15 Pro Max 256GB", "AirPods Pro 2"],
        total_amount=12498.0,
        shipping_address="北京市朝阳区建国路88号",
        created_at=datetime.now() - timedelta(days=2)
    ),
    "ORD2024002": OrderInfo(
        order_id="ORD2024002",
        status=OrderStatus.DELIVERED,
        items=["MacBook Pro 14寸", "Magic Mouse"],
        total_amount=19999.0,
        shipping_address="上海市浦东新区世纪大道100号",
        created_at=datetime.now() - timedelta(days=7)
    ),
    "ORD2024003": OrderInfo(
        order_id="ORD2024003",
        status=OrderStatus.PENDING,
        items=["iPad Air 5", "Apple Pencil"],
        total_amount=6899.0,
        shipping_address="广州市天河区天河路123号",
        created_at=datetime.now() - timedelta(days=1)
    ),
    "ORD2024004": OrderInfo(
        order_id="ORD2024004",
        status=OrderStatus.CANCELLED,
        items=["Sony WH-1000XM5"],
        total_amount=2999.0,
        shipping_address="深圳市南山区科技园南路88号",
        created_at=datetime.now() - timedelta(days=3)
    ),
}
