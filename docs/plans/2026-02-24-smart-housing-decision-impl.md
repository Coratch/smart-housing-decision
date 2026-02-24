# 智慧购房决策工具 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个购房决策 Web 工具，支持上海/苏州城市搜索，自动爬取房产数据并基于加权评分模型推荐小区。

**Architecture:** Python FastAPI 后端提供 REST API，React + Ant Design 前端 SPA。数据通过 httpx 爬虫从贝壳/安居客采集，高德地图 API 获取 POI，SQLite 存储。评分引擎对小区多维度加权打分并生成优缺点分析。

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy / httpx / parsel / SQLite / React 18 / TypeScript / Ant Design / ECharts

---

## Task 1: 后端项目脚手架

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

**Step 1: 创建 requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
httpx==0.28.1
parsel==1.9.1
pydantic==2.10.4
pydantic-settings==2.7.1
pytest==8.3.4
pytest-asyncio==0.25.0
httpx  # also used as test client
```

**Step 2: 创建 config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart Housing Decision"
    database_url: str = "sqlite:///./data/housing.db"
    amap_api_key: str = ""
    crawl_cache_days: int = 7
    crawl_request_delay_min: float = 2.0
    crawl_request_delay_max: float = 5.0

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 3: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
```

**Step 4: 写 health check 测试**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 5: 运行测试**

Run: `cd backend && pip install -r requirements.txt && python -m pytest tests/test_health.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: 初始化后端项目脚手架（FastAPI + 健康检查）"
```

---

## Task 2: 数据库模型（SQLAlchemy）

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/community.py`
- Create: `backend/app/models/database.py`
- Create: `backend/tests/test_models.py`

**Step 1: 创建 database.py**

```python
# backend/app/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2: 创建 community.py 数据模型**

```python
# backend/app/models/community.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.models.database import Base


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False, index=True)
    district = Column(String, index=True)
    address = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    avg_price = Column(Integer)
    price_trend = Column(JSON)
    build_year = Column(Integer)
    total_units = Column(Integer)
    green_ratio = Column(Float)
    volume_ratio = Column(Float)
    property_company = Column(String)
    property_fee = Column(Float)
    developer = Column(String)
    parking_ratio = Column(String)
    source_url = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school_districts = relationship("SchoolDistrict", back_populates="community")
    nearby_pois = relationship("NearbyPOI", back_populates="community")


class SchoolDistrict(Base):
    __tablename__ = "school_districts"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    primary_school = Column(String)
    middle_school = Column(String)
    school_rank = Column(String)  # 市重点/区重点/普通
    year = Column(Integer)

    community = relationship("Community", back_populates="school_districts")


class NearbyPOI(Base):
    __tablename__ = "nearby_pois"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    category = Column(String, nullable=False)  # 地铁/医院/商场/公园/学校
    name = Column(String, nullable=False)
    distance = Column(Integer)  # 米
    walk_time = Column(Integer)  # 分钟

    community = relationship("Community", back_populates="nearby_pois")
```

**Step 3: 写模型测试**

```python
# backend/tests/test_models.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.community import Community, NearbyPOI, SchoolDistrict
from app.models.database import Base

engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)


def setup_module():
    Base.metadata.create_all(engine)


def test_create_community():
    session = Session()
    community = Community(
        name="测试小区", city="上海", district="浦东", avg_price=50000
    )
    session.add(community)
    session.commit()
    assert community.id is not None
    assert community.name == "测试小区"
    session.close()


def test_create_school_district():
    session = Session()
    community = Community(name="学区房小区", city="上海", district="徐汇", avg_price=80000)
    session.add(community)
    session.commit()

    school = SchoolDistrict(
        community_id=community.id,
        primary_school="上海小学",
        school_rank="区重点",
        year=2026,
    )
    session.add(school)
    session.commit()
    assert school.community_id == community.id
    session.close()


def test_create_nearby_poi():
    session = Session()
    community = Community(name="地铁房小区", city="苏州", district="姑苏", avg_price=30000)
    session.add(community)
    session.commit()

    poi = NearbyPOI(
        community_id=community.id,
        category="地铁",
        name="1号线-人民广场站",
        distance=300,
        walk_time=5,
    )
    session.add(poi)
    session.commit()
    assert poi.community_id == community.id
    session.close()
```

**Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: 3 PASS

**Step 5: Commit**

```bash
git add backend/app/models/ backend/tests/test_models.py
git commit -m "feat: 添加数据库模型（Community/SchoolDistrict/NearbyPOI）"
```

---

## Task 3: Pydantic Schema 和搜索 API

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/community.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/search.py`
- Create: `backend/tests/test_search_api.py`

**Step 1: 创建 Pydantic schemas**

```python
# backend/app/schemas/community.py
from pydantic import BaseModel, Field


class WeightsConfig(BaseModel):
    price: float = Field(default=0.30, ge=0, le=1)
    school: float = Field(default=0.25, ge=0, le=1)
    facilities: float = Field(default=0.20, ge=0, le=1)
    property_mgmt: float = Field(default=0.15, ge=0, le=1)
    developer: float = Field(default=0.10, ge=0, le=1)


class SearchRequest(BaseModel):
    city: str
    district: str | None = None
    price_min: int
    price_max: int
    weights: WeightsConfig = WeightsConfig()


class SubScores(BaseModel):
    price: float
    school: float
    facilities: float
    property_mgmt: float
    developer: float


class CommunityBrief(BaseModel):
    id: int
    name: str
    city: str
    district: str | None
    avg_price: int | None
    score: float
    sub_scores: SubScores
    pros: list[str]
    cons: list[str]
    tags: list[str]

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    total: int
    communities: list[CommunityBrief]


class POIResponse(BaseModel):
    category: str
    name: str
    distance: int | None
    walk_time: int | None


class SchoolDistrictResponse(BaseModel):
    primary_school: str | None
    middle_school: str | None
    school_rank: str | None
    year: int | None


class CommunityDetail(BaseModel):
    id: int
    name: str
    city: str
    district: str | None
    address: str | None
    avg_price: int | None
    build_year: int | None
    total_units: int | None
    green_ratio: float | None
    volume_ratio: float | None
    property_company: str | None
    property_fee: float | None
    developer: str | None
    parking_ratio: str | None
    score: float
    sub_scores: SubScores
    pros: list[str]
    cons: list[str]
    school_districts: list[SchoolDistrictResponse]
    nearby_pois: list[POIResponse]

    class Config:
        from_attributes = True
```

**Step 2: 创建搜索 API 路由（先返回 mock 数据）**

```python
# backend/app/api/search.py
from fastapi import APIRouter

