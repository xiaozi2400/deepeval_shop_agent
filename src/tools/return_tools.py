"""退换货处理工具"""
import uuid
from datetime import datetime

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


def process_return_request(
    order_id: str,
    reason: str,
    request_type: str = "return",
    description: str = ""
) -> str:
    """处理退换货申请"""
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

    return request_id


def check_return_status(request_id: str) -> dict | None:
    """查询退换货状态"""
    return RETURN_REQUESTS.get(request_id)


def validate_return_eligibility(order_id: str, request_type: str) -> dict:
    """验证退换货资格"""
    return {
        "eligible": True,
        "policy": RETURN_POLICIES.get(request_type, {})
    }
