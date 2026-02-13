import logging
import time

from app.core.database import SessionLocal
from app.core.init_db import init_db
from app.services.analysis_manager import run_ai_analysis
from app.services.crawler.manager import run_crawl_job
from app.models.entities import CrawlJob, CrawlJobStatus
from app.services.queue import AI_QUEUE, CRAWL_QUEUE, dequeue
from app.services.scheduler import CrawlScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def process_crawl_message(payload: dict):
    job_id = payload.get('job_id')
    db = SessionLocal()
    try:
        if not job_id:
            trigger_type = payload.get('trigger_type', 'scheduled')
            filters = payload.get('filters', {})
            job = CrawlJob(status=CrawlJobStatus.queued, trigger_type=trigger_type, filters=filters)
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id
        run_crawl_job(db, int(job_id))
    finally:
        db.close()


def process_ai_message(payload: dict):
    analysis_id = payload.get('analysis_id')
    if not analysis_id:
        return
    db = SessionLocal()
    try:
        run_ai_analysis(db, int(analysis_id))
    finally:
        db.close()


def loop_worker():
    init_db()
    scheduler = CrawlScheduler()
    scheduler.start()
    logging.info('worker started and scheduler registered')

    try:
        while True:
            crawl_msg = dequeue(CRAWL_QUEUE, timeout=1)
            if crawl_msg and crawl_msg.get('type') == 'crawl.run':
                process_crawl_message(crawl_msg.get('payload', {}))

            ai_msg = dequeue(AI_QUEUE, timeout=1)
            if ai_msg and ai_msg.get('type') == 'ai.analyze':
                process_ai_message(ai_msg.get('payload', {}))

            time.sleep(0.1)
    finally:
        scheduler.stop()


if __name__ == '__main__':
    loop_worker()
