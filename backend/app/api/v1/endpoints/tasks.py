from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin
from app.models.entities import CrawlJob, CrawlJobStatus, Notice, User
from app.schemas.task import CrawlJobOut, TaskStatsOut

router = APIRouter()


@router.get('', response_model=list[CrawlJobOut])
def list_tasks(db: Session = Depends(get_db_session), _: User = Depends(require_admin), limit: int = 50):
    rows = db.query(CrawlJob).order_by(CrawlJob.id.desc()).limit(limit).all()
    return [
        CrawlJobOut(
            id=row.id,
            status=row.status.value,
            trigger_type=row.trigger_type,
            filters=row.filters,
            started_at=row.started_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
            metrics=row.metrics,
            error_message=row.error_message,
        )
        for row in rows
    ]


@router.get('/stats', response_model=TaskStatsOut)
def task_stats(db: Session = Depends(get_db_session), _: User = Depends(require_admin)):
    since = datetime.utcnow() - timedelta(hours=24)
    total_jobs = db.query(func.count(CrawlJob.id)).filter(CrawlJob.created_at >= since).scalar() or 0
    success_jobs = (
        db.query(func.count(CrawlJob.id))
        .filter(CrawlJob.created_at >= since, CrawlJob.status == CrawlJobStatus.completed)
        .scalar()
        or 0
    )
    failed_jobs = (
        db.query(func.count(CrawlJob.id))
        .filter(CrawlJob.created_at >= since, CrawlJob.status == CrawlJobStatus.failed)
        .scalar()
        or 0
    )
    notices_total = db.query(func.count(Notice.id)).scalar() or 0

    return TaskStatsOut(
        last_24h_total_jobs=total_jobs,
        last_24h_success_jobs=success_jobs,
        last_24h_failed_jobs=failed_jobs,
        notices_total=notices_total,
    )
