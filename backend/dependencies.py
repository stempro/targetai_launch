"""FastAPI dependency injection."""
from functools import lru_cache

from config import get_settings
from repositories.counselor_repository import CounselorRepository
from repositories.interaction_repository import InteractionRepository
from repositories.metrics_repository import MetricsRepository
from repositories.timeline_repository import TimelineRepository
from repositories.weekly_log_repository import WeeklyLogRepository
from storage.blob_client import BlobStorageClient


@lru_cache
def get_storage_client() -> BlobStorageClient:
    """Get cached blob storage client.

    Returns:
        Blob storage client instance
    """
    settings = get_settings()
    return BlobStorageClient(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_storage_container_name,
    )


def get_counselor_repository() -> CounselorRepository:
    """Get counselor repository instance.

    Returns:
        CounselorRepository instance
    """
    storage = get_storage_client()
    return CounselorRepository(storage)


def get_interaction_repository() -> InteractionRepository:
    """Get interaction repository instance.

    Returns:
        InteractionRepository instance
    """
    storage = get_storage_client()
    return InteractionRepository(storage)


def get_metrics_repository() -> MetricsRepository:
    """Get metrics repository instance.

    Returns:
        MetricsRepository instance
    """
    storage = get_storage_client()
    return MetricsRepository(storage)


def get_timeline_repository() -> TimelineRepository:
    """Get timeline repository instance.

    Returns:
        TimelineRepository instance
    """
    storage = get_storage_client()
    return TimelineRepository(storage)


def get_weekly_log_repository() -> WeeklyLogRepository:
    """Get weekly log repository instance.

    Returns:
        WeeklyLogRepository instance
    """
    storage = get_storage_client()
    return WeeklyLogRepository(storage)
