"""
Celery Beat schedule configuration for matching service.

Defines when periodic tasks should run:
- Daily match generation: 6 AM UTC (can be adjusted per timezone in production)
- Mutual match detection: Every 15 minutes

For production with multiple timezones, consider running match generation
hourly and filtering users whose local time is 6 AM.
"""

from celery.schedules import crontab

# Celery Beat schedule
CELERYBEAT_SCHEDULE = {
    # Generate daily matches at 6 AM UTC
    "generate-daily-matches": {
        "task": "services.matching.tasks.generate_daily_matches",
        "schedule": crontab(hour=6, minute=0),
        "options": {
            "queue": "matching",
            "priority": 8,
        },
    },
    # Check for mutual matches every 15 minutes
    "detect-mutual-matches-batch": {
        "task": "services.matching.tasks.detect_mutual_matches_batch",
        "schedule": crontab(minute="*/15"),
        "options": {
            "queue": "matching",
            "priority": 5,
        },
    },
}

# Timezone configuration
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# For multi-timezone support (production enhancement):
# Run match generation hourly and process users whose local time is 6 AM
"""
"generate-matches-by-timezone": {
    "task": "services.matching.tasks.generate_matches_for_timezone",
    "schedule": crontab(minute=0),  # Every hour
    "args": (6,),  # Target hour (6 AM local time)
},
"""
