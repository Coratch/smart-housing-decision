"""
评分引擎单元测试

覆盖 ScoringEngine 的 5 个维度评分方法和总分计算，
确保各评分逻辑符合业务规则。
"""

import pytest

from app.core.scoring import ScoringEngine
from app.schemas.community import WeightsConfig


@pytest.fixture
def engine():
    """创建评分引擎实例"""
    return ScoringEngine()


class TestPriceScore:
    """单价评分测试"""

    def test_price_score_within_range(self, engine):
        """价格在预算范围内，评分应在 6~10 之间"""
        score = engine.calc_price_score(avg_price=40000, price_min=30000, price_max=50000)
        assert 6.0 <= score <= 10.0

    def test_price_score_at_min(self, engine):
        """价格等于预算下限，评分应 >= 8"""
        score = engine.calc_price_score(avg_price=30000, price_min=30000, price_max=50000)
        assert score >= 8.0

    def test_price_score_exceeds_max(self, engine):
        """价格超出预算上限的 1.2 倍，评分应 <= 3"""
        score = engine.calc_price_score(avg_price=65000, price_min=30000, price_max=50000)
        assert score <= 3.0


class TestSchoolScore:
    """学区评分测试"""

    def test_school_score_top_school(self, engine):
        """市重点学校评分应为 10"""
        score = engine.calc_school_score(school_rank="市重点")
        assert score == 10.0

    def test_school_score_no_school(self, engine):
        """无学区信息评分应为 0"""
        score = engine.calc_school_score(school_rank=None)
        assert score == 0.0


class TestFacilitiesScore:
    """周边配套评分测试"""

    def test_facilities_score(self, engine):
        """周边配套评分应在 0~10 范围内"""
        pois = [
            {"category": "地铁", "distance": 300},
            {"category": "医院", "distance": 800},
            {"category": "商场", "distance": 1500},
            {"category": "公园", "distance": 500},
            {"category": "学校", "distance": 2500},
        ]
        score = engine.calc_facilities_score(pois)
        assert 0.0 <= score <= 10.0


class TestPropertyScore:
    """物业评分测试"""

    def test_property_score_top_company(self, engine):
        """Top10 物业公司评分应 >= 7"""
        score = engine.calc_property_score(
            company="碧桂园服务",
            fee=3.5,
            green_ratio=0.40,
            volume_ratio=1.8,
        )
        assert score >= 7.0


class TestDeveloperScore:
    """开发商评分测试"""

    def test_developer_score_top10(self, engine):
        """Top10 开发商评分应 >= 8"""
        score = engine.calc_developer_score(developer="万科")
        assert score >= 8.0

    def test_developer_score_unknown(self, engine):
        """未知开发商评分应 <= 4"""
        score = engine.calc_developer_score(developer="某小开发商")
        assert score <= 4.0


class TestTotalScore:
    """总分计算测试"""

    def test_total_score(self, engine):
        """验证总分为各子评分的加权和"""
        sub_scores = {
            "price": 8.0,
            "school": 10.0,
            "facilities": 6.0,
            "property_mgmt": 7.0,
            "developer": 5.0,
        }
        weights = WeightsConfig(
            price=0.30,
            school=0.25,
            facilities=0.20,
            property_mgmt=0.15,
            developer=0.10,
        )
        total = engine.calc_total_score(sub_scores, weights)
        # 手动计算: 8*0.3 + 10*0.25 + 6*0.2 + 7*0.15 + 5*0.1 = 2.4+2.5+1.2+1.05+0.5 = 7.65
        assert abs(total - 7.65) < 0.01
