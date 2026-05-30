from celery import Celery
from celery.signals import worker_ready
from prometheus_client import start_http_server

from app.core.config import settings

celery_app = Celery(
    "llm_gateway",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.chat"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)


@worker_ready.connect
def start_worker_metrics_server(**_kwargs: object) -> None:
    start_http_server(9100)
