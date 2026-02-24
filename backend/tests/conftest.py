"""
测试公共 fixtures

提供独立的 SQLite 内存数据库和预填充的测试数据，
确保每个测试会话与生产数据完全隔离。
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.community import Community, NearbyPOI, SchoolDistrict
from app.models.database import Base, get_db
from app.main import app

# 使用内存 SQLite 数据库，StaticPool 保证所有连接共享同一个内存库
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=_test_engine,
)


def _override_get_db() -> Generator[Session, None, None]:
    """替换 FastAPI 依赖注入的数据库会话，指向测试数据库。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    会话级 fixture：创建表结构、插入种子数据，测试结束后清理。

    使用 scope="session" 避免每个测试函数重复建表和插入数据。
    """
    # 覆盖 FastAPI 的数据库依赖
    app.dependency_overrides[get_db] = _override_get_db

    # 创建所有表
    Base.metadata.create_all(bind=_test_engine)

    # 插入测试种子数据
    db = TestingSessionLocal()
    try:
        communities = [
            Community(
                name="万科城市花园", city="上海", district="浦东",
                address="浦东新区张杨路1000号",
                lat=31.2356, lng=121.5257, avg_price=55000,
                build_year=2010, total_units=2000,
                green_ratio=0.35, volume_ratio=2.5,
                property_company="万物云", property_fee=3.8, developer="万科",
            ),
            Community(
                name="绿城玫瑰园", city="上海", district="浦东",
                address="浦东新区花木路500号",
                lat=31.2156, lng=121.5457, avg_price=48000,
                build_year=2015, total_units=800,
                green_ratio=0.40, volume_ratio=1.8,
                property_company="绿城服务", property_fee=4.5, developer="绿城中国",
            ),
        ]
        db.add_all(communities)
        db.flush()

        schools = [
            SchoolDistrict(
                community_id=communities[0].id,
                primary_school="浦东实验小学", middle_school="建平中学",
                school_rank="区重点", year=2026,
            ),
            SchoolDistrict(
                community_id=communities[1].id,
                primary_school="明珠小学", middle_school="上海中学东校",
                school_rank="市重点", year=2026,
            ),
        ]
        db.add_all(schools)

        pois = [
            NearbyPOI(
                community_id=communities[0].id, category="地铁",
                name="2号线-张杨路站", distance=300, walk_time=4,
            ),
            NearbyPOI(
                community_id=communities[1].id, category="公园",
                name="世纪公园", distance=400, walk_time=5,
            ),
        ]
        db.add_all(pois)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    yield

    # 测试结束后清理
    Base.metadata.drop_all(bind=_test_engine)
    app.dependency_overrides.clear()


@pytest.fixture()
def client() -> TestClient:
    """返回使用测试数据库的 FastAPI TestClient。"""
    return TestClient(app)
