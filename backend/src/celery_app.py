"""Resonance Engine — Celery application factory."""

from celery import Celery

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
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Auto-discover tasks in ingestion modules
app.autodiscover_tasks(["src.ingestion.edgar", "src.ingestion.gdelt", "src.ingestion.newsapi"])
