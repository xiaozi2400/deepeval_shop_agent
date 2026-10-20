"""pytest配置文件"""
import os
import sys

import pytest

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境"""
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key")
    yield
