"""
搜索 API 测试模块

覆盖基础搜索、按区域搜索、自定义权重搜索以及默认权重配置查询接口。
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_returns_empty_for_no_data():
    """无数据时搜索应返回空结果"""
    response = client.post(
        "/api/v1/search",
        json={
            "city": "上海",
            "price_min": 30000,
            "price_max": 60000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["communities"] == []


def test_search_with_district():
    """指定区域搜索应正常返回"""
    response = client.post(
        "/api/v1/search",
        json={
            "city": "上海",
            "district": "浦东",
            "price_min": 30000,
            "price_max": 60000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["communities"] == []


def test_search_with_custom_weights():
    """自定义权重搜索应正常返回"""
    response = client.post(
        "/api/v1/search",
        json={
            "city": "上海",
            "price_min": 30000,
            "price_max": 60000,
            "weights": {
                "price": 0.40,
                "school": 0.20,
                "facilities": 0.15,
                "property_mgmt": 0.15,
                "developer": 0.10,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["communities"] == []


def test_get_default_weights():
    """获取默认权重配置应返回预设值"""
    response = client.get("/api/v1/config/weights")
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 0.3
    assert data["school"] == 0.25
    assert data["facilities"] == 0.2
    assert data["property_mgmt"] == 0.15
    assert data["developer"] == 0.1
