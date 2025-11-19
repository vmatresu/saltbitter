"""
Celery application configuration for matching service.

Configures Celery with Redis broker and result backend for
distributed task processing.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "matching_service",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.matching.tasks"],
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    worker_prefetch_multiplier=1,  # One task at a time per worker
    result_expires=3600,  # Results expire after 1 hour
)

# Celery Beat schedule - runs daily match generation at 6 AM in various timezones
# For production, we'd run this hourly and process users whose local time is 6 AM
app.conf.beat_schedule = {
    "generate-daily-matches": {
        "task": "services.matching.tasks.generate_daily_matches",
        "schedule": crontab(hour=6, minute=0),  # 6 AM UTC
        "args": (),
    },
    "detect-mutual-matches": {
        "task": "services.matching.tasks.detect_mutual_matches_batch",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "args": (),
    },
}


# Optional: Configure task routes
app.conf.task_routes = {
    "services.matching.tasks.*": {"queue": "matching"},
}
