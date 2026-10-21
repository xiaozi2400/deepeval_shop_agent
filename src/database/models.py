"""SQLAlchemy ORM 模型"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class OrderStatusDB(str, enum.Enum):
    """数据库中的订单状态枚举"""
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    status: Mapped[str] = mapped_column(
        Enum(OrderStatusDB, native_enum=False),
        default=OrderStatusDB.PENDING
    )
    items: Mapped[str] = mapped_column(String(500), default="[]")
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    shipping_address: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Order(order_id={self.order_id}, status={self.status})>"