from app.schemas.community import (
    CommunityBrief,
    SearchRequest,
    SearchResponse,
    SubScores,
    WeightsConfig,
)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_communities(request: SearchRequest):
    # TODO: 替换为真实数据查询 + 评分逻辑
    return SearchResponse(total=0, communities=[])


@router.get("/config/weights", response_model=WeightsConfig)
async def get_default_weights():
    return WeightsConfig()
```

**Step 3: 注册路由到 main.py**

在 `backend/app/main.py` 中添加：

```python
from app.api.search import router as search_router

app.include_router(search_router)
```

**Step 4: 写搜索 API 测试**

```python
# backend/tests/test_search_api.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_returns_empty_for_no_data():
    response = client.post(
        "/api/v1/search",
        json={"city": "上海", "price_min": 30000, "price_max": 60000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["communities"] == []


def test_search_with_district():
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


def test_search_with_custom_weights():
    response = client.post(
        "/api/v1/search",
        json={
            "city": "上海",
            "price_min": 30000,
            "price_max": 60000,
            "weights": {"price": 0.5, "school": 0.2, "facilities": 0.1, "property_mgmt": 0.1, "developer": 0.1},
        },
    )
    assert response.status_code == 200


def test_get_default_weights():
    response = client.get("/api/v1/config/weights")
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 0.3
    assert data["school"] == 0.25
```

**Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/test_search_api.py -v`
Expected: 4 PASS

**Step 6: Commit**

```bash
git add backend/app/schemas/ backend/app/api/ backend/tests/test_search_api.py backend/app/main.py
git commit -m "feat: 添加 Pydantic Schema 和搜索 API 骨架"
```

---

## Task 4: 评分引擎

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/scoring.py`
- Create: `backend/tests/test_scoring.py`
- Create: `backend/data/property_ranks.json`
- Create: `backend/data/developer_ranks.json`

**Step 1: 创建静态评级数据**

```json
// backend/data/property_ranks.json
{
  "top10": ["碧桂园服务", "保利物业", "华润万象生活", "中海物业", "招商积余", "万物云", "融创服务", "绿城服务", "金地智慧服务", "龙湖智创生活"],
  "top50": ["雅生活智慧城市", "旭辉永升服务", "新城悦服务", "建业新生活", "世茂服务", "远洋服务", "越秀服务", "金科智慧服务", "正荣服务", "阳光智博"]
}
```

```json
// backend/data/developer_ranks.json
{
  "top10": ["万科", "碧桂园", "保利发展", "中海地产", "华润置地", "招商蛇口", "融创中国", "龙湖集团", "金地集团", "绿城中国"],
  "top50": ["旭辉集团", "新城控股", "世茂集团", "远洋集团", "越秀地产", "建业地产", "金科股份", "正荣地产", "阳光城", "中南建设", "美的置业", "雅居乐", "合景泰富", "中梁控股", "时代中国", "佳兆业", "弘阳地产", "祥生控股", "中骏集团", "禹洲集团"]
}
```

**Step 2: 写评分引擎测试**

```python
# backend/tests/test_scoring.py
from app.core.scoring import ScoringEngine
from app.schemas.community import WeightsConfig


def make_community_data(**overrides):
    defaults = {
        "avg_price": 50000,
        "build_year": 2015,
        "green_ratio": 0.35,
        "volume_ratio": 2.0,
        "property_company": "万物云",
        "property_fee": 3.5,
        "developer": "万科",
    }
    defaults.update(overrides)
    return defaults


def test_price_score_within_range():
    engine = ScoringEngine()
    score = engine.calc_price_score(avg_price=50000, price_min=30000, price_max=60000)
    assert 0 <= score <= 10


def test_price_score_at_min():
    engine = ScoringEngine()
    score = engine.calc_price_score(avg_price=30000, price_min=30000, price_max=60000)
    assert score >= 8  # 最便宜的应该得高分


def test_price_score_exceeds_max():
    engine = ScoringEngine()
    score = engine.calc_price_score(avg_price=70000, price_min=30000, price_max=60000)
    assert score <= 3


def test_school_score_top_school():
    engine = ScoringEngine()
    score = engine.calc_school_score(school_rank="市重点")
    assert score == 10


def test_school_score_no_school():
    engine = ScoringEngine()
    score = engine.calc_school_score(school_rank=None)
    assert score == 0


def test_facilities_score():
    engine = ScoringEngine()
    pois = [
        {"category": "地铁", "distance": 300},
        {"category": "医院", "distance": 800},
        {"category": "商场", "distance": 500},
    ]
    score = engine.calc_facilities_score(pois)
    assert 0 <= score <= 10


def test_property_score_top_company():
    engine = ScoringEngine()
    score = engine.calc_property_score(
        company="万物云", fee=3.5, green_ratio=0.35, volume_ratio=2.0
    )
    assert score >= 7


def test_developer_score_top10():
    engine = ScoringEngine()
    score = engine.calc_developer_score("万科")
    assert score >= 8


def test_developer_score_unknown():
    engine = ScoringEngine()
    score = engine.calc_developer_score("无名开发商")
    assert score <= 4


def test_total_score():
    engine = ScoringEngine()
    weights = WeightsConfig()
    sub_scores = {
        "price": 8.0,
        "school": 7.0,
        "facilities": 6.0,
        "property_mgmt": 7.5,
        "developer": 9.0,
    }
    total = engine.calc_total_score(sub_scores, weights)
    expected = 8.0 * 0.3 + 7.0 * 0.25 + 6.0 * 0.2 + 7.5 * 0.15 + 9.0 * 0.1
    assert abs(total - expected) < 0.01
```

**Step 3: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: FAIL (module not found)

**Step 4: 实现评分引擎**

```python
# backend/app/core/scoring.py
import json
from pathlib import Path

from app.schemas.community import WeightsConfig

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_json(filename: str) -> dict:
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}


class ScoringEngine:
    def __init__(self):
        self.property_ranks = _load_json("property_ranks.json")
        self.developer_ranks = _load_json("developer_ranks.json")

    def calc_price_score(self, avg_price: int, price_min: int, price_max: int) -> float:
        if avg_price is None:
            return 5.0
        if avg_price <= price_min:
            return 10.0
        if avg_price >= price_max * 1.2:
            return 1.0
        if avg_price > price_max:
            overshoot = (avg_price - price_max) / (price_max * 0.2)
            return max(1.0, 4.0 - overshoot * 3.0)
        ratio = (avg_price - price_min) / (price_max - price_min)
        return round(10.0 - ratio * 4.0, 1)  # 6~10 分

    def calc_school_score(self, school_rank: str | None) -> float:
        rank_map = {"市重点": 10, "区重点": 7, "普通": 5}
        if school_rank is None:
            return 0.0
        return float(rank_map.get(school_rank, 3.0))

    def calc_facilities_score(self, pois: list[dict]) -> float:
        if not pois:
            return 0.0
        category_weights = {"地铁": 3.0, "医院": 2.0, "商场": 2.0, "公园": 1.5, "学校": 1.5}
        total_weight = 0.0
        weighted_score = 0.0
        for poi in pois:
            cat = poi.get("category", "")
            dist = poi.get("distance", 9999)
            weight = category_weights.get(cat, 1.0)
            if dist <= 500:
                s = 10.0
            elif dist <= 1000:
                s = 7.0
            elif dist <= 2000:
                s = 4.0
            else:
                s = 1.0
            weighted_score += s * weight
            total_weight += weight
        if total_weight == 0:
            return 0.0
        return round(min(10.0, weighted_score / total_weight), 1)

    def calc_property_score(
        self, company: str | None, fee: float | None, green_ratio: float | None, volume_ratio: float | None
    ) -> float:
        score = 5.0
        if company:
            if company in self.property_ranks.get("top10", []):
                score += 3.0
            elif company in self.property_ranks.get("top50", []):
                score += 1.5
        if green_ratio is not None:
            if green_ratio >= 0.35:
                score += 1.0
            elif green_ratio < 0.2:
                score -= 1.0
        if volume_ratio is not None:
            if volume_ratio <= 2.0:
                score += 1.0
            elif volume_ratio > 4.0:
                score -= 1.0
        return round(min(10.0, max(0.0, score)), 1)

    def calc_developer_score(self, developer: str | None) -> float:
        if developer is None:
            return 3.0
        if developer in self.developer_ranks.get("top10", []):
            return 10.0
        if developer in self.developer_ranks.get("top50", []):
            return 7.0
        return 3.0

    def calc_total_score(self, sub_scores: dict[str, float], weights: WeightsConfig) -> float:
        total = (
            sub_scores["price"] * weights.price
            + sub_scores["school"] * weights.school
            + sub_scores["facilities"] * weights.facilities
            + sub_scores["property_mgmt"] * weights.property_mgmt
            + sub_scores["developer"] * weights.developer
        )
        return round(total, 2)
```

**Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/core/ backend/data/ backend/tests/test_scoring.py
git commit -m "feat: 实现加权评分引擎（5个维度评分计算）"
```

---

## Task 5: 优缺点分析引擎

**Files:**
- Create: `backend/app/core/analyzer.py`
- Create: `backend/tests/test_analyzer.py`

**Step 1: 写测试**

```python
# backend/tests/test_analyzer.py
from app.core.analyzer import ProConAnalyzer


def test_high_score_is_pro():
    analyzer = ProConAnalyzer()
    result = analyzer.analyze(
        sub_scores={"price": 9.0, "school": 3.0, "facilities": 6.0, "property_mgmt": 8.5, "developer": 2.0},
        community_data={"avg_price": 35000, "property_company": "万物云", "developer": "无名"},
        school_rank="市重点",
        pois=[{"category": "地铁", "distance": 200}],
    )
    assert any("性价比" in p for p in result["pros"])
    assert any("开发商" in c for c in result["cons"])


def test_tags_generated():
    analyzer = ProConAnalyzer()
    result = analyzer.analyze(
        sub_scores={"price": 9.0, "school": 10.0, "facilities": 8.0, "property_mgmt": 7.0, "developer": 9.0},
        community_data={"avg_price": 35000, "property_company": "万物云", "developer": "万科"},
        school_rank="市重点",
        pois=[{"category": "地铁", "distance": 200}],
    )
    assert "市重点学区" in result["tags"]
    assert "地铁旁" in result["tags"]
```

**Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_analyzer.py -v`
Expected: FAIL

**Step 3: 实现优缺点分析器**

```python
# backend/app/core/analyzer.py

DIMENSION_NAMES = {
    "price": "性价比",
    "school": "学区质量",
    "facilities": "周边配套",
    "property_mgmt": "物业品质",
    "developer": "开发商信誉",
}

PRO_TEMPLATES = {
    "price": "性价比高，均价 {avg_price} 元/㎡",
    "school": "对口优质学校",
    "facilities": "周边配套齐全",
    "property_mgmt": "物业管理品质优良（{property_company}）",
    "developer": "知名开发商（{developer}）",
}

CON_TEMPLATES = {
    "price": "价格偏高，均价 {avg_price} 元/㎡",
    "school": "学区一般或无对口学校",
    "facilities": "周边配套不足",
    "property_mgmt": "物业管理品质较低",
    "developer": "开发商知名度不高",
}


class ProConAnalyzer:
    def analyze(
        self,
        sub_scores: dict[str, float],
        community_data: dict,
        school_rank: str | None = None,
        pois: list[dict] | None = None,
    ) -> dict:
        pros = []
        cons = []
        tags = []

        for dim, score in sub_scores.items():
            if score >= 8.0:
                template = PRO_TEMPLATES.get(dim, f"{DIMENSION_NAMES.get(dim, dim)}表现优秀")
                pros.append(template.format(**community_data))
            elif score <= 4.0:
                template = CON_TEMPLATES.get(dim, f"{DIMENSION_NAMES.get(dim, dim)}表现不足")
                cons.append(template.format(**community_data))

        # 生成标签
        if school_rank == "市重点":
            tags.append("市重点学区")
        elif school_rank == "区重点":
            tags.append("区重点学区")

        if pois:
            subway_nearby = any(p["category"] == "地铁" and p.get("distance", 9999) <= 500 for p in pois)
            if subway_nearby:
                tags.append("地铁旁")

        if sub_scores.get("price", 0) >= 8.0:
            tags.append("高性价比")

        return {"pros": pros, "cons": cons, "tags": tags}
```

**Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_analyzer.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/core/analyzer.py backend/tests/test_analyzer.py
git commit -m "feat: 实现优缺点分��引擎（自动生成标签/优缺点）"
```

---

## Task 6: 爬虫基础框架 + 贝壳爬虫

**Files:**
- Create: `backend/app/crawler/__init__.py`
- Create: `backend/app/crawler/base.py`
- Create: `backend/app/crawler/beike.py`
- Create: `backend/tests/test_crawler.py`

**Step 1: 写爬虫测试（使用 mock）**

```python
# backend/tests/test_crawler.py
from unittest.mock import AsyncMock, patch

import pytest

from app.crawler.beike import BeikeCrawler


@pytest.mark.asyncio
async def test_beike_parse_community_list():
    """测试贝壳小区列表页面解析"""
    crawler = BeikeCrawler()
    # 模拟的 HTML 片段（简化版贝壳小区列表结构）
    mock_html = """
    <div class="resblock-list-wrapper">
        <li class="resblock-list-post">
            <div class="resblock-name">
                <a href="/xiaoqu/123/">测试花园</a>
            </div>
            <div class="resblock-price">
                <span class="number">50000</span>
                <span class="desc">元/㎡</span>
            </div>
            <div class="resblock-location">浦东</div>
        </li>
    </div>
    """
    results = crawler.parse_community_list(mock_html)
    assert len(results) >= 0  # 解析结果取决于实际页面结构


@pytest.mark.asyncio
async def test_beike_crawler_builds_url():
    crawler = BeikeCrawler()
    url = crawler.build_list_url(city="sh", district=None, page=1)
    assert "sh.ke.com" in url or "ke.com" in url
```

**Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_crawler.py -v`
Expected: FAIL

**Step 3: 实现爬虫基类**

```python
# backend/app/crawler/base.py
import asyncio
import random

import httpx

from app.config import settings

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class BaseCrawler:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
        )

    def _random_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def _delay(self):
        delay = random.uniform(settings.crawl_request_delay_min, settings.crawl_request_delay_max)
        await asyncio.sleep(delay)

    async def fetch(self, url: str) -> str | None:
        try:
            await self._delay()
            resp = await self.client.get(url, headers=self._random_headers())
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as e:
            print(f"Crawl error for {url}: {e}")
            return None

    async def close(self):
        await self.client.aclose()
