"""
FastAPI 应用入口模块

提供应用实例初始化、CORS 中间件配置以及健康检查接口。
启动时自动创建数据库表结构。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.community import router as community_router
from app.api.search import router as search_router
from app.config import settings
from app.models.database import Base, engine

# 自动创建数据库表（如果尚未存在）
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# CORS 中间件 — 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search_router)
app.include_router(community_router)


@app.get("/api/v1/health")
async def health_check():
    """健康检查接口，用于确认服务正常运行。"""
    return {"status": "ok"}
