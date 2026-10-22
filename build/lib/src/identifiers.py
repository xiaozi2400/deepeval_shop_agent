"""标识符解析与归一"""
import re

_ORDER_ID_PATTERN = re.compile(r"ORD\d{6,}", re.IGNORECASE)


def normalize_order_id(raw: str | None) -> str:
    """把传入的订单标识归一成规范订单号

    LLM 常把整句用户输入塞进参数（例如"帮我查一下 ORD2024001 谢谢"），
    所以先用正则从中抽出订单号，抽不到再退回去空格大写的原值。
    """
    text = (raw or "").strip()
    if not text:
        return ""

    match = _ORDER_ID_PATTERN.search(text)
    if match:
        return match.group(0).upper()

    return text.upper()