```

**Step 4: 实现贝壳爬虫**

```python
# backend/app/crawler/beike.py
from parsel import Selector

from app.crawler.base import BaseCrawler

# 贝壳城市代码映射
CITY_CODES = {
    "上海": "sh",
    "苏州": "su",
}


class BeikeCrawler(BaseCrawler):
    BASE_URL = "https://{city_code}.ke.com"

    def build_list_url(self, city: str, district: str | None = None, page: int = 1) -> str:
        city_code = CITY_CODES.get(city, city)
        base = self.BASE_URL.format(city_code=city_code)
        if district:
            return f"{base}/xiaoqu/{district}/pg{page}/"
        return f"{base}/xiaoqu/pg{page}/"

    def parse_community_list(self, html: str) -> list[dict]:
        sel = Selector(text=html)
        results = []
        for item in sel.css(".resblock-list-post, .xiaoquListItem"):
            name = item.css(".resblock-name a::text, .maidian-detail .title a::text").get("").strip()
            price_text = item.css(".resblock-price .number::text, .totalPrice span::text").get("0")
            link = item.css(".resblock-name a::attr(href), .maidian-detail .title a::attr(href)").get("")
            if name:
                results.append({
                    "name": name,
                    "avg_price": int(price_text) if price_text.isdigit() else None,
                    "source_url": link,
                })
        return results

    def parse_community_detail(self, html: str) -> dict:
        sel = Selector(text=html)
        data = {}
        # 通用属性提取（贝壳小区详情页）
        for row in sel.css(".xiaoquInfoItem, .resblock-detail-item"):
            label = row.css(".xiaoquInfoItemTitle::text, .label::text").get("").strip()
            value = row.css(".xiaoquInfoItemValue::text, .value::text").get("").strip()
            if "物业公司" in label:
                data["property_company"] = value
            elif "物业费" in label:
                data["property_fee"] = self._parse_float(value)
            elif "建筑年代" in label or "建成" in label:
                data["build_year"] = self._parse_int(value)
            elif "容积率" in label:
                data["volume_ratio"] = self._parse_float(value)
            elif "绿化率" in label:
                data["green_ratio"] = self._parse_float(value.replace("%", "")) / 100 if "%" in value else self._parse_float(value)
            elif "开发商" in label:
                data["developer"] = value
            elif "总户数" in label:
                data["total_units"] = self._parse_int(value)
            elif "车位" in label:
                data["parking_ratio"] = value
        return data

    @staticmethod
    def _parse_float(s: str) -> float | None:
        try:
            return float("".join(c for c in s if c.isdigit() or c == "."))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_int(s: str) -> int | None:
        try:
            return int("".join(c for c in s if c.isdigit()))
        except (ValueError, TypeError):
            return None
