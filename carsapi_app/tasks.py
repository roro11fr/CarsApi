# app/tasks.py
from celery import shared_task
import structlog
from django.utils import timezone
from carsapi_app.services import detect_and_log_expired_policies

logger = structlog.get_logger(__name__)
@shared_task(name="app.tasks.policy_expiry_scan", max_retries=3, default_retry_delay=30)
def policy_expiry_scan():
    now = timezone.localtime()
    if now.hour != 0:   # doar în fereastra 00:00–00:59
        return 0

    try:
        created = detect_and_log_expired_policies()
        logger.info("policy_expiry_scan_done", created=created, run_date=str(timezone.localdate()))
        return created
    except Exception as exc:
        logger.error("policy_expiry_scan_failed", error=str(exc))
        raise

