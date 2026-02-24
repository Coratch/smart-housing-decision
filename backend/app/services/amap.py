"""
高德地图 POI 服务模块

封装高德地图周边搜索 API，支持按分类批量查询 POI 信息，
用于评估小区周边配套设施（地铁、医院、商场、公园、学校）。
"""

from typing import Dict, List
from urllib.parse import urlencode

import httpx

from app.config import settings


# 高德 POI 分类编码映射
# 参考：https://lbs.amap.com/api/webservice/download
CATEGORY_TYPES: Dict[str, str] = {
    "地铁": "150500",
    "医院": "090100",
    "商场": "060100|060200",
    "公园": "110200",
    "学校": "141200",
}


class AmapService:
    """
    高德地图 POI 周边搜索服务

    提供基于经纬度的周边 POI 搜索能力，支持地铁、医院、商场、公园、学校等
    多种分类的批量查询和结果解析。

    Attributes:
        api_key: 高德地图 Web 服务 API 密钥
        client: httpx 异步 HTTP 客户端
    """

    BASE_URL = "https://restapi.amap.com/v3/place/around"

    def __init__(self) -> None:
        """初始化服务，从应用配置加载 API Key 并创建 HTTP 客户端。"""
        self.api_key: str = settings.amap_api_key
        self.client: httpx.AsyncClient = httpx.AsyncClient(timeout=10.0)

    def build_search_url(
        self,
        lat: float,
        lng: float,
        keywords: str,
        radius: int = 1000,
    ) -> str:
        """
        构建高德周边搜索请求 URL

        Args:
            lat: 纬度
            lng: 经度
            keywords: POI 分类编码（如 150500）
            radius: 搜索半径，单位米，默认 1000

        Returns:
            完整的请求 URL 字符串
        """
        params = {
            "key": self.api_key,
            "location": f"{lng},{lat}",
            "keywords": keywords,
            "radius": radius,
            "output": "json",
            "extensions": "base",
        }
        return f"{self.BASE_URL}?{urlencode(params)}"

    def parse_poi_response(self, data: dict, category: str) -> List[dict]:
        """
        解析高德 API 响应中的 POI 数据

        将原始响应转换为标准化的 POI 列表，包含分类、名称、距离和步行时间。
        步行时间按 80 米/分钟估算，最小值为 1 分钟。

        Args:
            data: 高德 API 原始响应字典
            category: POI 分类中文名（如 "地铁"、"医院"）

        Returns:
            解析后的 POI 字典列表，每项包含 category、name、distance、walk_time
        """
        pois = data.get("pois", [])
        result: List[dict] = []

        for poi in pois:
            distance = int(poi["distance"])
            walk_time = max(distance // 80, 1)

            result.append({
                "category": category,
                "name": poi["name"],
                "distance": distance,
                "walk_time": walk_time,
            })

        return result

    async def search_nearby(
        self,
        lat: float,
        lng: float,
        category: str,
        radius: int = 1000,
    ) -> List[dict]:
        """
        异步搜索指定分类的周边 POI

        Args:
            lat: 纬度
            lng: 经度
            category: POI 分类中文名（需在 CATEGORY_TYPES 中定义）
            radius: 搜索半径，单位米，默认 1000

        Returns:
            解析后的 POI 列表；若无 API Key 或分类不存在则返回空列表
        """
        if not self.api_key:
            return []

        keywords = CATEGORY_TYPES.get(category)
        if keywords is None:
            return []

        url = self.build_search_url(lat, lng, keywords, radius)
        response = await self.client.get(url)
        data = response.json()

        return self.parse_poi_response(data, category)

    async def search_all_categories(
        self,
        lat: float,
        lng: float,
    ) -> List[dict]:
        """
        异步搜索所有分类的周边 POI

        遍历 CATEGORY_TYPES 中定义的所有分类，逐一调用周边搜索并汇总结果。

        Args:
            lat: 纬度
            lng: 经度

        Returns:
            所有分类的 POI 合并列表
        """
        all_pois: List[dict] = []

        for category in CATEGORY_TYPES:
            pois = await self.search_nearby(lat, lng, category)
            all_pois.extend(pois)

        return all_pois

    async def close(self) -> None:
        """关闭 HTTP 客户端，释放连接资源。"""
        await self.client.aclose()