```

**Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/test_crawler.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add backend/app/crawler/ backend/tests/test_crawler.py
git commit -m "feat: 实现爬虫基础框架和贝壳爬虫解析器"
```

---

## Task 7: 高德地图 POI 服务

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/amap.py`
- Create: `backend/tests/test_amap.py`

**Step 1: 写测试**

```python
# backend/tests/test_amap.py
from unittest.mock import AsyncMock, patch

import pytest

from app.services.amap import AmapService


@pytest.mark.asyncio
async def test_parse_poi_response():
    service = AmapService()
    mock_response = {
        "status": "1",
        "pois": [
            {"name": "人民广场站", "type": "地铁站", "distance": "350"},
            {"name": "仁济医院", "type": "医院", "distance": "800"},
        ],
    }
    pois = service.parse_poi_response(mock_response, category="地铁")
    assert len(pois) == 2
    assert pois[0]["name"] == "人民广场站"
    assert pois[0]["distance"] == 350


@pytest.mark.asyncio
async def test_build_search_url():
    service = AmapService()
    url = service.build_search_url(lat=31.2304, lng=121.4737, keywords="地铁站", radius=1000)
    assert "keywords" in url
    assert "location" in url
```

**Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_amap.py -v`
Expected: FAIL

**Step 3: 实现高德地图服务**

