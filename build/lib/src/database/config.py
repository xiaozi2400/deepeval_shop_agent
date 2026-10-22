"""数据库配置"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# 默认库放在 data/ 下，是运行时产物，不进版本库。
DEFAULT_DB_PATH = DATA_DIR / "orders.db"


def _resolve_sqlite_url(url: str) -> str:
    """把 sqlite URL 里的相对路径锚定到项目

    写明目录的相对路径（如 sqlite:///data/orders.db）锚定到项目根，
    纯文件名（如 sqlite:///orders.db）落在 data/ 下。这样无论从哪个工作目录
    启动，同一份配置都指向同一张库。
    """
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url
    raw = url[len(prefix):]
    if not raw or raw == ":memory:":
        return url
    path = Path(raw)
    if not path.is_absolute():
        base = DATA_DIR if len(path.parts) == 1 else PROJECT_ROOT
        path = (base / path).resolve()
    return prefix + path.as_posix()


DATABASE_URL = _resolve_sqlite_url(
    os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")
)

# SQLite 特定配置
SQLITE_ECHO = os.getenv("SQLITE_ECHO", "false").lower() == "true"

if "sqlite" in DATABASE_URL:
    _db_path = Path(DATABASE_URL[len("sqlite:///"):])
    _db_path.parent.mkdir(parents=True, exist_ok=True)
