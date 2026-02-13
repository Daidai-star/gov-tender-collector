from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, exists, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.entities import AIAnalysisRecord, AIJobStatus, Attachment, FavoriteNotice, Notice, User
from app.schemas.notice import AIAnalysisOut, NoticeDetailOut, NoticeListItem, NoticeListOut
from app.services.queue import AI_QUEUE, enqueue

router = APIRouter()


@router.get('', response_model=NoticeListOut)
def list_notices(
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
    keyword: str | None = None,
    province: str | None = None,
    city: str | None = None,
    tender_type: str | None = None,
    has_attachments: bool | None = None,
    favorited_only: bool = False,
    analyzed_only: bool = False,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    page: int = 1,
    page_size: int = 20,
):
    conditions = []
    if keyword:
        conditions.append(
            or_(
                Notice.title.ilike(f'%{keyword}%'),
                func.to_tsvector('simple', func.coalesce(Notice.content_text, '')).op('@@')(
                    func.plainto_tsquery('simple', keyword)
                ),
            )
        )
    if province:
        conditions.append(Notice.region_province == province)
    if city:
        conditions.append(Notice.region_city == city)
    if tender_type:
        conditions.append(Notice.tender_type == tender_type)
    if has_attachments is not None:
        conditions.append(Notice.has_attachments.is_(has_attachments))
    if start_date:
        conditions.append(Notice.publish_time >= start_date)
    if end_date:
        conditions.append(Notice.publish_time <= end_date)

    query = db.query(Notice)
    if favorited_only:
        query = query.filter(
            exists().where(
                and_(
                    FavoriteNotice.notice_id == Notice.id,
                    FavoriteNotice.user_id == user.id,
                )
            )
        )
    if analyzed_only:
        query = query.filter(
            exists().where(
                and_(
                    AIAnalysisRecord.notice_id == Notice.id,
                    AIAnalysisRecord.status == AIJobStatus.done,
                )
            )
        )
    if conditions:
        query = query.filter(and_(*conditions))

    total = query.with_entities(func.count(Notice.id)).scalar() or 0
    rows = (
        query.order_by(Notice.publish_time.desc().nullslast(), Notice.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    notice_ids = [row.id for row in rows]
    favorite_notice_ids = {
        item.notice_id
        for item in db.query(FavoriteNotice.notice_id).filter(
            FavoriteNotice.user_id == user.id,
            FavoriteNotice.notice_id.in_(notice_ids if notice_ids else [-1]),
        )
    }
    analyzed_notice_ids = {
        item.notice_id
        for item in db.query(AIAnalysisRecord.notice_id)
        .filter(AIAnalysisRecord.notice_id.in_(notice_ids if notice_ids else [-1]), AIAnalysisRecord.status == AIJobStatus.done)
        .distinct()
    }

    items = [
        NoticeListItem(
            id=row.id,
            title=row.title,
            tender_type=row.tender_type,
            region_province=row.region_province,
            region_city=row.region_city,
            publish_time=row.publish_time,
            has_attachments=row.has_attachments,
            attachment_names=[att.file_name for att in row.attachments],
            is_favorited=row.id in favorite_notice_ids,
            has_ai_analysis=row.id in analyzed_notice_ids,
        )
        for row in rows
    ]
    return NoticeListOut(total=total, items=items)


@router.get('/{notice_id}', response_model=NoticeDetailOut)
def get_notice_detail(notice_id: int, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail='notice not found')

    attachments = db.query(Attachment).filter(Attachment.notice_id == notice_id).all()
    latest_ai = (
        db.query(AIAnalysisRecord)
        .filter(AIAnalysisRecord.notice_id == notice_id)
        .order_by(AIAnalysisRecord.id.desc())
        .first()
    )

    latest_ai_out = None
    if latest_ai:
        latest_ai_out = AIAnalysisOut(
            id=latest_ai.id,
            model=latest_ai.model,
            status=latest_ai.status.value,
            summary=latest_ai.summary,
            key_requirements=latest_ai.key_requirements,
            risk_points=latest_ai.risk_points,
            deadline_items=latest_ai.deadline_items,
            raw_json=latest_ai.raw_json,
            error_message=latest_ai.error_message,
            created_at=latest_ai.created_at,
        )

    return NoticeDetailOut(
        id=notice.id,
        title=notice.title,
        source_url=notice.source_url,
        tender_type=notice.tender_type,
        region_province=notice.region_province,
        region_city=notice.region_city,
        publish_time=notice.publish_time,
        content_text=notice.content_text,
        attachments=attachments,
        is_favorited=(
            db.query(FavoriteNotice)
            .filter(FavoriteNotice.notice_id == notice_id, FavoriteNotice.user_id == user.id)
            .first()
            is not None
        ),
        latest_ai_analysis=latest_ai_out,
    )


@router.post('/{notice_id}/analyze', response_model=AIAnalysisOut)
def analyze_notice(notice_id: int, db: Session = Depends(get_db_session), _: User = Depends(get_current_user)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail='notice not found')

    record = AIAnalysisRecord(
        notice_id=notice_id,
        model='deepseek',
        status=AIJobStatus.pending,
        key_requirements=[],
        risk_points=[],
        deadline_items=[],
        raw_json={},
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    enqueue(AI_QUEUE, {'type': 'ai.analyze', 'payload': {'analysis_id': record.id}})

    return AIAnalysisOut(
        id=record.id,
        model=record.model,
        status=record.status.value,
        summary=record.summary,
        key_requirements=record.key_requirements,
        risk_points=record.risk_points,
        deadline_items=record.deadline_items,
        raw_json=record.raw_json,
        error_message=record.error_message,
        created_at=record.created_at,
    )


@router.post('/{notice_id}/favorite')
def favorite_notice(notice_id: int, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail='notice not found')

    existing = db.query(FavoriteNotice).filter(FavoriteNotice.notice_id == notice_id, FavoriteNotice.user_id == user.id).first()
    if not existing:
        db.add(FavoriteNotice(user_id=user.id, notice_id=notice_id))
        db.commit()
    return {'favorited': True}


@router.delete('/{notice_id}/favorite')
def unfavorite_notice(notice_id: int, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    existing = db.query(FavoriteNotice).filter(FavoriteNotice.notice_id == notice_id, FavoriteNotice.user_id == user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {'favorited': False}
