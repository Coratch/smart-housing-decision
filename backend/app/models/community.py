"""
小区及周边信息数据模型

包含三个核心模型：
- Community: 小区基本信息（价格、位置、配套等）
- SchoolDistrict: 学区信息（对口小学/初中及等级）
- NearbyPOI: 周边兴趣点（地铁、医院、商场等距离信息）
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Community(Base):
    """小区信息表，记录小区的基本属性、价格走势及地理位置。"""

    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False, index=True)
    district: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price_trend: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    build_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_units: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    green_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    property_company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    property_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    developer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parking_ratio: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联关系
    school_districts: Mapped[List["SchoolDistrict"]] = relationship(
        "SchoolDistrict", back_populates="community"
    )
    nearby_pois: Mapped[List["NearbyPOI"]] = relationship(
        "NearbyPOI", back_populates="community"
    )


class SchoolDistrict(Base):
    """学区信息表，记录小区对口的小学和初中及其等级。"""

    __tablename__ = "school_districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("communities.id"), nullable=False
    )
    primary_school: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    middle_school: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    school_rank: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 关联关系
    community: Mapped["Community"] = relationship(
        "Community", back_populates="school_districts"
    )


class NearbyPOI(Base):
    """周边兴趣点表，记录小区附近的地铁、医院、商场等设施及距离信息。"""

    __tablename__ = "nearby_pois"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("communities.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    walk_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 关联关系
    community: Mapped["Community"] = relationship(
        "Community", back_populates="nearby_pois"
    )
