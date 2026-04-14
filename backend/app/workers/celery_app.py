from celery import Celery
from app.config import settings

celery_app = Celery(
    "jsw_msme",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.campaign_tasks",
        "app.workers.followup_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Retry failed Salesforce syncs every 15 minutes
        "sf-retry-every-15min": {
            "task": "app.workers.followup_tasks.retry_failed_sf_syncs",
            "schedule": 900.0,
        },
        # Send scheduled campaigns at their scheduled_at time (checked every minute)
        "check-scheduled-campaigns": {
            "task": "app.workers.campaign_tasks.dispatch_scheduled_campaigns",
            "schedule": 60.0,
        },
    },
)