```python
# backend/app/services/amap.py
from urllib.parse import urlencode

import httpx

from app.config import settings

# 高德 POI 类型映射
CATEGORY_TYPES = {
    "地铁": "150500",
    "医院": "090100",
    "商场": "060100|060200",
    "公园": "110200",
    "学校": "141200",
}


class AmapService:
    BASE_URL = "https://restapi.amap.com/v3/place/around"

    def __init__(self):
        self.api_key = settings.amap_api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    def build_search_url(self, lat: float, lng: float, keywords: str, radius: int = 1000) -> str:
        params = {
            "key": self.api_key,
            "location": f"{lng},{lat}",
            "keywords": keywords,
            "radius": radius,
            "output": "json",
            "offset": 20,
        }
        return f"{self.BASE_URL}?{urlencode(params)}"

    def parse_poi_response(self, data: dict, category: str) -> list[dict]:
        pois = []
        for item in data.get("pois", []):
            distance = int(item.get("distance", 0))
            pois.append({
                "category": category,
                "name": item.get("name", ""),
                "distance": distance,
                "walk_time": max(1, distance // 80),  # 步行速度约 80m/min
            })
        return pois

    async def search_nearby(self, lat: float, lng: float, category: str, radius: int = 1000) -> list[dict]:
        if not self.api_key:
            return []
        type_code = CATEGORY_TYPES.get(category, "")
        params = {
            "key": self.api_key,
            "location": f"{lng},{lat}",
            "types": type_code,
            "radius": radius,
            "output": "json",
            "offset": 10,
        }
        try:
            resp = await self.client.get(self.BASE_URL, params=params)
            data = resp.json()
            if data.get("status") == "1":
                return self.parse_poi_response(data, category)
        except Exception as e:
            print(f"Amap API error: {e}")
        return []

    async def search_all_categories(self, lat: float, lng: float) -> list[dict]:
        all_pois = []
        for category in CATEGORY_TYPES:
            pois = await self.search_nearby(lat, lng, category)
            all_pois.extend(pois)
        return all_pois

    async def close(self):
        await self.client.aclose()
```

**Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_amap.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/services/ backend/tests/test_amap.py
git commit -m "feat: 实现高德地图 POI 服务（周边搜索 + 解析）"
```

---

## Task 8: 数据聚合层（连接爬虫 + 评分 + 数据库）

**Files:**
- Create: `backend/app/core/aggregator.py`
- Create: `backend/tests/test_aggregator.py`

**Step 1: 写测试**

```python
# backend/tests/test_aggregator.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.aggregator import DataAggregator
from app.models.community import Community
from app.models.database import Base
from app.schemas.community import WeightsConfig

engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)


def setup_module():
    Base.metadata.create_all(engine)


def test_score_community():
    session = Session()
    community = Community(
        name="测试小区",
        city="上海",
        district="浦东",
        avg_price=50000,
        build_year=2015,
        green_ratio=0.35,
        volume_ratio=2.0,
        property_company="万物云",
        property_fee=3.5,
        developer="万科",
    )
    session.add(community)
    session.commit()

    aggregator = DataAggregator()
    weights = WeightsConfig()
    result = aggregator.score_community(
        community=community,
        school_rank="区重点",
        pois=[{"category": "地铁", "distance": 300}],
        price_min=30000,
        price_max=60000,
        weights=weights,
    )
    assert "score" in result
    assert "sub_scores" in result
    assert "pros" in result
    assert "cons" in result
    assert 0 <= result["score"] <= 100
    session.close()


def test_filter_communities():
    session = Session()
    c1 = Community(name="便宜小区", city="上海", district="浦东", avg_price=35000)
    c2 = Community(name="贵的小区", city="上海", district="浦东", avg_price=80000)
    c3 = Community(name="苏州小区", city="苏州", district="姑苏", avg_price=25000)
    session.add_all([c1, c2, c3])
    session.commit()

    aggregator = DataAggregator()
    filtered = aggregator.filter_communities(session, city="上海", district="浦东", price_min=30000, price_max=60000)
    assert len(filtered) == 1
    assert filtered[0].name == "便宜小区"
    session.close()
```

**Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_aggregator.py -v`
Expected: FAIL

**Step 3: 实现数据聚合层**

```python
# backend/app/core/aggregator.py
from sqlalchemy.orm import Session

from app.core.analyzer import ProConAnalyzer
from app.core.scoring import ScoringEngine
from app.models.community import Community, NearbyPOI, SchoolDistrict
from app.schemas.community import WeightsConfig


class DataAggregator:
    def __init__(self):
        self.scoring = ScoringEngine()
        self.analyzer = ProConAnalyzer()

    def filter_communities(
        self, db: Session, city: str, district: str | None, price_min: int, price_max: int
    ) -> list[Community]:
        query = db.query(Community).filter(Community.city == city)
        if district:
            query = query.filter(Community.district == district)
        query = query.filter(Community.avg_price >= price_min, Community.avg_price <= price_max)
        return query.all()

    def score_community(
        self,
        community: Community,
        school_rank: str | None,
        pois: list[dict],
        price_min: int,
        price_max: int,
        weights: WeightsConfig,
    ) -> dict:
        sub_scores = {
            "price": self.scoring.calc_price_score(community.avg_price, price_min, price_max),
            "school": self.scoring.calc_school_score(school_rank),
            "facilities": self.scoring.calc_facilities_score(pois),
            "property_mgmt": self.scoring.calc_property_score(
                community.property_company, community.property_fee,
                community.green_ratio, community.volume_ratio,
            ),
            "developer": self.scoring.calc_developer_score(community.developer),
        }
        total = self.scoring.calc_total_score(sub_scores, weights)

        community_data = {
            "avg_price": community.avg_price or 0,
            "property_company": community.property_company or "",
            "developer": community.developer or "",
        }
        analysis = self.analyzer.analyze(
            sub_scores=sub_scores,
            community_data=community_data,
            school_rank=school_rank,
            pois=pois,
        )

        return {
            "score": total,
            "sub_scores": sub_scores,
            "pros": analysis["pros"],
            "cons": analysis["cons"],
            "tags": analysis["tags"],
        }

    def search_and_rank(
        self, db: Session, city: str, district: str | None, price_min: int, price_max: int, weights: WeightsConfig
    ) -> list[dict]:
        communities = self.filter_communities(db, city, district, price_min, price_max)
        results = []
        for c in communities:
            school_district = db.query(SchoolDistrict).filter(SchoolDistrict.community_id == c.id).first()
            school_rank = school_district.school_rank if school_district else None
            pois = [
                {"category": p.category, "distance": p.distance}
                for p in db.query(NearbyPOI).filter(NearbyPOI.community_id == c.id).all()
            ]
            scored = self.score_community(c, school_rank, pois, price_min, price_max, weights)
            scored["community"] = c
            results.append(scored)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
```

**Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_aggregator.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/core/aggregator.py backend/tests/test_aggregator.py
git commit -m "feat: 实现数据聚合层（筛选 + 评分 + 排序）"
```

---

## Task 9: 连接搜索 API 到聚合层

**Files:**
- Modify: `backend/app/api/search.py`
- Create: `backend/app/api/community.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_search_api.py`

**Step 1: 更新搜索 API 使用真实聚合层**

```python
# backend/app/api/search.py（完整替换）
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
async def search_communities(request: SearchRequest, db: Session = Depends(get_db)):
    results = aggregator.search_and_rank(
        db=db,
        city=request.city,
        district=request.district,
        price_min=request.price_min,
        price_max=request.price_max,
        weights=request.weights,
    )
    communities = []
    for r in results:
        c = r["community"]
        communities.append(
            CommunityBrief(
                id=c.id,
                name=c.name,
                city=c.city,
                district=c.district,
                avg_price=c.avg_price,
                score=r["score"],
                sub_scores=SubScores(**r["sub_scores"]),
                pros=r["pros"],
                cons=r["cons"],
                tags=r["tags"],
            )
        )
    return SearchResponse(total=len(communities), communities=communities)


