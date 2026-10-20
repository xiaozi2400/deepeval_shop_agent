"""Agent节点定义"""
import re

from langchain_core.messages import AIMessage

from src.agent.state import CustomerServiceState, Intent
from src.tools.faq_tools import search_faq
from src.tools.order_tools import format_order_info, query_order
from src.tools.policy_tools import query_policy
from src.tools.return_tools import process_return_request


def routing_node(state: CustomerServiceState) -> CustomerServiceState:
    """路由节点 - 意图分类"""
    last_message = state["messages"][-1].content.lower()

    if any(word in last_message for word in ["你好", "hi", "hello", "在吗", "嗨"]):
        next_node = "greeting_node"
    elif any(word in last_message for word in ["退货", "换货", "退款", "退换"]):
        next_node = "return_exchange_node"
    elif any(word in last_message for word in ["订单", "查单", "什么时候到", "发货", "物流", "到了吗"]):
        next_node = "order_query_node"
    elif any(word in last_message for word in ["运费", "支付", "联系客服", "积分"]):
        next_node = "faq_node"
    elif any(word in last_message for word in ["政策", "规定", "规则", "会员"]):
        next_node = "policy_query_node"
    elif any(word in last_message for word in ["谢谢", "再见", "bye", "拜拜"]):
        next_node = "goodbye_node"
    else:
        next_node = "faq_node"

    return {"next_node": next_node}


def extract_order_id(text: str) -> str:
    """从文本中提取订单号"""
    patterns = [
        r'ORD\d{7}',
        r'订单[0-9A-Za-z]+',
        r'订单号[：:]?\s*([A-Za-z0-9]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            order_id = match.group(0) if 'ORD' in match.group(0) else match.group(1) if match.lastindex else match.group(0)
            if 'ORD' not in order_id and '订单' in order_id:
                continue
            for oid in ["ORD2024001", "ORD2024002", "ORD2024003", "ORD2024004"]:
                if oid in text:
                    return oid
            return order_id
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
        "current_node": "order_query_node"
    }


def return_exchange_node(state: CustomerServiceState) -> CustomerServiceState:
    """退换货处理节点"""
    last_message = state["messages"][-1].content

    if "退货" in last_message:
        order_id = extract_order_id(last_message)
        if order_id:
            result = process_return_request(
                order_id=order_id,
                reason="用户申请退货",
                request_type="return"
            )
            response = f"您的退货申请已受理，退款将在3-5个工作日内原路返回。申请编号: {result}"
        else:
            response = "请提供您要退货的订单号，例如：退货订单ORD2024003"
    elif "换货" in last_message:
        order_id = extract_order_id(last_message)
        if order_id:
            result = process_return_request(
                order_id=order_id,
                reason="用户申请换货",
                request_type="exchange"
            )
            response = f"您的换货申请已受理，我们将尽快为您处理。申请编号: {result}"
        else:
            response = "请提供您要换货的订单号，例如：换货订单ORD2024001"
    else:
        response = "请问您是需要退货还是换货呢？"

    return {
        "messages": [AIMessage(content=response)],
        "intent": Intent.RETURN_EXCHANGE,
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
