"""Agent节点定义"""
import re

from langchain_core.messages import AIMessage

from src.agent.state import CustomerServiceState, Intent
from src.tools.faq_tools import search_faq
from src.tools.order_tools import format_order_info, query_order
from src.tools.policy_tools import query_policy
from src.tools.return_tools import process_return_request


def routing_node(state: CustomerServiceState, llm) -> CustomerServiceState:
    """路由节点 - 使用LLM进行意图分类，支持降级到关键词匹配"""
    last_message = state["messages"][-1].content

    if llm is None:
        # 降级到关键词匹配
        intent = _keyword_based_routing(last_message)
    else:
        prompt = f"""你是一个电商客服意图分类器。请根据用户消息判断用户意图。

用户消息: {last_message}

可选意图:
- greeting_node: 用户在问候或打招呼
- order_query_node: 用户在查询订单状态
- return_exchange_node: 用户在申请退换货
- policy_query_node: 用户在询问政策（如配送政策、退换货政策、会员政策）
- faq_node: 用户在咨询常见问题（如运费、支付方式、联系客服）
- goodbye_node: 用户在说再见或结束对话

请只返回一个意图名称，不要其他内容。"""

        response = llm.invoke(prompt)
        intent = response.content.strip().lower()

        # 验证返回的意图是否有效
        valid_intents = ["greeting_node", "order_query_node", "return_exchange_node",
                         "policy_query_node", "faq_node", "goodbye_node"]

        if intent not in valid_intents:
            intent = "faq_node"

    return {"next_node": intent}


def _keyword_based_routing(message: str) -> str:
    """基于关键词的路由降级方案"""
    msg_lower = message.lower()

    # 告别检测（优先级最高）
    if any(kw in msg_lower for kw in ["再见", "bye", "拜拜", "结束"]):
        return "goodbye_node"

    # 问候检测
    if any(kw in msg_lower for kw in ["你好", "hi", "hello", "在吗", "您好", "嗨"]):
        return "greeting_node"

    # 政策查询检测（优先级高于退换货，因为询问政策不是申请退换货）
    if any(kw in msg_lower for kw in ["政策", "规定", "规则"]):
        return "policy_query_node"

    # 会员/积分政策
    if any(kw in msg_lower for kw in ["会员", "积分", "折扣", "等级"]):
        return "policy_query_node"

    # 配送查询（独立于退换货）
    if any(kw in msg_lower for kw in ["配送", "发货", "送到"]):
        return "policy_query_node"

    # 退换货检测（在政策类关键词之后）
    if any(kw in msg_lower for kw in ["退货", "换货", "退款", "退换"]):
        return "return_exchange_node"

    # 订单查询检测
    if any(kw in msg_lower for kw in ["订单", "查单", "物流", "到了", "签收"]):
        return "order_query_node"

    # FAQ检测
    if any(kw in msg_lower for kw in ["运费", "支付", "联系客服", "怎么联系", "客服电话"]):
        return "faq_node"

    # 默认FAQ
    return "faq_node"


def extract_order_id(text: str) -> str:
    """从文本中提取订单号"""
    from src.data.mock_orders import MOCK_ORDERS
    valid_order_ids = set(MOCK_ORDERS.keys())

    patterns = [
        r'ORD\d{7}',                           # ORD2024001 格式
        r'订单[：:]?\s*([A-Za-z0-9]+)',        # 订单号：xxx 格式
        r'订单\s*([A-Za-z0-9]+)',              # 订单 xxx 格式
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # 提取可能的订单号
            candidate = match.group(1) if match.lastindex else match.group(0)
            # 清理并检查是否是有效订单号
            candidate = candidate.strip()
            if candidate in valid_order_ids:
                return candidate
            # 检查是否包含有效订单号（用于 "订单ORD2024001" 格式）
            for oid in valid_order_ids:
                if oid in text:
                    return oid

    return ""


def faq_node(state: CustomerServiceState) -> CustomerServiceState:
    """FAQ问答节点"""
    last_message = state["messages"][-1].content
    answer = search_faq(last_message)

    return {
        "messages": [AIMessage(content=answer)],
        "intent": Intent.FAQ,
        "current_node": "faq_node"
    }


def order_query_node(state: CustomerServiceState) -> CustomerServiceState:
    """订单查询节点"""
    last_message = state["messages"][-1].content

    order_id = extract_order_id(last_message)
    order_info = None
    if order_id:
        order_info = query_order(order_id)
        if order_info:
            response = format_order_info(order_info)
        else:
            response = f"未找到订单号 {order_id}，请确认订单号是否正确。"
    else:
        response = "请提供您的订单号，以便我为您查询。例如：帮我查一下订单ORD2024001"

    return {
        "messages": [AIMessage(content=response)],
        "intent": Intent.ORDER_QUERY,
        "order_info": order_info,
        "current_node": "order_query_node"
    }


def return_exchange_node(state: CustomerServiceState) -> CustomerServiceState:
    """退换货处理节点"""
    from src.agent.state import ReturnRequest

    last_message = state["messages"][-1].content
    return_request = None

    if "退货" in last_message:
        order_id = extract_order_id(last_message)
        if order_id:
            request_id = process_return_request(
                order_id=order_id,
                reason="用户申请退货",
                request_type="return"
            )
            return_request = ReturnRequest(
                order_id=order_id,
                reason="用户申请退货",
                request_type="return",
                status="pending"
            )
            response = f"您的退货申请已受理，退款将在3-5个工作日内原路返回。申请编号: {request_id}"
        else:
            response = "请提供您要退货的订单号，例如：退货订单ORD2024003"
    elif "换货" in last_message:
        order_id = extract_order_id(last_message)
        if order_id:
            request_id = process_return_request(
                order_id=order_id,
                reason="用户申请换货",
                request_type="exchange"
            )
            return_request = ReturnRequest(
                order_id=order_id,
                reason="用户申请换货",
                request_type="exchange",
                status="pending"
            )
            response = f"您的换货申请已受理，我们将尽快为您处理。申请编号: {request_id}"
        else:
            response = "请提供您要换货的订单号，例如：换货订单ORD2024001"
    else:
        response = "请问您是需要退货还是换货呢？"

    return {
        "messages": [AIMessage(content=response)],
        "intent": Intent.RETURN_EXCHANGE,
        "return_request": return_request,
        "current_node": "return_exchange_node"
    }


def policy_query_node(state: CustomerServiceState) -> CustomerServiceState:
    """政策查询节点"""
    last_message = state["messages"][-1].content
    policy_info = query_policy(last_message)

    return {
        "messages": [AIMessage(content=policy_info)],
        "intent": Intent.POLICY_QUERY,
        "current_node": "policy_query_node"
    }


def greeting_node(state: CustomerServiceState) -> CustomerServiceState:
    """问候节点"""
    greeting = """您好！我是电商客服助手，请问有什么可以帮您？您可以：

1. 查询订单状态（告诉我订单号即可）
2. 办理退换货（告诉我订单号和退货/换货）
3. 了解购物政策（配送、退换货、支付、会员政策）
4. 咨询常见问题（运费、支付方式、联系客服等）"""
    return {
        "messages": [AIMessage(content=greeting)],
        "intent": Intent.GREETING,
        "current_node": "greeting_node"
    }


def goodbye_node(state: CustomerServiceState) -> CustomerServiceState:
    """告别节点"""
    return {
        "messages": [AIMessage(content="感谢您的咨询，祝您购物愉快！如有需要随时联系我。")],
        "intent": Intent.GOODBYE,
        "current_node": "goodbye_node"
    }