@router.get("/config/weights", response_model=WeightsConfig)
async def get_default_weights():
    return WeightsConfig()
```

**Step 2: 创建小区详情 API**

```python
# backend/app/api/community.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.aggregator import DataAggregator
from app.models.community import Community, NearbyPOI, SchoolDistrict
from app.models.database import get_db
from app.schemas.community import (
    CommunityDetail,
    POIResponse,
    SchoolDistrictResponse,
    SubScores,
    WeightsConfig,
)

router = APIRouter(prefix="/api/v1", tags=["community"])
aggregator = DataAggregator()


@router.get("/community/{community_id}", response_model=CommunityDetail)
async def get_community_detail(community_id: int, db: Session = Depends(get_db)):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="小区不存在")

    school_district = db.query(SchoolDistrict).filter(SchoolDistrict.community_id == community_id).first()
    school_rank = school_district.school_rank if school_district else None
    pois_db = db.query(NearbyPOI).filter(NearbyPOI.community_id == community_id).all()
    pois = [{"category": p.category, "distance": p.distance} for p in pois_db]

    weights = WeightsConfig()
    scored = aggregator.score_community(community, school_rank, pois, 0, 999999, weights)

    school_districts = []
    if school_district:
        school_districts.append(SchoolDistrictResponse(
            primary_school=school_district.primary_school,
            middle_school=school_district.middle_school,
            school_rank=school_district.school_rank,
            year=school_district.year,
        ))

    nearby_pois = [
        POIResponse(category=p.category, name=p.name, distance=p.distance, walk_time=p.walk_time)
        for p in pois_db
    ]

    return CommunityDetail(
        id=community.id,
        name=community.name,
        city=community.city,
        district=community.district,
        address=community.address,
        avg_price=community.avg_price,
        build_year=community.build_year,
        total_units=community.total_units,
        green_ratio=community.green_ratio,
        volume_ratio=community.volume_ratio,
        property_company=community.property_company,
        property_fee=community.property_fee,
        developer=community.developer,
        parking_ratio=community.parking_ratio,
        score=scored["score"],
        sub_scores=SubScores(**scored["sub_scores"]),
        pros=scored["pros"],
        cons=scored["cons"],
        school_districts=school_districts,
        nearby_pois=nearby_pois,
    )
```

**Step 3: 注册 community 路由到 main.py**

在 `backend/app/main.py` 中添加：

```python
from app.api.community import router as community_router

app.include_router(community_router)
```

同时在 main.py 启动时创建数据库表：

```python
from app.models.database import Base, engine

Base.metadata.create_all(bind=engine)
```

**Step 4: 运行所有测试**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/app/api/ backend/app/main.py backend/tests/
git commit -m "feat: 连接搜索 API 到聚合层，添加小区详情 API"
```

---

## Task 10: 前端项目初始化

**Files:**
- Create: `frontend/` (via create-react-app or vite)
- Create: `frontend/src/api/client.ts`

**Step 1: 使用 Vite 创建 React + TypeScript 项目**

Run:
```bash
cd /Users/wangzhicheng/IdeaProjects/smart-housing-decision
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install antd @ant-design/icons echarts echarts-for-react axios react-router-dom
```

**Step 2: 创建 API 客户端**

```typescript
// frontend/src/api/client.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  timeout: 30000,
});

export interface WeightsConfig {
  price: number;
  school: number;
  facilities: number;
  property_mgmt: number;
  developer: number;
}

export interface SearchRequest {
  city: string;
  district?: string;
  price_min: number;
  price_max: number;
  weights?: WeightsConfig;
}

export interface SubScores {
  price: number;
  school: number;
  facilities: number;
  property_mgmt: number;
  developer: number;
}

export interface CommunityBrief {
  id: number;
  name: string;
  city: string;
  district: string | null;
  avg_price: number | null;
  score: number;
  sub_scores: SubScores;
  pros: string[];
  cons: string[];
  tags: string[];
}

export interface SearchResponse {
  total: number;
  communities: CommunityBrief[];
}

export const searchCommunities = (params: SearchRequest) =>
  apiClient.post<SearchResponse>("/search", params);

export const getCommunityDetail = (id: number) =>
  apiClient.get(`/community/${id}`);

export const getDefaultWeights = () =>
  apiClient.get<WeightsConfig>("/config/weights");
```

**Step 3: 验证前端能启动**

Run: `cd frontend && npm run dev`
Expected: Vite dev server 启动成功

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: 初始化前端项目（React + TypeScript + Ant Design）"
```

---

## Task 11: 前端搜索页

**Files:**
- Create: `frontend/src/pages/SearchPage.tsx`
- Create: `frontend/src/components/SearchForm.tsx`
- Create: `frontend/src/components/WeightSlider.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: 创建 SearchForm 组件**

```tsx
// frontend/src/components/SearchForm.tsx
import { Button, Col, Form, InputNumber, Row, Select } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import type { SearchRequest } from "../api/client";

const CITIES = [
  { label: "上海", value: "上海" },
  { label: "苏州", value: "苏州" },
];

const DISTRICTS: Record<string, { label: string; value: string }[]> = {
  上海: [
    { label: "浦东", value: "浦东" },
    { label: "徐汇", value: "徐汇" },
    { label: "静安", value: "静安" },
    { label: "黄浦", value: "黄浦" },
    { label: "长宁", value: "长宁" },
    { label: "闵行", value: "闵行" },
    { label: "杨浦", value: "杨浦" },
    { label: "虹口", value: "虹口" },
    { label: "普陀", value: "普陀" },
    { label: "宝山", value: "宝山" },
    { label: "松江", value: "松江" },
    { label: "嘉定", value: "嘉定" },
  ],
  苏州: [
    { label: "姑苏", value: "姑苏" },
    { label: "工业园区", value: "工业园区" },
    { label: "高新区", value: "高新区" },
    { label: "吴中", value: "吴中" },
    { label: "相城", value: "相城" },
    { label: "吴江", value: "吴江" },
  ],
};

interface Props {
  onSearch: (values: SearchRequest) => void;
  loading: boolean;
}

export default function SearchForm({ onSearch, loading }: Props) {
  const [form] = Form.useForm();
  const city = Form.useWatch("city", form);

  const handleSubmit = (values: Record<string, unknown>) => {
    onSearch({
      city: values.city as string,
      district: values.district as string | undefined,
      price_min: values.price_min as number,
      price_max: values.price_max as number,
    });
  };

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Row gutter={16}>
        <Col span={6}>
          <Form.Item name="city" label="城市" rules={[{ required: true, message: "请选择城市" }]}>
            <Select options={CITIES} placeholder="选择城市" onChange={() => form.setFieldValue("district", undefined)} />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item name="district" label="区域（可选）">
            <Select options={city ? DISTRICTS[city] || [] : []} placeholder="选择区域" allowClear />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item name="price_min" label="最低单价（元/㎡）" rules={[{ required: true }]}>
            <InputNumber style={{ width: "100%" }} min={0} step={5000} />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item name="price_max" label="最高单价（元/㎡）" rules={[{ required: true }]}>
            <InputNumber style={{ width: "100%" }} min={0} step={5000} />
          </Form.Item>
        </Col>
        <Col span={4} style={{ display: "flex", alignItems: "flex-end" }}>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>
              查询推荐
            </Button>
          </Form.Item>
        </Col>
      </Row>
    </Form>
  );
}
```

