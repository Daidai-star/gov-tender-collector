from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AttachmentOut(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    storage_path: str

    model_config = {'from_attributes': True}


class NoticeListItem(BaseModel):
    id: int
    title: str
    tender_type: str
    region_province: str
    region_city: str
    publish_time: datetime | None
    has_attachments: bool
    attachment_names: list[str] = Field(default_factory=list)
    is_favorited: bool = False
    has_ai_analysis: bool = False

    model_config = {'from_attributes': True}


class NoticeListOut(BaseModel):
    total: int
    items: list[NoticeListItem]


class AIAnalysisOut(BaseModel):
    id: int
    model: str
    status: str
    summary: str | None
    key_requirements: list[Any]
    risk_points: list[Any]
    deadline_items: list[Any]
    raw_json: dict[str, Any]
    error_message: str | None
    created_at: datetime

    model_config = {'from_attributes': True}


class NoticeDetailOut(BaseModel):
    id: int
    title: str
    source_url: str
    tender_type: str
    region_province: str
    region_city: str
    publish_time: datetime | None
    content_text: str
    attachments: list[AttachmentOut]
    is_favorited: bool = False
    latest_ai_analysis: AIAnalysisOut | None

    model_config = {'from_attributes': True}
