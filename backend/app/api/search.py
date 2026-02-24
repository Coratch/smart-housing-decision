"""
搜索 API 路由模块

提供小区搜索接口和默认权重配置查询接口。
当前为骨架实现，将在 Task 9 中接入聚合评分逻辑。
"""

from fastapi import APIRouter

from app.schemas.community import SearchRequest, SearchResponse, WeightsConfig

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_communities(request: SearchRequest):
    """
    小区搜索接口

    根据城市、区域、价格区间和权重配置搜索匹配的小区。
    当前为占位实现，将在 Task 9 中接入聚合评分服务。
    """
    # Placeholder - will be connected to aggregator in Task 9
    return SearchResponse(total=0, communities=[])


@router.get("/config/weights", response_model=WeightsConfig)
async def get_default_weights():
    """获取默认评分权重配置"""
    return WeightsConfig()
