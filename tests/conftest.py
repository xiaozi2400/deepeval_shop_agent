"""pytest 配置"""
import os
import sys
from pathlib import Path

import pytest

# 必须在任何 src.* 被 import 之前把数据库指向临时库。
# 否则测试会写进开发库 data/orders.db，把订单状态改脏。
_TMP_DB = Path(__file__).parent / ".tmp" / "test.db"
_TMP_DB.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """每次会话用一张全新的库，跑完的种子数据不残留"""
    from src.database.connection import init_db

    if _TMP_DB.exists():
        _TMP_DB.unlink()
    init_db()
    yield


@pytest.fixture
def fake_llm():
    """返回 FakeToolCallingModel 的工厂，用来在不调用真实 LLM 的前提下驱动 ReAct 循环"""
    from tests.fake_llm import FakeToolCallingModel

    return FakeToolCallingModel
