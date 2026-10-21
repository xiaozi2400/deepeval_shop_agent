"""退换货处理工具"""
import uuid
from datetime import datetime

from langchain_core.tools import tool

# 退换货申请存储
RETURN_REQUESTS = {}

RETURN_POLICIES = {
    "return": {
        "time_limit": 7,
        "conditions": ["商品未拆封", "不影响二次销售", "附带发票"],
        "refund_time": "3-5个工作日"
    },
    "exchange": {
        "time_limit": 15,
        "conditions": ["商品存在质量问题", "型号错误", "描述不符"],
        "process_time": "5-7个工作日"
    }
}


@tool
def process_return_request(
    order_id: str,
    reason: str,
    request_type: str = "return",
    description: str = ""
) -> str:
    """处理用户的退换货申请。

    Args:
        order_id: 订单号
        reason: 退换货原因
        request_type: 申请类型，"return"表示退货，"exchange"表示换货
        description: 详细描述（可选）

    Returns:
        申请结果，包含申请编号
    """
    request_id = f"REQ{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"

    RETURN_REQUESTS[request_id] = {
        "request_id": request_id,
        "order_id": order_id,
        "type": request_type,
        "reason": reason,
        "description": description,
        "status": "pending",
        "created_at": datetime.now()
    }

    type_name = "退货" if request_type == "return" else "换货"
    return f"{type_name}申请已受理，申请编号: {request_id}。我们将尽快为您处理。"


@tool
def check_return_status(request_id: str) -> str:
    """查询退换货申请的处理状态。

    Args:
        request_id: 退换货申请编号，格式如 REQ20231015ABC123

    Returns:
        申请状态详情
    """
    status_info = RETURN_REQUESTS.get(request_id)
    if not status_info:
        return f"未找到申请编号 {request_id}，请确认申请编号是否正确。"

    type_name = "退货" if status_info["type"] == "return" else "换货"
    return f"""申请编号：{status_info['request_id']}
订单号：{status_info['order_id']}
类型：{type_name}
原因：{status_info['reason']}
状态：{status_info['status']}
申请时间：{status_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"""


@tool
def validate_return_eligibility(order_id: str, request_type: str = "return") -> str:
    """验证订单是否符合退换货资格。

    Args:
        order_id: 订单号
        request_type: 申请类型，"return"表示退货，"exchange"表示换货

    Returns:
        退换货资格和政策信息
    """
    policy = RETURN_POLICIES.get(request_type, {})
    type_name = "退货" if request_type == "return" else "换货"

    if not policy:
        return f"暂不支持{type_name}，请咨询客服。"

    conditions = "、".join(policy.get("conditions", []))
    time_limit = policy.get("time_limit", 0)
    time_info = policy.get("refund_time") or policy.get("process_time", "")

    return f"""退换货资格验证：
类型：{type_name}
申请时限：{time_limit}天内
退换货条件：{conditions}
{"退款时间：" + time_info if time_info else ""}"""
