"""工具单元测试"""
from src.agent.state import OrderStatus
from src.tools.faq_tools import search_faq
from src.tools.order_tools import cancel_order, query_order
from src.tools.policy_tools import query_policy
from src.tools.return_tools import process_return_request, validate_return_eligibility


class TestOrderTools:
    def test_query_existing_order(self):
        order = query_order("ORD2024001")
        assert order is not None
        assert order.order_id == "ORD2024001"
        assert order.status == OrderStatus.SHIPPED

    def test_query_nonexistent_order(self):
        order = query_order("INVALID")
        assert order is None

    def test_cancel_pending_order(self):
        from src.database.connection import get_session
        from src.database.repositories.order_repository import SQLiteOrderRepository
        # 获取仓库并查询原始状态
        with get_session() as session:
            repo = SQLiteOrderRepository(session)
            original_order = repo.get_by_id("ORD2024003")
            original_status = original_order.status
        # 取消订单
        result = cancel_order("ORD2024003")
        assert result["success"] is True
        # 恢复订单状态
        with get_session() as session:
            repo = SQLiteOrderRepository(session)
            repo.update_status("ORD2024003", original_status)

    def test_cancel_shipped_order(self):
        result = cancel_order("ORD2024001")
        assert result["success"] is False
        assert "无法取消" in result["message"]

    def test_get_valid_order_ids(self):
        from src.tools.order_tools import get_valid_order_ids
        ids = get_valid_order_ids()
        assert "ORD2024001" in ids
        assert "ORD2024002" in ids
        assert "ORD2024003" in ids
        assert "ORD2024004" in ids


class TestFAQQueries:
    def test_search_shipping_cost(self):
        result = search_faq("运费如何计算")
        assert "99" in result or "运费" in result

    def test_search_payment(self):
        result = search_faq("支持哪些支付方式")
        assert "支付宝" in result or "微信" in result

    def test_no_match(self):
        result = search_faq("一些无关的内容xyz123")
        assert "抱歉" in result


class TestReturnTools:
    def test_process_return_request(self):
        request_id = process_return_request(
            order_id="ORD2024001",
            reason="商品不满意",
            request_type="return"
        )
        assert request_id.startswith("REQ")

    def test_validate_return_eligibility(self):
        result = validate_return_eligibility("ORD2024001", "return")
        assert result["eligible"] is True


class TestPolicyTools:
    def test_query_shipping_policy(self):
        result = query_policy("配送政策")
        assert "发货" in result or "配送" in result

    def test_query_return_policy(self):
        result = query_policy("退货政策")
        assert "7天" in result or "退货" in result
