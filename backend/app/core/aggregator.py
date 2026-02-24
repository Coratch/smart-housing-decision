"""
数据聚合层

整合小区筛选、评分计算和优缺点分析，提供统一的搜索与排序入口。
作为 API 层和底层引擎之间的桥梁，将数据库查询、评分引擎、分析器
串联成完整的业务流程。

作者: smart-housing-decision
创建时间: 2026-02-24
"""

from typing import Dict, List, Optional

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.scoring import ScoringEngine
from app.core.analyzer import ProConAnalyzer
from app.models.community import Community, SchoolDistrict, NearbyPOI
from app.schemas.community import WeightsConfig


class DataAggregator:
    """
    数据聚合器

    职责：
    1. 按城市、区域、价格范围筛选小区
    2. 对单个小区进行多维度评分并生成优缺点
    3. 批量搜索并按总分降序排序
    """

    def __init__(self):
        self.scoring = ScoringEngine()
        self.analyzer = ProConAnalyzer()

    def filter_communities(
        self,
        db: Session,
        city: str,
        district: Optional[str],
        price_min: int,
        price_max: int,
    ) -> List[Community]:
        """
        按条件筛选小区

        Args:
            db: 数据库会话
            city: 城市名称（必填）
            district: 区域名称（选填，为 None 时不筛选区域）
            price_min: 价格下限（元/平米）
            price_max: 价格上限（元/平米）

        Returns:
            符合条件的小区列表
        """
        query = db.query(Community).filter(Community.city == city)

        if district:
            query = query.filter(Community.district == district)

        query = query.filter(
            Community.avg_price >= price_min,
            Community.avg_price <= price_max,
        )

        return query.all()

    def score_community(
        self,
        community: Community,
        school_rank: Optional[str],
        pois: List[Dict],
        price_min: int,
        price_max: int,
        weights: WeightsConfig,
    ) -> Dict:
        """
        对单个小区进行评分并生成优缺点分析

        Args:
            community: 小区 ORM 对象
            school_rank: 对口学校等级（市重点/区重点/普通/None）
            pois: 周边 POI 列表，每项包含 category 和 distance 字段
            price_min: 用户预算下限
            price_max: 用户预算上限
            weights: 评分权重配置

        Returns:
            包含 score、sub_scores、pros、cons、tags 的字典
        """
        # 计算各维度子评分
        sub_scores: Dict[str, float] = {
            "price": self.scoring.calc_price_score(
                avg_price=community.avg_price,
                price_min=price_min,
                price_max=price_max,
            ),
            "school": self.scoring.calc_school_score(school_rank=school_rank),
            "facilities": self.scoring.calc_facilities_score(pois=pois),
            "property_mgmt": self.scoring.calc_property_score(
                company=community.property_company,
                fee=community.property_fee,
                green_ratio=community.green_ratio,
                volume_ratio=community.volume_ratio,
            ),
            "developer": self.scoring.calc_developer_score(
                developer=community.developer,
            ),
        }

        # 计算加权总分（0~10），再映射到 0~100
        weighted_total = self.scoring.calc_total_score(sub_scores, weights)
        total_score = round(weighted_total * 10, 1)

        # 构建小区数据字典，供优缺点模板渲染使用
        community_data: Dict = {
            "avg_price": community.avg_price,
            "developer": community.developer,
            "property_company": community.property_company,
        }

        # 构建 POI 列表（适配 analyzer 的 type 字段）
        analyzer_pois: List[Dict] = []
        for poi in pois:
            analyzer_pois.append({
                "type": "subway" if poi.get("category") == "地铁" else poi.get("category", ""),
                "name": poi.get("name", ""),
                "distance": poi.get("distance"),
            })

        # 生成优缺点和标签
        analysis = self.analyzer.analyze(
            sub_scores=sub_scores,
            community_data=community_data,
            school_rank=school_rank,
            pois=analyzer_pois,
        )

        return {
            "score": total_score,
            "sub_scores": sub_scores,
            "pros": analysis["pros"],
            "cons": analysis["cons"],
            "tags": analysis["tags"],
        }

    def search_and_rank(
        self,
        db: Session,
        city: str,
        district: Optional[str],
        price_min: int,
        price_max: int,
        weights: WeightsConfig,
    ) -> List[Dict]:
        """
        搜索小区并按评分降序排序

        完整流程：
        1. 按条件筛选小区
        2. 为每个小区查询学区和 POI 信息
        3. 计算评分和优缺点
        4. 按总分降序排序返回

        Args:
            db: 数据库会话
            city: 城市名称
            district: 区域名称（可选）
            price_min: 价格下限
            price_max: 价格上限
            weights: 评分权重配置

        Returns:
            按评分降序排列的小区结果列表
        """
        # 筛选小区
        communities = self.filter_communities(
            db=db,
            city=city,
            district=district,
            price_min=price_min,
            price_max=price_max,
        )

        results: List[Dict] = []

        for community in communities:
            # 查询学区信息，取最新的一条记录的 school_rank
            # 使用 case 表达式处理 NULL 排序，兼容 SQLite（不支持 NULLS LAST）
            school_district = (
                db.query(SchoolDistrict)
                .filter(SchoolDistrict.community_id == community.id)
                .order_by(
                    case(
                        (SchoolDistrict.year.is_(None), 1),
                        else_=0,
                    ),
                    SchoolDistrict.year.desc(),
                )
                .first()
            )
            school_rank = school_district.school_rank if school_district else None

            # 查询周边 POI，转换为字典列表
            poi_records = (
                db.query(NearbyPOI)
                .filter(NearbyPOI.community_id == community.id)
                .all()
            )
            pois: List[Dict] = [
                {
                    "category": poi.category,
                    "name": poi.name,
                    "distance": poi.distance,
                }
                for poi in poi_records
            ]

            # 评分
            score_result = self.score_community(
                community=community,
                school_rank=school_rank,
                pois=pois,
                price_min=price_min,
                price_max=price_max,
                weights=weights,
            )

            results.append({
                "id": community.id,
                "name": community.name,
                "city": community.city,
                "district": community.district,
                "avg_price": community.avg_price,
                **score_result,
            })

        # 按评分降序排序
        results.sort(key=lambda x: x["score"], reverse=True)

        return results
