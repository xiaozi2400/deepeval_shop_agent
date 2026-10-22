"""SQLAlchemy ORM 模型"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""


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


class Product(Base):
    """商品模型"""
    __tablename__ = "products"

    sku_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Product(sku_id={self.sku_id}, name={self.name})>"


class Logistics(Base):
    """物流模型，一个订单至多一条物流记录"""
    __tablename__ = "logistics"

    order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    carrier: Mapped[str] = mapped_column(String(50), default="")
    tracking_number: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(20), default="")
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<Logistics(order_id={self.order_id}, status={self.status})>"


class Handoff(Base):
    """转人工工单"""
    __tablename__ = "handoffs"

    handoff_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    reason: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Handoff(handoff_id={self.handoff_id}, status={self.status})>"
