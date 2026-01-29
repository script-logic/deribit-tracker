"""
Configures Celery with Redis broker and result backend,
with proper connection pooling and error handling.
"""

from celery import Celery

from app.core import get_logger, get_settings

logger = get_logger(__name__)


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.

    Returns:
        Configured Celery instance with Redis broker.
    """
    settings = get_settings()

    celery_app = Celery(
        "deribit_tracker",
        broker=settings.redis.url,
        backend=settings.redis.url,
        include=["app.tasks.price_collection"],
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
        worker_concurrency=settings.celery.worker_concurrency,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        task_track_started=settings.celery.task_track_started,
        task_always_eager=False,
        worker_cancel_long_running_tasks_on_connection_loss=True,
    )

    if settings.celery.beat_enabled:
        celery_app.conf.beat_schedule = {
            "collect-prices-every-minute": {
                "task": "app.tasks.price_collection.collect_all_prices",
                "schedule": 60.0,
                "options": {"queue": "price_collection"},
            },
        }

    logger.info("Celery app configured")

    return celery_app


celery_app = create_celery_app()
