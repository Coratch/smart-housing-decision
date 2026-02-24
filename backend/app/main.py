"""
FastAPI 应用入口模块

提供应用实例初始化、CORS 中间件配置以及健康检查接口。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.search import router as search_router
from app.config import settings

app = FastAPI(title=settings.app_name)

# CORS 中间件 — 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册搜索 API 路由
app.include_router(search_router)


@app.get("/api/v1/health")
async def health_check():
    """健康检查接口，用于确认服务正常运行。"""
    return {"status": "ok"}
