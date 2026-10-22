"""工具单元测试"""
from sqlalchemy import select

from src.agent.state import OrderStatus
from src.database.connection import get_session
from src.database.models import Handoff
from src.tools.handoff_tools import handoff_to_human
from src.tools.logistics_tools import query_logistics
from src.tools.order_tools import query_order
from src.tools.policy_tools import search_policy
from src.tools.product_tools import query_product


class TestProductTool:
    def test_query_by_sku(self):
        result = query_product.invoke({"sku_id": "SKU-IPHONE-15-PROMAX-256"})
        assert result.found is True
        assert result.name == "iPhone 15 Pro Max 256GB"
        assert result.price == 9999.0
        assert result.stock == 50
        assert result.in_stock is True

    def test_query_by_name_resolves_sku(self):
        result = query_product.invoke({"sku_id": "iPhone 15 Pro Max 256GB"})
        assert result.found is True
        assert result.sku_id == "SKU-IPHONE-15-PROMAX-256"

    def test_resolves_name_embedded_in_the_question(self):
        """LLM 可能把整句问法塞进 sku_id，商品名在里面就要能认出来"""
        result = query_product.invoke({"sku_id": "iPhone 15 Pro Max 256GB 多少钱"})
        assert result.found is True
        assert result.sku_id == "SKU-IPHONE-15-PROMAX-256"

    def test_out_of_stock(self):
        result = query_product.invoke({"sku_id": "SKU-SONY-WH1000XM5"})
        assert result.found is True
        assert result.stock == 0
        assert result.in_stock is False

    def test_missing_param_needs_input(self):
        result = query_product.invoke({"sku_id": ""})
        assert result.found is False
        assert result.needs_input is True

    def test_unknown_product(self):
        result = query_product.invoke({"sku_id": "量子计算器xyz"})
        assert result.found is False
        assert result.needs_input is False


class TestOrderTool:
    def test_query_existing_order(self):
        result = query_order.invoke({"order_id": "ORD2024001"})
        assert result.found is True
        assert result.order_id == "ORD2024001"
        assert result.status == OrderStatus.SHIPPED.value
        assert result.status_text == "已发货"
        assert result.total_amount == 12498.0
        assert "iPhone 15 Pro Max 256GB" in result.items

    def test_status_is_not_pinned_to_pending(self):
        """回归测试：跨枚举查表曾让所有订单都读成"待发货\""""
        assert query_order.invoke({"order_id": "ORD2024001"}).status_text == "已发货"
        assert query_order.invoke({"order_id": "ORD2024002"}).status_text == "已签收"
        assert query_order.invoke({"order_id": "ORD2024003"}).status_text == "待发货"
        assert query_order.invoke({"order_id": "ORD2024004"}).status_text == "已取消"

    def test_extracts_order_id_from_free_text(self):
        result = query_order.invoke({"order_id": "帮我查一下 ORD2024002 谢谢"})
        assert result.found is True
        assert result.order_id == "ORD2024002"

    def test_missing_param_needs_input(self):
        result = query_order.invoke({"order_id": ""})
        assert result.found is False
        assert result.needs_input is True

    def test_nonexistent_order(self):
        result = query_order.invoke({"order_id": "ORD9999999"})
        assert result.found is False
        assert result.needs_input is False


class TestLogisticsTool:
    def test_query_in_transit(self):
        result = query_logistics.invoke({"order_id": "ORD2024001"})
        assert result.found is True
        assert result.carrier == "顺丰速运"
        assert result.tracking_number == "SF1234567890"
        assert result.status == "in_transit"
        assert result.current_location == "北京市分拨中心"

    def test_query_delivered(self):
        result = query_logistics.invoke({"order_id": "ORD2024002"})
        assert result.found is True
        assert result.status == "delivered"
        assert result.delivered_at

    def test_order_without_logistics(self):
        result = query_logistics.invoke({"order_id": "ORD2024003"})
        assert result.found is False
        assert result.needs_input is False
        assert "暂无物流信息" in result.message

    def test_missing_param_needs_input(self):
        result = query_logistics.invoke({"order_id": ""})
        assert result.found is False
        assert result.needs_input is True

    def test_nonexistent_order(self):
        result = query_logistics.invoke({"order_id": "ORD9999999"})
        assert result.found is False


class TestPolicyTool:
    def test_seven_day_no_reason(self):
        result = search_policy.invoke({"query": "能七天无理由吗"})
        assert result.found is True
        assert "7天" in result.content
        assert "退换货" in result.title

    def test_shipping_fee(self):
        result = search_policy.invoke({"query": "运费怎么算"})
        assert result.found is True
        assert "99" in result.content

    def test_shipping_policy(self):
        result = search_policy.invoke({"query": "配送政策是什么"})
        assert result.found is True
        assert "发货" in result.content

    def test_unknown_policy(self):
        result = search_policy.invoke({"query": "量子计算机怎么买"})
        assert result.found is False
        assert result.needs_input is False

    def test_matched_sections_keep_primary_content(self):
        result = search_policy.invoke({"query": "运费怎么算，配送要几天"})
        assert result.found is True
        assert result.content
        assert result.sections


class TestHandoffTool:
    def test_creates_ticket(self):
        result = handoff_to_human.invoke({"reason": "用户投诉服务态度差"})
        assert result.found is True
        assert result.handoff_id.startswith("HO")
        assert result.status == "pending"

    def test_ticket_is_persisted(self):
        result = handoff_to_human.invoke({"reason": "要求取消订单"})
        with get_session() as session:
            row = session.execute(
                select(Handoff).where(Handoff.handoff_id == result.handoff_id)
            ).scalar_one()
            assert row.reason == "要求取消订单"
            assert row.status == "pending"

    def test_missing_param_needs_input(self):
        result = handoff_to_human.invoke({"reason": ""})
        assert result.found is False
        assert result.needs_input is True
