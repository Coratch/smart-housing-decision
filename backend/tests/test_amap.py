"""
高德地图 POI 服务单元测试

测试 AmapService 的 URL 构建和响应解析功能。
"""

import pytest

from app.services.amap import AmapService


class TestParsePoiResponse:
    """测试 parse_poi_response 方法：验证从高德 API 响应中正确解析 POI 数据。"""

    def setup_method(self):
        self.service = AmapService()

    def test_parse_poi_response_basic(self):
        """验证基础解析：name、distance 转 int、walk_time 计算。"""
        mock_data = {
            "status": "1",
            "pois": [
                {"name": "龙华地铁站", "distance": "320"},
                {"name": "深圳北站", "distance": "850"},
            ],
        }
        result = self.service.parse_poi_response(mock_data, "地铁")

        assert len(result) == 2

        # 第一个 POI
        assert result[0]["category"] == "地铁"
        assert result[0]["name"] == "龙华地铁站"
        assert result[0]["distance"] == 320
        assert isinstance(result[0]["distance"], int)
        # walk_time = 320 // 80 = 4
        assert result[0]["walk_time"] == 4

        # 第二个 POI
        assert result[1]["name"] == "深圳北站"
        assert result[1]["distance"] == 850
        # walk_time = 850 // 80 = 10
        assert result[1]["walk_time"] == 10

    def test_parse_poi_response_min_walk_time(self):
        """验证 walk_time 最小值为 1 分钟（距离很近时）。"""
        mock_data = {
            "status": "1",
            "pois": [
                {"name": "楼下便利店", "distance": "30"},
            ],
        }
        result = self.service.parse_poi_response(mock_data, "商场")

        assert result[0]["walk_time"] == 1

    def test_parse_poi_response_empty_pois(self):
        """验证无 POI 时返回空列表。"""
        mock_data = {"status": "1", "pois": []}
        result = self.service.parse_poi_response(mock_data, "医院")
        assert result == []

    def test_parse_poi_response_no_pois_key(self):
        """验证响应中缺少 pois 字段时返回空列表。"""
        mock_data = {"status": "1"}
        result = self.service.parse_poi_response(mock_data, "公园")
        assert result == []


class TestBuildSearchUrl:
    """测试 build_search_url 方法：验证 URL 构建正确性。"""

    def setup_method(self):
        self.service = AmapService()
        self.service.api_key = "test_api_key_123"

    def test_build_search_url_contains_keywords(self):
        """验证 URL 包含 keywords 参数。"""
        url = self.service.build_search_url(22.5, 114.0, "150500")
        assert "keywords" in url

    def test_build_search_url_contains_location(self):
        """验证 URL 包含 location 参数（经度,纬度格式）。"""
        url = self.service.build_search_url(22.5, 114.0, "150500")
        assert "location" in url
        # 高德格式: 经度,纬度
        assert "114.0%2C22.5" in url or "114.0,22.5" in url

    def test_build_search_url_contains_radius(self):
        """验证 URL 包含 radius 参数。"""
        url = self.service.build_search_url(22.5, 114.0, "150500", radius=2000)
        assert "radius=2000" in url

    def test_build_search_url_contains_api_key(self):
        """验证 URL 包含 key 参数。"""
        url = self.service.build_search_url(22.5, 114.0, "150500")
        assert "key=test_api_key_123" in url

    def test_build_search_url_default_radius(self):
        """验证默认 radius 为 1000。"""
        url = self.service.build_search_url(22.5, 114.0, "150500")
        assert "radius=1000" in url
