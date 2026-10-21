"""数据库连接和会话管理"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.database.config import DATABASE_URL, SQLITE_ECHO

# 根据数据库类型设置连接参数
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=SQLITE_ECHO,
    pool_pre_ping=True,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """初始化数据库，创建表并填充初始数据"""
    from src.database.models import Base
    from src.database.seed import seed_initial_orders

    Base.metadata.create_all(bind=engine)
    seed_initial_orders()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """获取数据库会话的上下文管理器

    Usage:
        with get_session() as session:
            result = session.query(Order).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
