"""数据库初始化和种子数据"""
import json
from datetime import datetime, timedelta

from src.database.connection import get_session
from src.database.models import Order, OrderStatusDB


# 内嵌的初始订单数据
_INITIAL_ORDERS = [
    {
        "order_id": "ORD2024001",
        "status": "shipped",
        "items": ["iPhone 15 Pro Max 256GB", "AirPods Pro 2"],
        "total_amount": 12498.0,
        "shipping_address": "北京市朝阳区建国路88号",
        "created_at": datetime.now() - timedelta(days=2),
    },
    {
        "order_id": "ORD2024002",
        "status": "delivered",
        "items": ["MacBook Pro 14寸", "Magic Mouse"],
        "total_amount": 19999.0,
        "shipping_address": "上海市浦东新区世纪大道100号",
        "created_at": datetime.now() - timedelta(days=7),
    },
    {
        "order_id": "ORD2024003",
        "status": "pending",
        "items": ["iPad Air 5", "Apple Pencil"],
        "total_amount": 6899.0,
        "shipping_address": "广州市天河区天河路123号",
        "created_at": datetime.now() - timedelta(days=1),
    },
    {
        "order_id": "ORD2024004",
        "status": "cancelled",
        "items": ["Sony WH-1000XM5"],
        "total_amount": 2999.0,
        "shipping_address": "深圳市南山区科技园南路88号",
        "created_at": datetime.now() - timedelta(days=3),
    },
]


def seed_initial_orders() -> None:
    """初始化订单数据到数据库"""
    with get_session() as session:
        # 检查是否已有数据
        existing = session.query(Order).first()
        if existing:
            return  # 已有数据，跳过

        # 插入初始数据
        for order_data in _INITIAL_ORDERS:
            order_model = Order(
                order_id=order_data["order_id"],
                status=_map_status(order_data["status"]),
                items=json.dumps(order_data["items"]),
                total_amount=order_data["total_amount"],
                shipping_address=order_data["shipping_address"],
                created_at=order_data["created_at"],
            )
            session.add(order_model)
        session.commit()


def _map_status(status_str: str) -> OrderStatusDB:
    """将字符串状态映射到 OrderStatusDB 枚举"""
    status_map = {
        "pending": OrderStatusDB.PENDING,
        "shipped": OrderStatusDB.SHIPPED,
        "delivered": OrderStatusDB.DELIVERED,
        "cancelled": OrderStatusDB.CANCELLED,
    }
    return status_map.get(status_str.lower(), OrderStatusDB.PENDING)
