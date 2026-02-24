"""
优缺点分析引擎

根据各维度评分和小区数据，自动生成优缺点描述和标签。
评分 >= 8 的维度归为优点，评分 <= 4 的维度归为缺点，中间区间不做判断。

作者: smart-housing-decision
创建时间: 2026-02-24
"""

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# 维度中文名称映射
# ---------------------------------------------------------------------------
DIMENSION_NAMES: Dict[str, str] = {
    "price": "性价比",
    "school": "学区质量",
    "facilities": "周边配套",
    "property_mgmt": "物业品质",
    "developer": "开发商信誉",
}

# ---------------------------------------------------------------------------
# 优点模板 —— 当维度得分 >= 8 时使用
# ---------------------------------------------------------------------------
PRO_TEMPLATES: Dict[str, str] = {
    "price": "性价比高，均价 {avg_price} 元/㎡",
    "school": "对口优质学校",
    "facilities": "周边配套齐全",
    "property_mgmt": "物业管理品质优良（{property_company}）",
    "developer": "知名开发商（{developer}）",
}

# ---------------------------------------------------------------------------
# 缺点模板 —— 当维度得分 <= 4 时使用
# ---------------------------------------------------------------------------
CON_TEMPLATES: Dict[str, str] = {
    "price": "价格偏高，均价 {avg_price} 元/㎡",
    "school": "学区一般或无对口学校",
    "facilities": "周边配套不足",
    "property_mgmt": "物业管理品质较低",
    "developer": "开发商知名度不高",
}

# 优点判定阈值
PRO_THRESHOLD: int = 8
# 缺点判定阈值
CON_THRESHOLD: int = 4
# 地铁"旁"的最大距离（米）
SUBWAY_NEARBY_DISTANCE: int = 500


class ProConAnalyzer:
    """
    优缺点分析器

    职责：
    1. 根据各维度子评分（sub_scores）将维度归类为优点或缺点
    2. 根据学区等级、POI 距离等信息生成快捷标签
    """

    def analyze(
        self,
        sub_scores: Dict[str, float],
        community_data: Dict,
        school_rank: Optional[str] = None,
        pois: Optional[List[Dict]] = None,
    ) -> Dict[str, List[str]]:
        """
        执行优缺点分析。

        参数:
            sub_scores: 各维度得分，key 为维度名（price/school/facilities/property_mgmt/developer），
                        value 为 0-10 的评分
            community_data: 小区基础数据，可包含 avg_price、developer、property_company 等字段
            school_rank: 学校等级，如 "市重点"、"区重点" 等
            pois: POI 列表，每个元素为 {"type": str, "name": str, "distance": float(米)}

        返回:
            {"pros": [...], "cons": [...], "tags": [...]}
        """
        pros = self._collect_pros(sub_scores, community_data)
        cons = self._collect_cons(sub_scores, community_data)
        tags = self._generate_tags(sub_scores, school_rank, pois)

        return {"pros": pros, "cons": cons, "tags": tags}

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _collect_pros(
        self,
        sub_scores: Dict[str, float],
        community_data: Dict,
    ) -> List[str]:
        """收集得分 >= PRO_THRESHOLD 的维度，填充优点模板。"""
        pros: List[str] = []
        for dimension, score in sub_scores.items():
            if score >= PRO_THRESHOLD and dimension in PRO_TEMPLATES:
                text = self._render_template(
                    PRO_TEMPLATES[dimension], community_data
                )
                pros.append(text)
        return pros

    def _collect_cons(
        self,
        sub_scores: Dict[str, float],
        community_data: Dict,
    ) -> List[str]:
        """收集得分 <= CON_THRESHOLD 的维度，填充缺点模板。"""
        cons: List[str] = []
        for dimension, score in sub_scores.items():
            if score <= CON_THRESHOLD and dimension in CON_TEMPLATES:
                text = self._render_template(
                    CON_TEMPLATES[dimension], community_data
                )
                cons.append(text)
        return cons

    @staticmethod
    def _render_template(template: str, data: Dict) -> str:
        """
        安全渲染模板字符串。

        如果 data 中缺少模板所需的 key，则用 "未知" 替代，避免 KeyError。
        """
        try:
            return template.format_map(
                _DefaultDict(data)
            )
        except (KeyError, ValueError):
            return template

    @staticmethod
    def _generate_tags(
        sub_scores: Dict[str, float],
        school_rank: Optional[str],
        pois: Optional[List[Dict]],
    ) -> List[str]:
        """
        根据业务规则生成标签列表。

        规则：
        - school_rank 为 "市重点" → 添加 "市重点学区"
        - school_rank 为 "区重点" → 添加 "区重点学区"
        - POI 中存在 type=subway 且 distance <= 500m → 添加 "地铁旁"
        - price 维度得分 >= 8 → 添加 "高性价比"
        """
        tags: List[str] = []

        # 学区标签
        if school_rank == "市重点":
            tags.append("市重点学区")
        elif school_rank == "区重点":
            tags.append("区重点学区")

        # 地铁标签
        if pois:
            for poi in pois:
                if (
                    poi.get("type") == "subway"
                    and poi.get("distance", float("inf")) <= SUBWAY_NEARBY_DISTANCE
                ):
                    tags.append("地铁旁")
                    break  # 只要有一个地铁站在范围内即可

        # 高性价比标签
        if sub_scores.get("price", 0) >= PRO_THRESHOLD:
            tags.append("高性价比")

        return tags


class _DefaultDict(dict):
    """
    继承 dict，在 format_map 找不到 key 时返回 "未知" 而非抛异常。

    仅用于模板渲染，避免因小区数据字段缺失导致整条优缺点丢失。
    """

    def __missing__(self, key: str) -> str:
        return "未知"
