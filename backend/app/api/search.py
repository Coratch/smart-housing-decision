"""
搜索 API 路由模块

提供小区搜索接口和默认权重配置查询接口。
通过 DataAggregator 聚合层完成筛选、评分和排序。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.aggregator import DataAggregator
from app.models.database import get_db
from app.schemas.community import (
    CommunityBrief,
    SearchRequest,
    SearchResponse,
    SubScores,
    WeightsConfig,
)

router = APIRouter(prefix="/api/v1", tags=["search"])

aggregator = DataAggregator()


@router.post("/search", response_model=SearchResponse)
async def search_communities(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
    """
    小区搜索接口

    根据城市、区域、价格区间和权重配置搜索匹配的小区，
    返回按综合评分降序排列的结果列表。
    """
    results = aggregator.search_and_rank(
        db=db,
        city=request.city,
        district=request.district,
        price_min=request.price_min,
        price_max=request.price_max,
        weights=request.weights,
    )

    communities = [
        CommunityBrief(
            id=item["id"],
            name=item["name"],
            city=item["city"],
            district=item.get("district"),
            avg_price=item.get("avg_price"),
            score=item["score"],
            sub_scores=SubScores(**item["sub_scores"]),
            pros=item["pros"],
            cons=item["cons"],
            tags=item["tags"],
        )
        for item in results
    ]

    return SearchResponse(total=len(communities), communities=communities)


@router.get("/config/weights", response_model=WeightsConfig)
async def get_default_weights():
    """获取默认评分权重配置"""
    return WeightsConfig()
