"""
优缺点分析引擎单元测试

验证 ProConAnalyzer 的核心逻辑：
- 根据维度得分自动归类为优点或缺点
- 根据小区数据和 POI 信息自动生成标签
"""

import pytest

from app.core.analyzer import ProConAnalyzer


@pytest.fixture
def analyzer():
    return ProConAnalyzer()


class TestProConAnalysis:
    """优缺点分析测试"""

    def test_high_score_is_pro(self, analyzer):
        """
        维度得分 >= 8 应归为优点，得分 <= 4 应归为缺点。
        price=9 → "性价比" 出现在 pros 中
        developer=2 → "开发商" 出现在 cons 中
        """
        sub_scores = {
            "price": 9,
            "school": 6,
            "facilities": 5,
            "property_mgmt": 7,
            "developer": 2,
        }
        community_data = {
            "avg_price": 35000,
            "developer": "某小开发商",
            "property_company": "某物业",
        }

        result = analyzer.analyze(sub_scores, community_data)

        # 验证返回结构包含 pros、cons、tags 三个字段
        assert "pros" in result
        assert "cons" in result
        assert "tags" in result

        # price=9 >= 8，应出现在优点中，包含"性价比"关键词
        pro_texts = " ".join(result["pros"])
        assert "性价比" in pro_texts

        # developer=2 <= 4，应出现在缺点中，包含"开发商"关键词
        con_texts = " ".join(result["cons"])
        assert "开发商" in con_texts

        # school=6, facilities=5, property_mgmt=7 处于中间区间，不应出现在优缺点中
        assert not any("学区" in p for p in result["pros"])
        assert not any("学区" in c for c in result["cons"])

    def test_tags_generated(self, analyzer):
        """
        school_rank=市重点 → tags 包含 "市重点学区"
        subway POI distance=200m → tags 包含 "地铁旁"
        """
        sub_scores = {
            "price": 9,
            "school": 9,
            "facilities": 5,
            "property_mgmt": 5,
            "developer": 5,
        }
        community_data = {
            "avg_price": 28000,
            "developer": "万科",
            "property_company": "万科物业",
        }
        pois = [
            {"type": "subway", "name": "地铁2号线-南京西路站", "distance": 200},
            {"type": "hospital", "name": "华山医院", "distance": 1500},
        ]

        result = analyzer.analyze(
            sub_scores,
            community_data,
            school_rank="市重点",
            pois=pois,
        )

        assert "市重点学区" in result["tags"]
        assert "地铁旁" in result["tags"]

    def test_district_school_tag(self, analyzer):
        """school_rank=区重点 → tags 包含 "区重点学区" """
        sub_scores = {
            "price": 5,
            "school": 7,
            "facilities": 5,
            "property_mgmt": 5,
            "developer": 5,
        }
        community_data = {"avg_price": 40000}

        result = analyzer.analyze(
            sub_scores, community_data, school_rank="区重点"
        )

        assert "区重点学区" in result["tags"]

    def test_high_price_score_tag(self, analyzer):
        """price >= 8 → tags 包含 "高性价比" """
        sub_scores = {
            "price": 8,
            "school": 5,
            "facilities": 5,
            "property_mgmt": 5,
            "developer": 5,
        }
        community_data = {"avg_price": 25000}

        result = analyzer.analyze(sub_scores, community_data)

        assert "高性价比" in result["tags"]

    def test_no_subway_tag_when_far(self, analyzer):
        """地铁距离 > 500m 时不应生成 "地铁旁" 标签"""
        sub_scores = {
            "price": 5,
            "school": 5,
            "facilities": 5,
            "property_mgmt": 5,
            "developer": 5,
        }
        community_data = {"avg_price": 40000}
        pois = [
            {"type": "subway", "name": "地铁站", "distance": 800},
        ]

        result = analyzer.analyze(
            sub_scores, community_data, pois=pois
        )

        assert "地铁旁" not in result["tags"]
