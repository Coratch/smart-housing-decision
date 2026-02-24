"""
小区详情 API 路由模块

提供小区详情查询接口，返回小区基本信息、学区信息、
周边 POI 以及综合评分。
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.aggregator import DataAggregator
from app.models.community import Community, NearbyPOI, SchoolDistrict
from app.models.database import get_db
from app.schemas.community import (
    CommunityDetail,
    POIResponse,
    SchoolDistrictResponse,
    SubScores,
    WeightsConfig,
)

router = APIRouter(prefix="/api/v1", tags=["community"])

aggregator = DataAggregator()


@router.get("/community/{community_id}", response_model=CommunityDetail)
async def get_community_detail(
    community_id: int,
    db: Session = Depends(get_db),
):
    """
    小区详情接口

    根据小区 ID 查询完整信息，包括学区、周边 POI 及综合评分。
    如果小区不存在则返回 404。
    """
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="小区不存在")

    # 查询学区信息
    school_districts = (
        db.query(SchoolDistrict)
        .filter(SchoolDistrict.community_id == community_id)
        .all()
    )

    # 取最新学区记录的 school_rank 用于评分
    school_rank = None
    if school_districts:
        # 按 year 降序取第一条，None 排最后
        sorted_districts = sorted(
            school_districts,
            key=lambda sd: (sd.year is None, -(sd.year or 0)),
        )
        school_rank = sorted_districts[0].school_rank

    # 查询周边 POI
    poi_records = (
        db.query(NearbyPOI)
        .filter(NearbyPOI.community_id == community_id)
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

    # 使用默认权重和价格范围进行评分
    # 价格范围设为小区均价的 ±30%，确保评分合理
    avg_price = community.avg_price or 0
    price_min = int(avg_price * 0.7)
    price_max = int(avg_price * 1.3) if avg_price > 0 else 100000

    score_result = aggregator.score_community(
        community=community,
        school_rank=school_rank,
        pois=pois,
        price_min=price_min,
        price_max=price_max,
        weights=WeightsConfig(),
    )

    return CommunityDetail(
        id=community.id,
        name=community.name,
        city=community.city,
        district=community.district,
        address=community.address,
        avg_price=community.avg_price,
        build_year=community.build_year,
        total_units=community.total_units,
        green_ratio=community.green_ratio,
        volume_ratio=community.volume_ratio,
        property_company=community.property_company,
        property_fee=community.property_fee,
        developer=community.developer,
        parking_ratio=community.parking_ratio,
        score=score_result["score"],
        sub_scores=SubScores(**score_result["sub_scores"]),
        pros=score_result["pros"],
        cons=score_result["cons"],
        school_districts=[
            SchoolDistrictResponse(
                primary_school=sd.primary_school,
                middle_school=sd.middle_school,
                school_rank=sd.school_rank,
                year=sd.year,
            )
            for sd in school_districts
        ],
        nearby_pois=[
            POIResponse(
                category=poi.category,
                name=poi.name,
                distance=poi.distance,
                walk_time=poi.walk_time,
            )
            for poi in poi_records
        ],
    )
