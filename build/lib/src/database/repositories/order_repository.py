"""订单数据访问层 (Repository Pattern)"""
from datetime import datetime
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agent.state import OrderInfo, OrderStatus
from src.database.models import Order, OrderStatusDB


class SQLiteOrderRepository:
    """基于 SQLite 的订单仓库实现"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, order_id: str) -> OrderInfo | None:
        """根据订单号查询订单"""
        stmt = select(Order).where(Order.order_id == order_id)
        order_model = self.session.execute(stmt).scalar_one_or_none()
        if not order_model:
            return None
        return self._to_order_info(order_model)

    def _to_order_info(self, order: Order) -> OrderInfo:
        """将数据库模型转换为 OrderInfo dataclass"""
        return OrderInfo(
            order_id=order.order_id,
            status=_map_status_from_db(order.status),
            items=json.loads(order.items) if order.items else [],
            total_amount=order.total_amount,
            shipping_address=order.shipping_address,
            created_at=order.created_at or datetime.utcnow(),
        )


def _map_status_from_db(status: OrderStatusDB) -> OrderStatus:
    """从数据库枚举映射到 OrderStatus"""
    if isinstance(status, OrderStatusDB):
        return OrderStatus(status.value)
    return OrderStatus(str(status).lower())
