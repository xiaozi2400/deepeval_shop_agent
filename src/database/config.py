"""数据库配置"""
import os
from pathlib import Path

# 数据库 URL，默认使用项目根目录下的 orders.db
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "orders.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# SQLite 特定配置
SQLITE_ECHO = os.getenv("SQLITE_ECHO", "false").lower() == "true"
