"""
加权评分引擎

提供 5 个维度的评分计算（单价、学区、配套设施、物业管理、开发商），
以及根据用户自定义权重计算总分的能力。

每个维度评分范围为 0~10 分，总分为各维度加权和。
"""

import json
import os
from typing import Dict, List, Optional

from app.schemas.community import WeightsConfig

# 数据文件所在目录
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _load_json(filename: str) -> dict:
    """加载 data 目录下的 JSON 文件"""
    filepath = os.path.join(_DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# 模块级别加载排名数据，避免每次调用重复读取文件
_PROPERTY_RANKS = _load_json("property_ranks.json")
_DEVELOPER_RANKS = _load_json("developer_ranks.json")


class ScoringEngine:
    """
    小区评分引擎

    支持 5 个维度的独立评分和加权总分计算：
    - 单价评分：基于用户预算区间的价格竞争力
    - 学区评分：基于对口学校等级
    - 配套设施评分：基于周边 POI 的距离加权评分
    - 物业管理评分：基于物业公司排名和小区指标
    - 开发商评分：基于开发商品牌排名
    """

    # 配套设施类别权重
    CATEGORY_WEIGHTS: Dict[str, float] = {
        "地铁": 3.0,
        "医院": 2.0,
        "商场": 2.0,
        "公园": 1.5,
        "学校": 1.5,
    }

    def calc_price_score(
        self,
        avg_price: Optional[int],
        price_min: int,
        price_max: int,
    ) -> float:
        """
        计算单价评分

        评分逻辑：
        - 无价格信息 → 5.0（中性分）
        - 低于预算下限 → 10.0（价格非常有竞争力）
        - 在预算范围内 → 6.0~10.0（线性映射）
        - 超出预算上限但未超 1.2 倍 → 1.0~4.0（线性递减）
        - 超出预算上限 1.2 倍及以上 → 1.0（严重超预算）

        Args:
            avg_price: 小区均价（元/平米），可能为 None
            price_min: 用户预算下限
            price_max: 用户预算上限

        Returns:
            0~10 的浮点数评分
        """
        if avg_price is None:
            return 5.0

        if avg_price <= price_min:
            return 10.0

        upper_bound = price_max * 1.2
        if avg_price >= upper_bound:
            return 1.0

        if avg_price > price_max:
            # 超出预算上限但未超 1.2 倍，线性从 4.0 递减到 1.0
            ratio = (avg_price - price_max) / (upper_bound - price_max)
            return 4.0 - ratio * 3.0

        # 在预算范围内，线性从 10.0 递减到 6.0
        price_range = price_max - price_min
        if price_range == 0:
            return 10.0
        ratio = (avg_price - price_min) / price_range
        return 10.0 - ratio * 4.0

    def calc_school_score(self, school_rank: Optional[str]) -> float:
        """
        计算学区评分

        Args:
            school_rank: 学校等级（市重点/区重点/普通），None 表示无学区信息

        Returns:
            0~10 的浮点数评分
        """
        rank_map: Dict[str, float] = {
            "市重点": 10.0,
            "区重点": 7.0,
            "普通": 5.0,
        }
        if school_rank is None:
            return 0.0
        return rank_map.get(school_rank, 0.0)

    def calc_facilities_score(self, pois: List[dict]) -> float:
        """
        计算周边配套设施评分

        根据各类 POI 的距离进行评分，按类别权重加权平均。
        同一类别有多个 POI 时取最高分。

        距离评分规则：
        - <= 500m → 10 分
        - <= 1000m → 7 分
        - <= 2000m → 4 分
        - > 2000m → 1 分

        Args:
            pois: POI 信息列表，每项包含 category 和 distance 字段

        Returns:
            0~10 的浮点数评分
        """
        if not pois:
            return 0.0

        # 按类别分组，取每个类别的最佳距离评分
        category_best_scores: Dict[str, float] = {}
        for poi in pois:
            category = poi.get("category", "")
            distance = poi.get("distance")
            if distance is None:
                continue

            score = self._distance_to_score(distance)

            if category not in category_best_scores or score > category_best_scores[category]:
                category_best_scores[category] = score

        if not category_best_scores:
            return 0.0

        # 加权平均
        total_weight = 0.0
        weighted_sum = 0.0
        for category, score in category_best_scores.items():
            weight = self.CATEGORY_WEIGHTS.get(category, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        result = weighted_sum / total_weight
        return min(result, 10.0)

    @staticmethod
    def _distance_to_score(distance: int) -> float:
        """
        将距离转换为评分

        Args:
            distance: 距离（米）

        Returns:
            评分值
        """
        if distance <= 500:
            return 10.0
        elif distance <= 1000:
            return 7.0
        elif distance <= 2000:
            return 4.0
        else:
            return 1.0

    def calc_property_score(
        self,
        company: Optional[str],
        fee: Optional[float],
        green_ratio: Optional[float],
        volume_ratio: Optional[float],
    ) -> float:
        """
        计算物业管理评分

        基础分 5.0，根据物业公司排名和小区指标进行加减分：
        - Top10 物业公司 → +3.0
        - Top50 物业公司 → +1.5
        - 绿化率 >= 0.35 → +1.0
        - 绿化率 < 0.2 → -1.0
        - 容积率 <= 2.0 → +1.0（居住舒适度高）
        - 容积率 > 4.0 → -1.0（居住密度过高）

        Args:
            company: 物业公司名称
            fee: 物业费（元/平米/月）
            green_ratio: 绿化率
            volume_ratio: 容积率

        Returns:
            0~10 的浮点数评分
        """
        score = 5.0

        # 物业公司排名加分
        if company:
            if company in _PROPERTY_RANKS.get("top10", []):
                score += 3.0
            elif company in _PROPERTY_RANKS.get("top50", []):
                score += 1.5

        # 绿化率调整
        if green_ratio is not None:
            if green_ratio >= 0.35:
                score += 1.0
            elif green_ratio < 0.2:
                score -= 1.0

        # 容积率调整
        if volume_ratio is not None:
            if volume_ratio <= 2.0:
                score += 1.0
            elif volume_ratio > 4.0:
                score -= 1.0

        # 确保评分在 0~10 范围内
        return max(0.0, min(score, 10.0))

    def calc_developer_score(self, developer: Optional[str]) -> float:
        """
        计算开发商评分

        Args:
            developer: 开发商名称，None 表示无信息

        Returns:
            0~10 的浮点数评分
        """
        if developer is None:
            return 3.0

        if developer in _DEVELOPER_RANKS.get("top10", []):
            return 10.0

        if developer in _DEVELOPER_RANKS.get("top50", []):
            return 7.0

        return 3.0

    def calc_total_score(
        self,
        sub_scores: Dict[str, float],
        weights: WeightsConfig,
    ) -> float:
        """
        计算加权总分

        Args:
            sub_scores: 各维度子评分字典，键为维度名称，值为评分
            weights: 权重配置

        Returns:
            加权总分
        """
        total = (
            sub_scores.get("price", 0.0) * weights.price
            + sub_scores.get("school", 0.0) * weights.school
            + sub_scores.get("facilities", 0.0) * weights.facilities
            + sub_scores.get("property_mgmt", 0.0) * weights.property_mgmt
            + sub_scores.get("developer", 0.0) * weights.developer
        )
        return round(total, 2)
