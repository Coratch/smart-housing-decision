"""
向数据库插入测试种子数据，用于端到端验证。

特性：
- 幂等性：先清空旧数据再插入，可重复执行
- 事务原子性：所有数据在单次 commit 中写入
- 动态 ID 引用：flush 后通过 ORM 对象获取自增 ID
- 错误处理：异常时回滚事务，finally 中关闭会话
"""

import pathlib
import sys

# 将项目 backend 目录加入 Python 路径
_backend_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.models.community import Community, NearbyPOI, SchoolDistrict
from app.models.database import Base, SessionLocal, engine


def seed() -> None:
    """清空旧数据并插入全部种子数据（单事务）。"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ------ 1. 清空旧数据（按外键依赖倒序删除） ------
        deleted_pois = db.query(NearbyPOI).delete()
        deleted_schools = db.query(SchoolDistrict).delete()
        deleted_communities = db.query(Community).delete()
        print(
            f"已清空旧数据: "
            f"NearbyPOI={deleted_pois}, "
            f"SchoolDistrict={deleted_schools}, "
            f"Community={deleted_communities}"
        )

        # ------ 2. 插入小区数据并 flush 以获取自增 ID ------
        communities = [
            Community(
                name="万科城市花园", city="上海", district="浦东",
                address="浦东新区张杨路1000号",
                lat=31.2356, lng=121.5257, avg_price=55000,
                build_year=2010, total_units=2000,
                green_ratio=0.35, volume_ratio=2.5,
                property_company="万物云", property_fee=3.8, developer="万科",
            ),
            Community(
                name="绿城玫瑰园", city="上海", district="浦东",
                address="浦东新区花木路500号",
                lat=31.2156, lng=121.5457, avg_price=48000,
                build_year=2015, total_units=800,
                green_ratio=0.40, volume_ratio=1.8,
                property_company="绿城服务", property_fee=4.5, developer="绿城中国",
            ),
            Community(
                name="保利天悦", city="上海", district="徐汇",
                address="徐汇区龙华中路800号",
                lat=31.1856, lng=121.4557, avg_price=62000,
                build_year=2018, total_units=500,
                green_ratio=0.38, volume_ratio=2.0,
                property_company="保利物业", property_fee=5.0, developer="保利发展",
            ),
            Community(
                name="碧桂园湖滨城", city="苏州", district="工业园区",
                address="苏州工业园区星湖街100号",
                lat=31.3156, lng=120.7257, avg_price=32000,
                build_year=2020, total_units=1500,
                green_ratio=0.42, volume_ratio=1.5,
                property_company="碧桂园服务", property_fee=3.2, developer="碧桂园",
            ),
            Community(
                name="中海国际社区", city="苏州", district="姑苏",
                address="姑苏区人民路200号",
                lat=31.3056, lng=120.6357, avg_price=35000,
                build_year=2016, total_units=1200,
                green_ratio=0.33, volume_ratio=2.2,
                property_company="中海物业", property_fee=3.5, developer="中海地产",
            ),
        ]
        db.add_all(communities)
        db.flush()  # flush 使 ORM 分配自增 ID，但不提交事务

        # ------ 3. 插入学区数据（使用动态 community ID） ------
        schools = [
            SchoolDistrict(
                community_id=communities[0].id,
                primary_school="浦东实验小学", middle_school="建平中学",
                school_rank="区重点", year=2026,
            ),
            SchoolDistrict(
                community_id=communities[1].id,
                primary_school="明珠小学", middle_school="上海中学东校",
                school_rank="市重点", year=2026,
            ),
            SchoolDistrict(
                community_id=communities[2].id,
                primary_school="向阳小学", middle_school="位育中学",
                school_rank="市重点", year=2026,
            ),
            SchoolDistrict(
                community_id=communities[3].id,
                primary_school="星海小学", middle_school="星海实验中学",
                school_rank="区重点", year=2026,
            ),
        ]
        db.add_all(schools)

        # ------ 4. 插入 POI 数据（使用动态 community ID） ------
        pois = [
            NearbyPOI(community_id=communities[0].id, category="地铁",
                      name="2号线-张杨路站", distance=300, walk_time=4),
            NearbyPOI(community_id=communities[0].id, category="医院",
                      name="仁济医院", distance=1200, walk_time=15),
            NearbyPOI(community_id=communities[0].id, category="商场",
                      name="第一八佰伴", distance=800, walk_time=10),
            NearbyPOI(community_id=communities[1].id, category="地铁",
                      name="7号线-花木路站", distance=500, walk_time=7),
            NearbyPOI(community_id=communities[1].id, category="公园",
                      name="世纪公园", distance=400, walk_time=5),
            NearbyPOI(community_id=communities[2].id, category="地铁",
                      name="12号线-龙华站", distance=200, walk_time=3),
            NearbyPOI(community_id=communities[2].id, category="商场",
                      name="正大乐城", distance=600, walk_time=8),
            NearbyPOI(community_id=communities[3].id, category="地铁",
                      name="1号线-星湖街站", distance=350, walk_time=5),
            NearbyPOI(community_id=communities[3].id, category="公园",
                      name="金鸡湖", distance=500, walk_time=7),
            NearbyPOI(community_id=communities[4].id, category="医院",
                      name="苏州大学附属医院", distance=900, walk_time=12),
        ]
        db.add_all(pois)

        # ------ 5. 单次提交确保事务原子性 ------
        db.commit()

        print(
            f"种子数据插入成功: "
            f"Community={len(communities)}, "
            f"SchoolDistrict={len(schools)}, "
            f"NearbyPOI={len(pois)}"
        )
    except Exception:
        db.rollback()
        print("种子数据插入失败，事务已回滚")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
