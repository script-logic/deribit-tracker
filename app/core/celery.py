"""
Celery configuration for background task processing.

Configures Celery with Redis broker and result backend,
with proper connection pooling and error handling.
"""

from celery import Celery

from . import get_logger, settings

logger = get_logger(__name__)


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.

    Returns:
        Configured Celery instance with Redis broker.
    """
    celery_app = Celery(
        "deribit_tracker",
        broker=settings.redis.url,
        backend=settings.redis.url,
        include=["app.tasks.price_collection"],
    )

    worker_concurrency = getattr(
        settings,
        "celery_worker_concurrency",
        2 if settings.application.debug else 4,
    )

    beat_enabled = getattr(
        settings,
        "celery_beat_enabled",
        True,
    )

    task_track_started = getattr(
        settings,
        "celery_task_track_started",
        True,
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=5,
        task_default_queue="default",
        task_routes={
            "app.tasks.price_collection.*": {"queue": "price_collection"},
        },
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_max_tasks_per_child=1000,
        worker_concurrency=worker_concurrency,
        task_track_started=task_track_started,
    )

    if beat_enabled:
        celery_app.conf.beat_schedule = {
            "collect-prices-every-minute": {
                "task": "app.tasks.price_collection.collect_all_prices",
                "schedule": 60.0,
                "options": {"queue": "price_collection"},
            },
        }

    logger.info(
        "Celery app configured with Redis: %s:%s",
        settings.redis.host,
        settings.redis.port,
    )
    logger.info(
        "Celery settings: concurrency=%s, beat_enabled=%s",
        worker_concurrency,
        beat_enabled,
    )

    return celery_app


celery_app = create_celery_app()
