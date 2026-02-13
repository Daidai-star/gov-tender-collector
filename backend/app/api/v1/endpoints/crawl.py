from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin
from app.models.entities import CrawlJob, CrawlJobStatus, User
from app.schemas.crawl import CrawlRunRequest, CrawlRunResponse
from app.services.queue import CRAWL_QUEUE, enqueue

router = APIRouter()


@router.post('/run', response_model=CrawlRunResponse)
def run_crawl(
    payload: CrawlRunRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    job = CrawlJob(
        status=CrawlJobStatus.queued,
        trigger_type='manual',
        filters={
            'site_ids': payload.site_ids,
            'provinces': payload.provinces,
            'cities': payload.cities,
            'tender_types': payload.tender_types,
        },
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    enqueue(CRAWL_QUEUE, {'type': 'crawl.run', 'payload': {'job_id': job.id}})
    return CrawlRunResponse(job_id=job.id, status=job.status.value)
