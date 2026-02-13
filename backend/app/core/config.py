from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Gov Tender Collector'
    api_v1_str: str = '/api/v1'
    secret_key: str = Field(default='change-this-in-production', alias='SECRET_KEY')
    access_token_expire_minutes: int = 60 * 24

    database_url: str = Field(
        default='postgresql+psycopg2://postgres:postgres@postgres:5432/gov_tender',
        alias='DATABASE_URL',
    )
    redis_url: str = Field(default='redis://redis:6379/0', alias='REDIS_URL')

    timezone: str = 'Asia/Shanghai'
    crawl_schedule_hours: str = Field(default='9,14,21', alias='CRAWL_SCHEDULE_HOURS')
    crawl_global_concurrency: int = 20
    crawl_site_concurrency: int = 4
    crawl_timeout_seconds: int = 20
    crawl_retry_times: int = 3

    storage_root: str = Field(default='/data/attachments', alias='STORAGE_ROOT')

    deepseek_api_key: str = Field(default='', alias='DEEPSEEK_API_KEY')
    deepseek_base_url: str = Field(default='https://api.deepseek.com/v1', alias='DEEPSEEK_BASE_URL')
    deepseek_model: str = Field(default='deepseek-chat', alias='DEEPSEEK_MODEL')
    deepseek_timeout_seconds: int = 60

    seed_admin_username: str = Field(default='admin', alias='SEED_ADMIN_USERNAME')
    seed_admin_password: str = Field(default='admin123456', alias='SEED_ADMIN_PASSWORD')

    @property
    def resolved_storage_root(self) -> Path:
        return Path(self.storage_root).expanduser().resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
