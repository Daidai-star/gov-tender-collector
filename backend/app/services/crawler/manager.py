from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Attachment, CrawlJob, CrawlJobLog, CrawlJobStatus, Notice, NoticeVersion, Site
from app.services.crawler.registry import adapter_registry
from app.services.crawler.types import NoticeSeed, ParsedNotice
from app.services.storage import save_attachment
from app.services.utils import sha256_text

settings = get_settings()


def append_job_log(db: Session, job_id: int, message: str, level: str = 'INFO') -> None:
    db.add(CrawlJobLog(crawl_job_id=job_id, level=level, message=message))
    db.commit()


def run_crawl_job(db: Session, job_id: int) -> None:
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        return

    job.status = CrawlJobStatus.running
    job.started_at = datetime.utcnow()
    db.commit()

    filters = job.filters or {}
    tender_types = filters.get('tender_types')
    query = db.query(Site).filter(Site.crawl_enabled.is_(True))

    site_ids = filters.get('site_ids')
    provinces = filters.get('provinces')
    cities = filters.get('cities')

    if site_ids:
        query = query.filter(Site.id.in_(site_ids))
    if provinces:
        query = query.filter(Site.province.in_(provinces))
    if cities:
        query = query.filter(Site.city.in_(cities))

    sites = query.all()

    metrics = {
        'sites_total': len(sites),
        'notices_scanned': 0,
        'notices_inserted': 0,
        'notices_updated': 0,
        'attachments_downloaded': 0,
        'failed_sites': 0,
    }

    try:
        for site in sites:
            append_job_log(db, job.id, f'crawl site={site.name} ({site.base_url})')
            try:
                adapter = adapter_registry.get(site.adapter_key)
                seeds = adapter.list_notices(site, tender_types=tender_types)
                metrics['notices_scanned'] += len(seeds)

                parsed_notices = _parse_seeds_concurrently(adapter, site, seeds, tender_types)
                for parsed in parsed_notices:
                    if not parsed:
                        continue
                    parsed = adapter.normalize(parsed)
                    source_hash = sha256_text(parsed.source_url)
                    content_hash = sha256_text(parsed.content_text)
                    existing = db.query(Notice).filter(Notice.source_url_hash == source_hash).first()

                    if existing:
                        if existing.content_hash != content_hash:
                            existing.content_text = parsed.content_text
                            existing.content_hash = content_hash
                            existing.title = parsed.title
                            existing.tender_type = parsed.tender_type
                            existing.publish_time = parsed.publish_time
                            db.add(
                                NoticeVersion(
                                    notice_id=existing.id,
                                    content_hash=content_hash,
                                    content_text=parsed.content_text,
                                )
                            )
                            metrics['notices_updated'] += 1
                        continue

                    notice = Notice(
                        site_id=site.id,
                        title=parsed.title,
                        source_url=parsed.source_url,
                        source_url_hash=source_hash,
                        source_notice_id=parsed.source_notice_id,
                        publish_time=parsed.publish_time,
                        tender_type=parsed.tender_type,
                        region_province=site.province,
                        region_city=site.city,
                        content_text=parsed.content_text,
                        content_hash=content_hash,
                        has_attachments=bool(parsed.attachments),
                    )
                    db.add(notice)
                    db.flush()

                    for attachment in parsed.attachments:
                        try:
                            content, mime_type = adapter.download_attachment(site, attachment.source_url)
                            storage_path, file_size, digest = save_attachment(notice.id, attachment.file_name, content)
                            db.add(
                                Attachment(
                                    notice_id=notice.id,
                                    file_name=attachment.file_name,
                                    file_type=attachment.file_type or mime_type,
                                    file_size=file_size,
                                    storage_path=storage_path,
                                    sha256=digest,
                                    source_url=attachment.source_url,
                                )
                            )
                            metrics['attachments_downloaded'] += 1
                        except Exception as exc:  # noqa: BLE001
                            append_job_log(
                                db,
                                job.id,
                                f'attachment failed site={site.name} url={attachment.source_url} err={exc}',
                                level='WARN',
                            )

                    metrics['notices_inserted'] += 1
                db.commit()
            except Exception as exc:  # noqa: BLE001
                metrics['failed_sites'] += 1
                append_job_log(db, job.id, f'site failed site={site.name} err={exc}', level='ERROR')

        job.status = CrawlJobStatus.completed
        job.completed_at = datetime.utcnow()
        job.metrics = metrics
        db.commit()
    except Exception as exc:  # noqa: BLE001
        job.status = CrawlJobStatus.failed
        job.completed_at = datetime.utcnow()
        job.error_message = str(exc)
        job.metrics = metrics
        db.commit()
        append_job_log(db, job.id, f'job failed err={exc}', level='ERROR')


def _parse_seeds_concurrently(adapter, site: Site, seeds: list[NoticeSeed], tender_types: list[str] | None) -> list[ParsedNotice]:
    max_workers = max(1, min(site.rate_limit or settings.crawl_site_concurrency, settings.crawl_global_concurrency))
    parsed_results: list[ParsedNotice] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(adapter.parse_notice, site, seed, tender_types): seed
            for seed in seeds
        }
        for future in as_completed(future_map):
            try:
                parsed = future.result()
                if parsed:
                    parsed_results.append(parsed)
            except Exception:
                continue
    return parsed_results
