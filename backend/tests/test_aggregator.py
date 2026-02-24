"""
数据聚合层单元测试

使用 SQLite 内存数据库验证 DataAggregator 的社区筛选、评分计算
和搜索排序功能是否正常工作。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.models.community import Community, SchoolDistrict, NearbyPOI
from app.schemas.community import WeightsConfig
from app.core.aggregator import DataAggregator


@pytest.fixture
def db_session():
    """创建内存数据库会话，测试结束后自动销毁。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def aggregator():
    """创建 DataAggregator 实例"""
    return DataAggregator()


class TestScoreCommunity:
    """社区评分测试"""

    def test_score_community(self, aggregator):
        """验证评分结果包含必要字段，且总分在 0~100 范围内"""
        community = Community(
            id=1,
            name="优质小区",
            city="上海",
            district="浦东新区",
            avg_price=50000,
            green_ratio=0.40,
            volume_ratio=1.8,
            property_company="碧桂园服务",
            property_fee=3.5,
            developer="万科",
        )

        school_rank = "市重点"

        pois = [
            {"category": "地铁", "distance": 300},
            {"category": "医院", "distance": 800},
            {"category": "商场", "distance": 500},
            {"category": "公园", "distance": 400},
        ]

        weights = WeightsConfig()

        result = aggregator.score_community(
            community=community,
            school_rank=school_rank,
            pois=pois,
            price_min=40000,
            price_max=60000,
            weights=weights,
        )

        # 验证结果包含必要的字段
        assert "score" in result
        assert "sub_scores" in result
        assert "pros" in result
        assert "cons" in result

        # 验证总分在 0~100 范围内（总分 = 加权和 * 10）
        assert 0 <= result["score"] <= 100

        # 验证子评分字典包含所有维度
        sub_scores = result["sub_scores"]
        assert "price" in sub_scores
        assert "school" in sub_scores
        assert "facilities" in sub_scores
        assert "property_mgmt" in sub_scores
        assert "developer" in sub_scores

        # 各维度评分应在 0~10 范围内
        for dimension, score in sub_scores.items():
            assert 0 <= score <= 10, f"{dimension} 评分 {score} 超出范围"

        # 优缺点应为列表
        assert isinstance(result["pros"], list)
        assert isinstance(result["cons"], list)


class TestFilterCommunities:
    """社区筛选测试"""

    def test_filter_communities(self, aggregator, db_session):
        """验证按城市和价格范围筛选社区"""
        # 创建 3 个不同城市/价格的小区
        communities = [
            Community(
                name="上海浦东小区",
                city="上海",
                district="浦东新区",
                avg_price=50000,
            ),
            Community(
                name="上海徐汇小区",
                city="上海",
                district="徐汇区",
                avg_price=80000,
            ),
            Community(
                name="北京朝阳小区",
                city="北京",
                district="朝阳区",
                avg_price=60000,
            ),
        ]
        db_session.add_all(communities)
        db_session.commit()

        # 筛选上海、价格 40000~70000
        results = aggregator.filter_communities(
            db=db_session,
            city="上海",
            district=None,
            price_min=40000,
            price_max=70000,
        )

        # 应只返回"上海浦东小区"（上海 + 50000 在范围内）
        assert len(results) == 1
        assert results[0].name == "上海浦东小区"

    def test_filter_communities_with_district(self, aggregator, db_session):
        """验证按城市 + 区域筛选"""
        communities = [
            Community(
                name="浦东A",
                city="上海",
                district="浦东新区",
                avg_price=50000,
            ),
            Community(
                name="徐汇A",
                city="上海",
                district="徐汇区",
                avg_price=55000,
            ),
        ]
        db_session.add_all(communities)
        db_session.commit()

        results = aggregator.filter_communities(
            db=db_session,
            city="上海",
            district="浦东新区",
            price_min=40000,
            price_max=70000,
        )

        assert len(results) == 1
        assert results[0].name == "浦东A"


class TestSearchAndRank:
    """搜索与排序集成测试"""

    def test_search_and_rank(self, aggregator, db_session):
        """验证搜索结果按评分降序排列"""
        # 创建两个小区，一个更优质
        c1 = Community(
            name="普通小区",
            city="上海",
            district="浦东新区",
            avg_price=50000,
            green_ratio=0.20,
            volume_ratio=3.5,
            property_company=None,
            developer=None,
        )
        c2 = Community(
            name="优质小区",
            city="上海",
            district="浦东新区",
            avg_price=55000,
            green_ratio=0.40,
            volume_ratio=1.8,
            property_company="碧桂园服务",
            developer="万科",
        )
        db_session.add_all([c1, c2])
        db_session.commit()
        db_session.refresh(c1)
        db_session.refresh(c2)

        # 给优质小区添加学区信息
        school = SchoolDistrict(
            community_id=c2.id,
            primary_school="上海市实验小学",
            school_rank="市重点",
        )
        db_session.add(school)

        # 给优质小区添加周边 POI
        poi = NearbyPOI(
            community_id=c2.id,
            category="地铁",
            name="世纪大道站",
            distance=300,
        )
        db_session.add(poi)
        db_session.commit()

        weights = WeightsConfig()
        results = aggregator.search_and_rank(
            db=db_session,
            city="上海",
            district=None,
            price_min=40000,
            price_max=70000,
            weights=weights,
        )

        # 应返回 2 个结果
        assert len(results) == 2

        # 结果应按评分降序排列
        assert results[0]["score"] >= results[1]["score"]

        # 优质小区应排在前面
        assert results[0]["name"] == "优质小区"

        # 每个结果都应有完整结构
        for r in results:
            assert "id" in r
            assert "name" in r
            assert "score" in r
            assert "sub_scores" in r
            assert "pros" in r
            assert "cons" in r
            assert "tags" in r
