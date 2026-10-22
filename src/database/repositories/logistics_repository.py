"""物流数据访问层"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Logistics


class SQLiteLogisticsRepository:
    """基于 SQLite 的物流仓库"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_order_id(self, order_id: str) -> Logistics | None:
        """按订单号查询物流记录"""
        if not order_id:
            return None
        stmt = select(Logistics).where(Logistics.order_id == order_id)
        return self.session.execute(stmt).scalar_one_or_none()
