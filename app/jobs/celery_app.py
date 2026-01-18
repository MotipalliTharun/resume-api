from celery import Celery
from config import settings

celery_app = Celery(
    "resume_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.task_routes = {
    "jobs.tasks.tailor_async": {"queue": "tailor"},
}
