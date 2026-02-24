"""
应用配置模块

使用 pydantic-settings 管理应用配置，支持从 .env 文件加载环境变量。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从环境变量或 .env 文件加载配置项。"""

    app_name: str = "smart-housing-decision"
    database_url: str = "sqlite:///./data/housing.db"
    amap_api_key: str = ""
    crawl_cache_days: int = 7
    crawl_request_delay_min: float = 2.0
    crawl_request_delay_max: float = 5.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
