"""转人工工单数据访问层"""
from sqlalchemy.orm import Session

from src.database.models import Handoff


class SQLiteHandoffRepository:
    """基于 SQLite 的转人工工单仓库"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        handoff_id: str,
        reason: str,
    ) -> Handoff:
        """写入一条转人工工单"""
        handoff = Handoff(
            handoff_id=handoff_id,
            reason=reason,
            status="pending",
        )
        self.session.add(handoff)
        self.session.commit()
        return handoff
