from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class NoticeSeed:
    title: str
    detail_url: str
    publish_time: datetime | None = None
    source_notice_id: str | None = None


@dataclass(slots=True)
class ParsedAttachment:
    file_name: str
    source_url: str
    file_type: str


@dataclass(slots=True)
class ParsedNotice:
    title: str
    source_url: str
    publish_time: datetime | None
    tender_type: str
    content_text: str
    source_notice_id: str | None = None
    attachments: list[ParsedAttachment] = field(default_factory=list)
