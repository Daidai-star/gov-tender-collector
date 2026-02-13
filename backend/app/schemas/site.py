from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SiteCreateRequest(BaseModel):
    name: str
    base_url: HttpUrl
    province: str
    city: str
    adapter_key: str = 'generic_html'
    crawl_enabled: bool = True
    rate_limit: int = 4
    schedule_group: str = 'default'
    parser_rules: dict[str, Any] = Field(default_factory=dict)


class SiteOut(BaseModel):
    id: int
    name: str
    base_url: str
    province: str
    city: str
    adapter_key: str
    crawl_enabled: bool
    rate_limit: int
    schedule_group: str
    parser_rules: dict[str, Any]
    created_at: datetime

    model_config = {'from_attributes': True}


class SiteUpdateRequest(BaseModel):
    name: str | None = None
    province: str | None = None
    city: str | None = None
    adapter_key: str | None = None
    crawl_enabled: bool | None = None
    rate_limit: int | None = None
    schedule_group: str | None = None
    parser_rules: dict[str, Any] | None = None
