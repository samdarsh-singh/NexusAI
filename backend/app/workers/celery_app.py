from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.scoring", "app.workers.parsing", "app.workers.tailoring"]
)

celery_app.conf.task_routes = {
    "app.workers.ingestion.fetch_jobs_task": "main-queue",
    "app.workers.scoring.score_job_task": "main-queue",
    "app.workers.scoring.score_all_jobs_task": "main-queue",
    "app.workers.parsing.parse_resume_task": "main-queue",
    "app.workers.tailoring.tailor_resume_task": "main-queue",
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
