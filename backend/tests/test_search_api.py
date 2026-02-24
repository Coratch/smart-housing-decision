"""
搜索 API 测试模块

覆盖基础搜索、按区域搜索、自定义权重搜索以及默认权重配置查询接口。
使用不存在于数据库中的城市验证空结果场景，同时验证有数据时的正常返回。
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_returns_empty_for_no_data():
    """无数据城市搜索应返回空结果"""
    response = client.post(
        "/api/v1/search",
        json={
            "city": "北京",
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
            "city": "北京",
            "district": "朝阳",
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
            "city": "北京",
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


def test_search_returns_results_with_data():
    """有数据时搜索应返回包含评分和标签的结果"""
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
    assert data["total"] >= 1
    community = data["communities"][0]
    assert "score" in community
    assert "sub_scores" in community
    assert "pros" in community
    assert "cons" in community
    assert "tags" in community
    assert community["score"] > 0


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