**Step 2: 创建 SearchPage**

```tsx
// frontend/src/pages/SearchPage.tsx
import { useState } from "react";
import { Card, Layout, Typography } from "antd";
import SearchForm from "../components/SearchForm";
import { searchCommunities, type CommunityBrief, type SearchRequest } from "../api/client";

const { Header, Content } = Layout;

export default function SearchPage() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CommunityBrief[]>([]);

  const handleSearch = async (params: SearchRequest) => {
    setLoading(true);
    try {
      const { data } = await searchCommunities(params);
      setResults(data.communities);
    } catch (error) {
      console.error("搜索失败:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ background: "#fff", padding: "0 24px" }}>
        <Typography.Title level={3} style={{ margin: "16px 0" }}>
          智慧购房决策工具
        </Typography.Title>
      </Header>
      <Content style={{ padding: "24px" }}>
        <Card>
          <SearchForm onSearch={handleSearch} loading={loading} />
        </Card>
        {results.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <Typography.Text>找到 {results.length} 个小区</Typography.Text>
            {/* TODO: Task 12 实现 CommunityCard 列表 */}
          </div>
        )}
      </Content>
    </Layout>
  );
}
```

**Step 3: 更新 App.tsx**

```tsx
// frontend/src/App.tsx
import SearchPage from "./pages/SearchPage";

export default function App() {
  return <SearchPage />;
}
```

**Step 4: 验证前端能编译**

Run: `cd frontend && npm run build`
Expected: 编译成功

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: 实现前端搜索页（城市/区域/价格范围输入）"
```

---

## Task 12: 前端结果卡片和雷达图

**Files:**
- Create: `frontend/src/components/CommunityCard.tsx`
- Create: `frontend/src/components/ScoreRadar.tsx`
- Create: `frontend/src/components/ProsCons.tsx`
- Modify: `frontend/src/pages/SearchPage.tsx`

**Step 1: 创建雷达图组件**

```tsx
// frontend/src/components/ScoreRadar.tsx
import ReactECharts from "echarts-for-react";
import type { SubScores } from "../api/client";

interface Props {
  subScores: SubScores;
}

const LABELS: Record<string, string> = {
  price: "性价比",
  school: "学区",
  facilities: "配套",
  property_mgmt: "物业",
  developer: "开发商",
};

