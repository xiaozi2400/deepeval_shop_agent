"""转人工工具"""
import uuid
from datetime import datetime

from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.repositories.handoff_repository import SQLiteHandoffRepository
from src.schemas import HandoffResult


@tool
def handoff_to_human(reason: str) -> HandoffResult:
    """转接人工客服并生成工单。

    适用于用户投诉、表达不满、意图不明，以及一切需要人工介入的操作类请求
    （如取消订单、办理退换货、修改收货地址）。用户明确要求人工客服时也走这里。

    Args:
        reason: 转人工的原因，简要说明用户的诉求。

    Returns:
        工单编号与后续指引；缺原因时 needs_input 为 True。
    """
    text = (reason or "").strip()
    if not text:
        return HandoffResult(
            found=False,
            needs_input=True,
            message="转接人工客服需要说明原因，请补充用户的具体诉求。",
        )

    handoff_id = f"HO{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    with get_session() as session:
        repo = SQLiteHandoffRepository(session)
        repo.create(handoff_id=handoff_id, reason=text)

    return HandoffResult(
        found=True,
        handoff_id=handoff_id,
        reason=text,
        status="pending",
        message=f"已为您转接人工客服，工单编号 {handoff_id}。"
                f"人工客服会尽快接手，客服热线 400-123-4567，服务时间 9:00-21:00。",
    )
