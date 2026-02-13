from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CrawlJobOut(BaseModel):
    id: int
    status: str
    trigger_type: str
    filters: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    metrics: dict[str, Any]
    error_message: str | None

    model_config = {'from_attributes': True}


class TaskStatsOut(BaseModel):
    last_24h_total_jobs: int
    last_24h_success_jobs: int
    last_24h_failed_jobs: int
    notices_total: int
