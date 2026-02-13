from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.entities import AIAnalysisRecord, AIJobStatus, Attachment, Notice
from app.services.ai.deepseek import DeepSeekClient


def run_ai_analysis(db: Session, analysis_id: int) -> None:
    record = db.query(AIAnalysisRecord).filter(AIAnalysisRecord.id == analysis_id).first()
    if not record:
        return

    notice = db.query(Notice).filter(Notice.id == record.notice_id).first()
    if not notice:
        record.status = AIJobStatus.failed
        record.error_message = 'notice not found'
        db.commit()
        return

    record.status = AIJobStatus.running
    record.updated_at = datetime.utcnow()
    db.commit()

    attachment_texts: list[str] = []
    for attachment in db.query(Attachment).filter(Attachment.notice_id == notice.id).all():
        path = Path(attachment.storage_path)
        if not path.exists():
            continue
        try:
            if attachment.file_type.lower() in ('txt', 'md', 'csv', 'json'):
                attachment_texts.append(path.read_text(encoding='utf-8', errors='ignore'))
            else:
                attachment_texts.append(f'文件名: {attachment.file_name}，类型: {attachment.file_type}，大小: {attachment.file_size}')
        except Exception:  # noqa: BLE001
            continue

    client = DeepSeekClient()
    try:
        result = client.analyze(notice.content_text, attachment_texts)
        record.raw_json = result
        record.summary = result.get('summary')
        record.key_requirements = result.get('qualification_requirements', [])
        record.risk_points = result.get('risk_points', [])
        record.deadline_items = result.get('action_checklist', [])
        record.status = AIJobStatus.done
        record.updated_at = datetime.utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001
        record.status = AIJobStatus.failed
        record.error_message = str(exc)
        record.updated_at = datetime.utcnow()
        db.commit()
