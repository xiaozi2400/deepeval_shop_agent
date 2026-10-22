"""数据库初始化和种子数据"""
import json
from datetime import datetime, timedelta

from src.database.connection import get_session
from src.database.models import Logistics, Order, OrderStatusDB, Product

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

# 商品数据。ORD2024003 / ORD2024004 刻意不配物流记录，
# 让"该订单暂无物流信息"成为一个真实的可测场景。
_INITIAL_PRODUCTS = [
    {"sku_id": "SKU-IPHONE-15-PROMAX-256", "name": "iPhone 15 Pro Max 256GB", "price": 9999.0, "stock": 50, "category": "手机"},
    {"sku_id": "SKU-AIRPODS-PRO-2", "name": "AirPods Pro 2", "price": 1899.0, "stock": 200, "category": "耳机"},
    {"sku_id": "SKU-MACBOOK-PRO-14", "name": "MacBook Pro 14寸", "price": 15999.0, "stock": 30, "category": "电脑"},
    {"sku_id": "SKU-IPAD-AIR-5", "name": "iPad Air 5", "price": 5899.0, "stock": 80, "category": "平板"},
    {"sku_id": "SKU-MAGIC-MOUSE", "name": "Magic Mouse", "price": 699.0, "stock": 150, "category": "配件"},
    {"sku_id": "SKU-APPLE-PENCIL", "name": "Apple Pencil", "price": 999.0, "stock": 100, "category": "配件"},
    {"sku_id": "SKU-SONY-WH1000XM5", "name": "Sony WH-1000XM5", "price": 2999.0, "stock": 0, "category": "耳机"},
]

_INITIAL_LOGISTICS = [
    {
        "order_id": "ORD2024001",
        "carrier": "顺丰速运",
        "tracking_number": "SF1234567890",
        "status": "in_transit",
        "shipped_at": datetime.now() - timedelta(days=1),
        "delivered_at": None,
        "current_location": "北京市分拨中心",
    },
    {
        "order_id": "ORD2024002",
        "carrier": "中通快递",
        "tracking_number": "ZT9876543210",
        "status": "delivered",
        "shipped_at": datetime.now() - timedelta(days=3),
        "delivered_at": datetime.now() - timedelta(days=1),
        "current_location": "上海市浦东新区",
    },
]


def _seed_if_missing(session, model, pk_value, **fields) -> bool:
    """按主键逐条补种，已存在则跳过，不覆盖既有数据"""
    if session.get(model, pk_value) is not None:
        return False
    session.add(model(**fields))
    return True


def seed_initial_orders() -> None:
    """初始化订单数据到数据库"""
    with get_session() as session:
        for order_data in _INITIAL_ORDERS:
            _seed_if_missing(
                session,
                Order,
                order_data["order_id"],
                order_id=order_data["order_id"],
                status=_map_status(order_data["status"]),
                items=json.dumps(order_data["items"]),
                total_amount=order_data["total_amount"],
                shipping_address=order_data["shipping_address"],
                created_at=order_data["created_at"],
            )
        session.commit()


def seed_products() -> None:
    """初始化商品数据到数据库"""
    with get_session() as session:
        for product in _INITIAL_PRODUCTS:
            _seed_if_missing(session, Product, product["sku_id"], **product)
        session.commit()


def seed_logistics() -> None:
    """初始化物流数据到数据库"""
    with get_session() as session:
        for logistics in _INITIAL_LOGISTICS:
            _seed_if_missing(session, Logistics, logistics["order_id"], **logistics)
        session.commit()


def seed_all() -> None:
    """初始化全部种子数据"""
    seed_initial_orders()
    seed_products()
    seed_logistics()


def _map_status(status_str: str) -> OrderStatusDB:
    """将字符串状态映射到 OrderStatusDB 枚举"""
    return OrderStatusDB(status_str.lower())
