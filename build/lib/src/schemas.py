"""工具返回的结构化结果模型

工具不再返回拼好的自然语言，而是返回结构化模型：
同一份数据既作为 tool observation 回灌给 LLM，
也直接作为 DeepEval 的 context，忠实度指标才有真实依据。
"""
from pydantic import BaseModel


class ToolResult(BaseModel):
    """所有工具结果的公共语义

    found: 是否查到了实体
    needs_input: 没查到是因为参数缺失（需要向用户追问），而不是实体不存在
    message: 没查到或缺参时给 LLM 的说明与话术；查到时事实由各子类的 to_text 渲染
    """

    found: bool = False
    needs_input: bool = False
    message: str = ""

    def to_text(self) -> str:
        """渲染成给 LLM 与 DeepEval 用的文本"""
        return self.message

    def __str__(self) -> str:
        """工具结果被 LangChain 序列化时走这里，输出可读文本而非 pydantic repr"""
        return self.to_text()


class ProductResult(ToolResult):
    """商品查询结果"""

    sku_id: str = ""
    name: str = ""
    price: float = 0.0
    stock: int = 0
    in_stock: bool = False
    category: str = ""

    def to_text(self) -> str:
        if not self.found:
            return self.message
        stock_text = f"有货（库存 {self.stock} 件）" if self.in_stock else "暂时缺货"
        return (
            f"{self.name}（{self.sku_id}）售价 ¥{self.price:.2f}，"
            f"{stock_text}，分类：{self.category}"
        )


class OrderResult(ToolResult):
    """订单查询结果"""

    order_id: str = ""
    status: str = ""
    status_text: str = ""
    items: list[str] = []
    total_amount: float = 0.0
    shipping_address: str = ""
    created_at: str = ""

    def to_text(self) -> str:
        if not self.found:
            return self.message
        items_text = "、".join(self.items)
        return (
            f"订单 {self.order_id} 状态：{self.status_text}，商品：{items_text}，"
            f"金额 ¥{self.total_amount:.2f}，收货地址：{self.shipping_address}，"
            f"下单时间 {self.created_at}"
        )


class LogisticsResult(ToolResult):
    """物流查询结果"""

    order_id: str = ""
    carrier: str = ""
    tracking_number: str = ""
    status: str = ""
    status_text: str = ""
    shipped_at: str = ""
    delivered_at: str = ""
    current_location: str = ""
    estimated_delivery: str = ""

    def to_text(self) -> str:
        if not self.found:
            return self.message
        parts = [
            f"订单 {self.order_id} 的包裹由{self.carrier}承运，运单号 {self.tracking_number}",
            f"当前{self.status_text}，位置 {self.current_location}",
        ]
        if self.shipped_at:
            parts.append(f"发货时间 {self.shipped_at}")
        if self.delivered_at:
            parts.append(f"签收时间 {self.delivered_at}")
        if self.estimated_delivery:
            parts.append(f"预计送达 {self.estimated_delivery}")
        return "，".join(parts) + "。"


class PolicyResult(ToolResult):
    """政策查询结果"""

    title: str = ""
    content: str = ""
    sections: list[str] = []

    def to_text(self) -> str:
        if not self.found:
            return self.message
        lines = [f"【{self.title}】"] if self.title else []
        lines.extend(part for part in [self.content, *self.sections] if part)
        return "\n".join(lines)


class HandoffResult(ToolResult):
    """转人工工单结果"""

    handoff_id: str = ""
    reason: str = ""
    status: str = ""

    def to_text(self) -> str:
        return self.message
