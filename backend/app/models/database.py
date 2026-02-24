"""
数据库连接与会话管理模块

提供 SQLAlchemy 引擎、会话工厂以及声明式基类。
SQLite 使用 check_same_thread=False 以兼容 FastAPI 异步场景。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# 仅 SQLite 需要 check_same_thread=False，其他数据库引擎不支持该参数
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。"""
    pass


def get_db():
    """FastAPI 依赖注入：获取数据库会话，请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
