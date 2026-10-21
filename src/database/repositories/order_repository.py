"""订单数据访问层 (Repository Pattern)"""
import json
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agent.state import OrderInfo, OrderStatus
from src.database.models import Order, OrderStatusDB


class OrderRepositoryBase(ABC):
    """订单仓库抽象基类"""

    @abstractmethod
    def get_by_id(self, order_id: str) -> OrderInfo | None:
        """根据订单号查询订单"""
        ...

    @abstractmethod
    def get_all(self, user_id: str | None = None) -> list[OrderInfo]:
        """获取所有订单，可按用户ID过滤"""
        ...

    @abstractmethod
    def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """更新订单状态"""
        ...

    @abstractmethod
    def create(self, order: OrderInfo, user_id: str | None = None) -> bool:
        """创建新订单"""
        ...

    @abstractmethod
    def get_valid_order_ids(self) -> set[str]:
        """获取所有有效的订单号（用于 extract_order_id）"""
        ...


class SQLiteOrderRepository(OrderRepositoryBase):
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

    def get_all(self, user_id: str | None = None) -> list[OrderInfo]:
        """获取所有订单，可按用户ID过滤"""
        stmt = select(Order)
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)
        orders = self.session.execute(stmt).scalars().all()
        return [self._to_order_info(o) for o in orders]

    def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """更新订单状态"""
        stmt = select(Order).where(Order.order_id == order_id)
        order = self.session.execute(stmt).scalar_one_or_none()
        if not order:
            return False
        order.status = _map_status_to_db(status)
        self.session.commit()
        return True

    def create(self, order: OrderInfo, user_id: str | None = None) -> bool:
        """创建新订单"""
        order_model = Order(
            order_id=order.order_id,
            status=_map_status_to_db(order.status),
            items=json.dumps(order.items),
            total_amount=order.total_amount,
            shipping_address=order.shipping_address,
            created_at=order.created_at,
            user_id=user_id,
        )
        self.session.add(order_model)
        self.session.commit()
        return True

    def get_valid_order_ids(self) -> set[str]:
        """获取所有有效的订单号"""
        stmt = select(Order.order_id)
        order_ids = self.session.execute(stmt).scalars().all()
        return set(order_ids)

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


def _map_status_to_db(status: OrderStatus) -> OrderStatusDB:
    """将 OrderStatus 映射到数据库枚举"""
    mapping = {
        OrderStatus.PENDING: OrderStatusDB.PENDING,
        OrderStatus.SHIPPED: OrderStatusDB.SHIPPED,
        OrderStatus.DELIVERED: OrderStatusDB.DELIVERED,
        OrderStatus.CANCELLED: OrderStatusDB.CANCELLED,
    }
    return mapping.get(status, OrderStatusDB.PENDING)


def _map_status_from_db(status: OrderStatusDB) -> OrderStatus:
    """从数据库枚举映射到 OrderStatus"""
    mapping = {
        OrderStatusDB.PENDING: OrderStatus.PENDING,
        OrderStatusDB.SHIPPED: OrderStatus.SHIPPED,
        OrderStatusDB.DELIVERED: OrderStatus.DELIVERED,
        OrderStatusDB.CANCELLED: OrderStatus.CANCELLED,
    }
    if isinstance(status, str):
        status = OrderStatusDB(status)
    return mapping.get(status, OrderStatus.PENDING)
