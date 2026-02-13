from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.services.queue import CRAWL_QUEUE, enqueue

settings = get_settings()


class CrawlScheduler:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone=settings.timezone)

    def start(self) -> None:
        hours = [h.strip() for h in settings.crawl_schedule_hours.split(',') if h.strip()]
        for hour in hours:
            self.scheduler.add_job(
                self.enqueue_scheduled_crawl,
                trigger=CronTrigger(hour=hour, minute=0),
                id=f'scheduled-crawl-{hour}',
                replace_existing=True,
            )
        self.scheduler.start()

    def enqueue_scheduled_crawl(self) -> None:
        enqueue(CRAWL_QUEUE, {'type': 'crawl.run', 'payload': {'trigger_type': 'scheduled', 'filters': {}}})

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