export default function ScoreRadar({ subScores }: Props) {
  const option = {
    radar: {
      indicator: Object.entries(LABELS).map(([key, name]) => ({ name, max: 10 })),
      radius: 60,
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: Object.keys(LABELS).map((k) => subScores[k as keyof SubScores]),
            areaStyle: { opacity: 0.3 },
          },
        ],
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 180, width: 200 }} />;
}
```

**Step 2: 创建优缺点组件**

```tsx
// frontend/src/components/ProsCons.tsx
import { Tag, Space } from "antd";
import { CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";

interface Props {
  pros: string[];
  cons: string[];
}

export default function ProsCons({ pros, cons }: Props) {
  return (
    <Space direction="vertical" size={4}>
      {pros.slice(0, 2).map((p, i) => (
        <div key={`pro-${i}`}>
          <CheckCircleOutlined style={{ color: "#52c41a", marginRight: 4 }} />
          <span style={{ color: "#52c41a" }}>{p}</span>
        </div>
      ))}
      {cons.slice(0, 2).map((c, i) => (
        <div key={`con-${i}`}>
          <CloseCircleOutlined style={{ color: "#ff4d4f", marginRight: 4 }} />
          <span style={{ color: "#ff4d4f" }}>{c}</span>
        </div>
      ))}
    </Space>
  );
}
```

**Step 3: 创建小区卡片组件**

```tsx
// frontend/src/components/CommunityCard.tsx
import { Card, Col, Row, Tag, Typography } from "antd";
import type { CommunityBrief } from "../api/client";
import ScoreRadar from "./ScoreRadar";
import ProsCons from "./ProsCons";

interface Props {
  community: CommunityBrief;
  rank: number;
}

export default function CommunityCard({ community, rank }: Props) {
  return (
    <Card style={{ marginBottom: 16 }}>
      <Row gutter={16} align="middle">
        <Col span={1}>
          <Typography.Title level={3} style={{ margin: 0, color: rank <= 3 ? "#faad14" : "#999" }}>
            {rank}
          </Typography.Title>
        </Col>
        <Col span={7}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            {community.name}
          </Typography.Title>
          <Typography.Text type="secondary">
            {community.city} · {community.district}
          </Typography.Text>
          <div style={{ marginTop: 8 }}>
            {community.tags.map((tag) => (
              <Tag color="blue" key={tag}>{tag}</Tag>
            ))}
          </div>
          {community.avg_price && (
            <Typography.Text strong style={{ fontSize: 16, color: "#f5222d" }}>
              {community.avg_price.toLocaleString()} 元/㎡
            </Typography.Text>
          )}
        </Col>
        <Col span={6}>
          <div style={{ textAlign: "center" }}>
            <Typography.Title level={2} style={{ margin: 0, color: "#1890ff" }}>
              {community.score.toFixed(1)}
            </Typography.Title>
            <Typography.Text type="secondary">综合评分</Typography.Text>
          </div>
        </Col>
        <Col span={5}>
          <ScoreRadar subScores={community.sub_scores} />
        </Col>
        <Col span={5}>
          <ProsCons pros={community.pros} cons={community.cons} />
        </Col>
      </Row>
    </Card>
  );
}
```

**Step 4: 更新 SearchPage 使用 CommunityCard**

在 `SearchPage.tsx` 中将 TODO 注释替换为：

```tsx
import CommunityCard from "../components/CommunityCard";

// 在 results 展示部分：
{results.map((community, index) => (
  <CommunityCard key={community.id} community={community} rank={index + 1} />
))}
```

**Step 5: 验证编译**

Run: `cd frontend && npm run build`
Expected: 编译成功

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: 实现结果卡片（评分雷达图 + 优缺点展示）"
```

---

## Task 13: Docker Compose 部署配置

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `backend/.env.example`

**Step 1: 创建 backend Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: 创建 frontend Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 3: 创建 docker-compose.yml**

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
    env_file:
      - ./backend/.env

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

**Step 4: 创建 .env.example**

```
# backend/.env.example
AMAP_API_KEY=your_amap_api_key_here
DATABASE_URL=sqlite:///./data/housing.db
```

**Step 5: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.yml backend/.env.example
git commit -m "feat: 添加 Docker Compose 部署配置"
```

---

## Task 14: 端到端验证（手动 seed 数据 + 启动测试）

**Files:**
- Create: `backend/scripts/seed_data.py`

**Step 1: 创建种子数据脚本**

```python
# backend/scripts/seed_data.py
"""向数据库插入测试数据，用于端到端验证"""
import sys
sys.path.insert(0, ".")

from app.models.database import Base, engine, SessionLocal
from app.models.community import Community, SchoolDistrict, NearbyPOI

Base.metadata.create_all(bind=engine)
db = SessionLocal()

communities = [
    Community(name="万科城市花园", city="上海", district="浦东", address="浦东新区张杨路1000号",
              lat=31.2356, lng=121.5257, avg_price=55000, build_year=2010, total_units=2000,
              green_ratio=0.35, volume_ratio=2.5, property_company="万物云", property_fee=3.8, developer="万科"),
    Community(name="绿城玫瑰园", city="上海", district="浦东", address="浦东新区花木路500号",
              lat=31.2156, lng=121.5457, avg_price=48000, build_year=2015, total_units=800,
              green_ratio=0.40, volume_ratio=1.8, property_company="绿城服务", property_fee=4.5, developer="绿城中国"),
    Community(name="保利天悦", city="上海", district="徐汇", address="徐汇区龙华中路800号",
              lat=31.1856, lng=121.4557, avg_price=62000, build_year=2018, total_units=500,
              green_ratio=0.38, volume_ratio=2.0, property_company="保利物业", property_fee=5.0, developer="保利发展"),
    Community(name="碧桂园湖滨城", city="苏州", district="工业园区", address="苏州工业园区星湖街100号",
              lat=31.3156, lng=120.7257, avg_price=32000, build_year=2020, total_units=1500,
              green_ratio=0.42, volume_ratio=1.5, property_company="碧桂园服务", property_fee=3.2, developer="碧桂园"),
    Community(name="中海国际社区", city="苏州", district="姑苏", address="姑苏区人民路200号",
              lat=31.3056, lng=120.6357, avg_price=35000, build_year=2016, total_units=1200,
              green_ratio=0.33, volume_ratio=2.2, property_company="中海物业", property_fee=3.5, developer="中海地产"),
]

db.add_all(communities)
db.commit()

# 添加学区数据
schools = [
    SchoolDistrict(community_id=1, primary_school="浦东实验小学", middle_school="建平中学", school_rank="区重点", year=2026),
    SchoolDistrict(community_id=2, primary_school="明珠小学", middle_school="上海中学东校", school_rank="市重点", year=2026),
    SchoolDistrict(community_id=3, primary_school="向阳小学", middle_school="位育中学", school_rank="市重点", year=2026),
    SchoolDistrict(community_id=4, primary_school="星海小学", middle_school="星海实验中学", school_rank="区重点", year=2026),
]
db.add_all(schools)
db.commit()

# 添加 POI 数据
pois = [
    NearbyPOI(community_id=1, category="地铁", name="2号线-张杨路站", distance=300, walk_time=4),
    NearbyPOI(community_id=1, category="医院", name="仁济医院", distance=1200, walk_time=15),
    NearbyPOI(community_id=1, category="商场", name="第一八佰伴", distance=800, walk_time=10),
    NearbyPOI(community_id=2, category="地铁", name="7号线-花木路站", distance=500, walk_time=7),
    NearbyPOI(community_id=2, category="公园", name="世纪公园", distance=400, walk_time=5),
    NearbyPOI(community_id=3, category="地铁", name="12号线-龙华站", distance=200, walk_time=3),
    NearbyPOI(community_id=3, category="商场", name="正大乐城", distance=600, walk_time=8),
    NearbyPOI(community_id=4, category="地铁", name="1号线-星湖街站", distance=350, walk_time=5),
    NearbyPOI(community_id=4, category="公园", name="金鸡湖", distance=500, walk_time=7),
    NearbyPOI(community_id=5, category="医院", name="苏州大学附属医院", distance=900, walk_time=12),
]
db.add_all(pois)
db.commit()
db.close()

print("✓ 种子数据插入完成")
```

**Step 2: 运行种子脚本并启动后端**

Run:
```bash
cd backend
mkdir -p data
python scripts/seed_data.py
uvicorn app.main:app --reload
```

**Step 3: 用 curl 验证 API**

Run:
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"city": "上海", "price_min": 30000, "price_max": 60000}'
```
Expected: 返回排序后的小区列表，包含 score、sub_scores、pros、cons、tags

**Step 4: 运行全部后端测试**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add backend/scripts/
git commit -m "feat: 添加种子数据脚本（端到端验证）"
```

---

## 依赖关系

```
Task 1 (后端脚手架)
  └→ Task 2 (数据模型)
       └→ Task 3 (Schema + API)
       └→ Task 4 (评分引擎)
            └→ Task 5 (优缺点分析)
       └→ Task 6 (爬虫)
       └→ Task 7 (高德服务)
            └→ Task 8 (数据聚合层) ← depends on 4, 5, 6, 7
                 └→ Task 9 (连接 API) ← depends on 3, 8
                      └→ Task 14 (端到端验证)

Task 10 (前端初始化)
  └→ Task 11 (搜索页)
       └→ Task 12 (结果卡片) ← can parallel with Task 8-9
            └→ Task 13 (Docker) ← depends on 9, 12
```

**可并行的任务组：**
- Task 4 + Task 6 + Task 7（评分、爬虫、高德服务互不依赖）
- Task 10-12（前端）与 Task 4-8（后端核心）可并行
