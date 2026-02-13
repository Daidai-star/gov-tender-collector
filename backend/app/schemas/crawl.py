from pydantic import BaseModel


class CrawlRunRequest(BaseModel):
    site_ids: list[int] | None = None
    provinces: list[str] | None = None
    cities: list[str] | None = None
    tender_types: list[str] | None = None


class CrawlRunResponse(BaseModel):
    job_id: int
    status: str
