"""
贝壳找房爬虫模块

继承 BaseCrawler，实现贝壳找房小区列表和详情页的 URL 构建与 HTML 解析。
用于采集小区基础信息（均价、物业、建筑年代等）供决策分析使用。
"""

import logging
import re
from typing import Dict, List, Optional

from parsel import Selector

from app.crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

# 贝壳找房支持的城市编码映射
CITY_CODES: Dict[str, str] = {
    "上海": "sh",
    "苏州": "su",
}


class BeikeCrawler(BaseCrawler):
    """
    贝壳找房爬虫，提供小区列表和详情页的解析能力。

    支持从贝壳找房获取小区均价、物业信息、建筑年代等结构化数据。
    """

    # 详情页中标签文本到字段名的映射关系
    _LABEL_FIELD_MAP: Dict[str, str] = {
        "物业公司": "property_company",
        "物业费用": "property_fee",
        "建筑年代": "build_year",
        "容积率": "volume_ratio",
        "绿化率": "green_ratio",
        "开发商": "developer",
        "房屋总数": "total_units",
        "车位配比": "parking_ratio",
    }

    def build_list_url(self, city: str, district: str, page: int = 1) -> str:
        """
        构建贝壳找房小区列表页 URL。

        Args:
            city: 城市中文名（如 "上海"）
            district: 区域名称（如 "浦东"）
            page: 页码，默认第 1 页

        Returns:
            拼接好的小区列表页 URL

        Raises:
            ValueError: 城市不在支持的城市编码列表中
        """
        city_code = CITY_CODES.get(city)
        if city_code is None:
            raise ValueError(
                f"不支持的城市: {city}，当前支持: {list(CITY_CODES.keys())}"
            )
        return f"https://{city_code}.ke.com/xiaoqu/{district}/pg{page}/"

    def parse_community_list(self, html: str) -> List[Dict]:
        """
        解析小区列表页 HTML，提取小区名称、均价和来源链接。

        Args:
            html: 小区列表页的完整 HTML 文本

        Returns:
            小区信息字典列表，每项包含 name、avg_price、source_url
        """
        selector = Selector(text=html)
        communities: List[Dict] = []

        for item in selector.css("li.xiaoquListItem"):
            name = item.css("div.title a::text").get("")
            name = name.strip()
            if not name:
                continue

            source_url = item.css("div.title a::attr(href)").get("")
            price_text = item.css("div.totalPrice span::text").get("")
            avg_price = self._parse_int(price_text)

            communities.append({
                "name": name,
                "avg_price": avg_price,
                "source_url": source_url.strip(),
            })

        return communities

    def parse_community_detail(self, html: str) -> Dict:
        """
        解析小区详情页 HTML，提取物业、建筑、配套等详细信息。

        通过匹配标签文本（如"物业公司""建筑年代"）提取对应的值，
        并根据字段类型做数值转换。

        Args:
            html: 小区详情页的完整 HTML 文本

        Returns:
            包含 property_company、property_fee、build_year、volume_ratio、
            green_ratio、developer、total_units、parking_ratio 等字段的字典
        """
        selector = Selector(text=html)
        result: Dict = {}

        for info_item in selector.css("div.xiaoquInfoItem"):
            label = info_item.css("span.xiaoquInfoLabel::text").get("")
            label = label.strip()
            value = info_item.css("span.xiaoquInfoContent::text").get("")
            value = value.strip()

            field_name = self._LABEL_FIELD_MAP.get(label)
            if field_name is None:
                continue

            # 根据字段类型做不同的解析处理
            if field_name in ("property_company", "developer", "parking_ratio"):
                result[field_name] = value
            elif field_name == "property_fee":
                result[field_name] = self._parse_float(value)
            elif field_name in ("volume_ratio", "green_ratio"):
                result[field_name] = self._parse_float(value)
            elif field_name in ("build_year", "total_units"):
                result[field_name] = self._parse_int(value)

        return result

    @staticmethod
    def _parse_float(s: Optional[str]) -> Optional[float]:
        """
        从包含数字的字符串中安全提取浮点数。

        支持从 "3.5元/平米/月"、"35%" 等混合文本中提取数值部分。

        Args:
            s: 待解析的字符串

        Returns:
            提取到的浮点数，无法解析时返回 None
        """
        if s is None:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)", s)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def _parse_int(s: Optional[str]) -> Optional[int]:
        """
        从包含数字的字符串中安全提取整数。

        支持从 "3000户"、"2010年建成" 等混合文本中提取数值部分。

        Args:
            s: 待解析的字符串

        Returns:
            提取到的整数，无法解析时返回 None
        """
        if s is None:
            return None
        match = re.search(r"(\d+)", s)
        if match:
            return int(match.group(1))
        return None
