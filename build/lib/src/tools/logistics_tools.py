"""物流查询工具"""
from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.repositories.logistics_repository import SQLiteLogisticsRepository
from src.database.repositories.order_repository import SQLiteOrderRepository
from src.identifiers import normalize_order_id
from src.schemas import LogisticsResult
from src.tools.order_tools import STATUS_TEXT

LOGISTICS_STATUS_TEXT = {
    "pending": "待发货",
    "in_transit": "运输中",
    "delivered": "已签收",
    "exception": "物流异常",
}


@tool
def query_logistics(order_id: str) -> LogisticsResult:
    """查询订单的物流轨迹与承运信息。

    Args:
        order_id: 订单号，格式如 ORD2024001。传入整句用户输入也能从中解析出订单号。

    Returns:
        承运商、运单号、当前位置与时效；缺订单号时 needs_input 为 True，
        订单无物流记录时 found 为 False。
    """
    normalized = normalize_order_id(order_id)
    if not normalized:
        return LogisticsResult(
            found=False,
            needs_input=True,
            message="需要订单号才能查询物流。请向用户索要订单号，格式如 ORD2024001。",
        )

    with get_session() as session:
        logistics_repo = SQLiteLogisticsRepository(session)
        logistics = logistics_repo.get_by_order_id(normalized)

        if logistics is None:
            order_repo = SQLiteOrderRepository(session)
            order = order_repo.get_by_id(normalized)
            if order is None:
                return LogisticsResult(
                    found=False,
                    message=f"未找到订单号 {normalized}，无法查询物流。请确认订单号是否正确。",
                )
            return LogisticsResult(
                found=False,
                message=f"订单 {normalized} 当前状态为{STATUS_TEXT.get(order.status, '未知')}，暂无物流信息。",
            )

        status_text = LOGISTICS_STATUS_TEXT.get(logistics.status, logistics.status)
        return LogisticsResult(
            found=True,
            order_id=logistics.order_id,
            carrier=logistics.carrier,
            tracking_number=logistics.tracking_number,
            status=logistics.status,
            status_text=status_text,
            shipped_at=logistics.shipped_at.strftime("%Y-%m-%d %H:%M") if logistics.shipped_at else "",
            delivered_at=logistics.delivered_at.strftime("%Y-%m-%d %H:%M") if logistics.delivered_at else "",
            current_location=logistics.current_location or "",
            estimated_delivery=_estimate_delivery(logistics),
        )


def _estimate_delivery(logistics) -> str:
    """按承运商与状态给出预计送达时间"""
    if logistics.status == "delivered":
        return ""
    if logistics.carrier == "顺丰速运":
        return "预计2-3天送达"
    if logistics.carrier == "中通快递":
        return "预计3-4天送达"
    return "预计3-5天送达"
