"""
健康检查接口测试

验证 GET /api/v1/health 返回 200 状态码及 {"status": "ok"} 响应体。
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    """测试健康检查接口返回正确的状态码和响应内容。"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
