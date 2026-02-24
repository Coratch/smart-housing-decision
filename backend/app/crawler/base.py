"""
爬虫基础框架模块

提供 BaseCrawler 基类，封装 HTTP 请求、随机延迟、请求头伪装等通用能力，
供具体站点爬虫继承使用。
"""

import asyncio
import logging
import random
from typing import Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# 常用 Chrome User-Agent 列表，用于伪装请求来源
_CHROME_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
]


class BaseCrawler:
    """
    爬虫基类，封装异步 HTTP 客户端和通用请求逻辑。

    子类应继承此基类，实现具体站点的 URL 构建和 HTML 解析方法。
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    def _random_headers(self) -> Dict[str, str]:
        """生成随机请求头，模拟浏览器访问以降低被反爬识别的概率。"""
        return {
            "User-Agent": random.choice(_CHROME_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def _delay(self) -> None:
        """在请求之间插入随机延迟，避免触发目标站点的频率限制。"""
        delay = random.uniform(
            settings.crawl_request_delay_min,
            settings.crawl_request_delay_max,
        )
        await asyncio.sleep(delay)

    async def fetch(self, url: str) -> Optional[str]:
        """
        发起 GET 请求并返回响应文本。

        请求前会自动插入随机延迟，使用随机 User-Agent。
        网络异常或 HTTP 错误时返回 None 并记录日志。

        Args:
            url: 目标页面 URL

        Returns:
            页面 HTML 文本，失败时返回 None
        """
        await self._delay()
        try:
            response = await self._client.get(url, headers=self._random_headers())
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP 请求状态错误: url=%s, status=%d",
                url,
                exc.response.status_code,
            )
            return None
        except httpx.RequestError as exc:
            logger.error("HTTP 请求异常: url=%s, error=%s", url, exc)
            return None

    async def close(self) -> None:
        """关闭底层 HTTP 客户端，释放连接资源。"""
        await self._client.aclose()
