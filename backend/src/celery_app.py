"""Resonance Engine — Celery application factory with Beat schedule."""

from celery import Celery
from celery.schedules import crontab, solar

from src.config import settings

app = Celery(
    "resonance",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="US/Eastern",
    enable_utc=True,
    task_track_started=True,
)

# Auto-discover tasks in ingestion modules
app.autodiscover_tasks(["src.ingestion.edgar", "src.ingestion.gdelt", "src.ingestion.newsapi"])

# --- Celery Beat Schedule ---
# EDGAR polling during extended market hours (Mon-Fri, 8:00 AM – 6:00 PM ET)
# SEC filings can arrive before market open and after close.
app.conf.beat_schedule = {
    "edgar-poll-8k-every-5min": {
        "task": "edgar.poll_recent_filings",
        "schedule": crontab(minute="*/5", hour="8-17", day_of_week="1-5"),
        "args": ("8-K", 100),
        "options": {"queue": "edgar"},
    },
    "edgar-poll-10k-hourly": {
        "task": "edgar.poll_recent_filings",
        "schedule": crontab(minute="0", hour="9-16", day_of_week="1-5"),
        "args": ("10-K", 50),
        "options": {"queue": "edgar"},
    },
    "edgar-poll-form4-every-10min": {
        "task": "edgar.poll_recent_filings",
        "schedule": crontab(minute="*/10", hour="8-17", day_of_week="1-5"),
        "args": ("4", 100),
        "options": {"queue": "edgar"},
    },
}
