"""
小区相关的 Pydantic Schema 定义

包含搜索请求/响应、权重配置、小区摘要与详情等数据模型，
用于 API 层的请求校验与响应序列化。
"""

from typing import Optional, List

from pydantic import BaseModel, Field


class WeightsConfig(BaseModel):
    """评分权重配置，各维度权重之和建议为 1.0"""

    price: float = Field(default=0.30, ge=0, le=1)
    school: float = Field(default=0.25, ge=0, le=1)
    facilities: float = Field(default=0.20, ge=0, le=1)
    property_mgmt: float = Field(default=0.15, ge=0, le=1)
    developer: float = Field(default=0.10, ge=0, le=1)


class SearchRequest(BaseModel):
    """小区搜索请求参数"""

    city: str
    district: Optional[str] = None
    price_min: int
    price_max: int
    weights: WeightsConfig = WeightsConfig()


class SubScores(BaseModel):
    """各维度子评分"""

    price: float
    school: float
    facilities: float
    property_mgmt: float
    developer: float


class CommunityBrief(BaseModel):
    """小区摘要信息，用于搜索结果列表展示"""

    id: int
    name: str
    city: str
    district: Optional[str]
    avg_price: Optional[int]
    score: float
    sub_scores: SubScores
    pros: List[str]
    cons: List[str]
    tags: List[str]

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """搜索响应结果"""

    total: int
    communities: List[CommunityBrief]


class POIResponse(BaseModel):
    """周边 POI 信息"""

    category: str
    name: str
    distance: Optional[int]
    walk_time: Optional[int]


class SchoolDistrictResponse(BaseModel):
    """学区信息"""

    primary_school: Optional[str]
    middle_school: Optional[str]
    school_rank: Optional[str]
    year: Optional[int]


class CommunityDetail(BaseModel):
    """小区详情信��，包含学区和周边 POI"""

    id: int
    name: str
    city: str
    district: Optional[str]
    address: Optional[str]
    avg_price: Optional[int]
    build_year: Optional[int]
    total_units: Optional[int]
    green_ratio: Optional[float]
    volume_ratio: Optional[float]
    property_company: Optional[str]
    property_fee: Optional[float]
    developer: Optional[str]
    parking_ratio: Optional[str]
    score: float
    sub_scores: SubScores
    pros: List[str]
    cons: List[str]
    school_districts: List[SchoolDistrictResponse]
    nearby_pois: List[POIResponse]

    class Config:
        from_attributes = True
