"""
爬虫模块测试

测试 BeikeCrawler 的 URL 构建和 HTML 解析功能。
"""

import pytest

from app.crawler.beike import BeikeCrawler


MOCK_COMMUNITY_LIST_HTML = """
<html>
<body>
<ul class="listContent">
  <li class="clear xiaoquListItem" data-id="123456">
    <div class="info">
      <div class="title">
        <a href="https://sh.ke.com/xiaoqu/123456/" target="_blank">翠湖天地</a>
      </div>
      <div class="xiaoquListItemPrice">
        <div class="totalPrice">
          <span>128000</span>
        </div>
        <div class="priceDesc">元/平</div>
      </div>
    </div>
  </li>
  <li class="clear xiaoquListItem" data-id="789012">
    <div class="info">
      <div class="title">
        <a href="https://sh.ke.com/xiaoqu/789012/" target="_blank">仁恒河滨城</a>
      </div>
      <div class="xiaoquListItemPrice">
        <div class="totalPrice">
          <span>105000</span>
        </div>
        <div class="priceDesc">元/平</div>
      </div>
    </div>
  </li>
</ul>
</body>
</html>
"""

MOCK_COMMUNITY_DETAIL_HTML = """
<html>
<body>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">物业公司</span>
  <span class="xiaoquInfoContent">绿城物业</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">物业费用</span>
  <span class="xiaoquInfoContent">3.5元/平米/月</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">建筑年代</span>
  <span class="xiaoquInfoContent">2010年建成</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">容积率</span>
  <span class="xiaoquInfoContent">2.5</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">绿化率</span>
  <span class="xiaoquInfoContent">35%</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">开发商</span>
  <span class="xiaoquInfoContent">绿城中国</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">楼栋总数</span>
  <span class="xiaoquInfoContent">20栋</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">房屋总数</span>
  <span class="xiaoquInfoContent">3000户</span>
</div>
<div class="xiaoquInfoItem">
  <span class="xiaoquInfoLabel">车位配比</span>
  <span class="xiaoquInfoContent">1:1.5</span>
</div>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_beike_crawler_builds_url():
    """测试贝壳爬虫构建的列表 URL 包含 ke.com 域名。"""
    crawler = BeikeCrawler()
    try:
        url = crawler.build_list_url("上海", "浦东", 1)
        assert "ke.com" in url
        assert "sh" in url
    finally:
        await crawler.close()


@pytest.mark.asyncio
async def test_beike_parse_community_list():
    """测试贝壳爬虫解析小区列表 HTML，验证返回结构正确。"""
    crawler = BeikeCrawler()
    try:
        result = crawler.parse_community_list(MOCK_COMMUNITY_LIST_HTML)
        assert isinstance(result, list)
        assert len(result) == 2

        first = result[0]
        assert first["name"] == "翠湖天地"
        assert first["avg_price"] == 128000
        assert "ke.com" in first["source_url"]

        second = result[1]
        assert second["name"] == "仁恒河滨城"
        assert second["avg_price"] == 105000
    finally:
        await crawler.close()


@pytest.mark.asyncio
async def test_beike_parse_community_detail():
    """测试贝壳爬虫解析小区详情 HTML，验证返回字段正确。"""
    crawler = BeikeCrawler()
    try:
        result = crawler.parse_community_detail(MOCK_COMMUNITY_DETAIL_HTML)
        assert isinstance(result, dict)
        assert result["property_company"] == "绿城物业"
        assert result["property_fee"] == 3.5
        assert result["build_year"] == 2010
        assert result["volume_ratio"] == 2.5
        assert result["green_ratio"] == 35.0
        assert result["developer"] == "绿城中国"
        assert result["total_units"] == 3000
        assert result["parking_ratio"] == "1:1.5"
    finally:
        await crawler.close()


@pytest.mark.asyncio
async def test_beike_parse_float_and_int():
    """测试安全数字解析辅助方法。"""
    assert BeikeCrawler._parse_float("3.5元/平米/月") == 3.5
    assert BeikeCrawler._parse_float("35%") == 35.0
    assert BeikeCrawler._parse_float("无数据") is None
    assert BeikeCrawler._parse_float(None) is None

    assert BeikeCrawler._parse_int("3000户") == 3000
    assert BeikeCrawler._parse_int("2010年建成") == 2010
    assert BeikeCrawler._parse_int("暂无") is None
    assert BeikeCrawler._parse_int(None) is None
