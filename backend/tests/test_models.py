"""
数据库模型单元测试

使用 SQLite 内存数据库验证 Community、SchoolDistrict、NearbyPOI 模型的
创建及外键关联是否正常工作。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.models.community import Community, SchoolDistrict, NearbyPOI


@pytest.fixture
def db_session():
    """创建内存数据库会话，测试结束后自动销毁。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_create_community(db_session):
    """验证 Community 创建后能正确分配主键 ID。"""
    community = Community(
        name="测试小区",
        city="上海",
        district="浦东新区",
        address="世纪大道100号",
        avg_price=65000,
        build_year=2010,
    )
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)

    assert community.id is not None
    assert community.name == "测试小区"
    assert community.city == "上海"
    assert community.district == "浦东新区"
    assert community.avg_price == 65000


def test_create_school_district(db_session):
    """验证 SchoolDistrict 与 Community 之间的外键关联正确。"""
    community = Community(name="学区房小区", city="上海", district="徐汇区")
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)

    school = SchoolDistrict(
        community_id=community.id,
        primary_school="上海市实验小学",
        middle_school="上海市南模中学",
        school_rank="市重点",
        year=2025,
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)

    assert school.id is not None
    assert school.community_id == community.id
    assert school.primary_school == "上海市实验小学"
    assert school.school_rank == "市重点"
    # 验证关联关系
    assert school.community.name == "学区房小区"
    assert len(community.school_districts) == 1


def test_create_nearby_poi(db_session):
    """验证 NearbyPOI 与 Community 之间的外键关联正确。"""
    community = Community(name="地铁房小区", city="上海", district="闵行区")
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)

    poi = NearbyPOI(
        community_id=community.id,
        category="地铁",
        name="莘庄站",
        distance=500,
        walk_time=7,
    )
    db_session.add(poi)
    db_session.commit()
    db_session.refresh(poi)

    assert poi.id is not None
    assert poi.community_id == community.id
    assert poi.category == "地铁"
    assert poi.name == "莘庄站"
    assert poi.distance == 500
    assert poi.walk_time == 7
    # 验证关联关系
    assert poi.community.name == "地铁房小区"
    assert len(community.nearby_pois) == 1
