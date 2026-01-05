"""Metrics repository for data access."""
import logging
from datetime import date
from typing import Optional

from models.metrics import CurrentMetrics, DailyMetrics, Phase, WeeklyMetrics
from storage.blob_client import BlobStorageClient

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Repository for metrics data access."""

    def __init__(self, storage_client: BlobStorageClient):
        """Initialize repository.

        Args:
            storage_client: Azure Blob Storage client
        """
        self.storage = storage_client

    async def get_current(self) -> Optional[CurrentMetrics]:
        """Get current real-time metrics.

        Returns:
            Current metrics or None if not initialized
        """
        return await self.storage.read("metrics/current.json", CurrentMetrics)

    async def save_current(self, metrics: CurrentMetrics) -> CurrentMetrics:
        """Save current metrics.

        Args:
            metrics: Current metrics to save

        Returns:
            Saved metrics instance
        """
        await self.storage.write("metrics/current.json", metrics, etag=metrics.etag)
        logger.info("Saved current metrics")
        return metrics

    async def get_daily(self, target_date: date) -> Optional[DailyMetrics]:
        """Get daily metrics for a specific date.

        Args:
            target_date: Date to fetch metrics for

        Returns:
            Daily metrics or None if not found
        """
        date_str = target_date.isoformat()
        path = f"metrics/daily/{date_str}.json"
        return await self.storage.read(path, DailyMetrics)

    async def save_daily(self, metrics: DailyMetrics) -> DailyMetrics:
        """Save daily metrics.

        Args:
            metrics: Daily metrics to save

        Returns:
            Saved metrics instance
        """
        date_str = metrics.date.isoformat()
        path = f"metrics/daily/{date_str}.json"
        await self.storage.write(path, metrics, etag=metrics.etag)
        logger.info(f"Saved daily metrics for {date_str}")
        return metrics

    async def get_weekly(self, week_number: int) -> Optional[WeeklyMetrics]:
        """Get weekly metrics rollup.

        Args:
            week_number: Week number (1-8 for Phase 1)

        Returns:
            Weekly metrics or None if not found
        """
        path = f"metrics/weekly/week-{week_number:02d}.json"
        return await self.storage.read(path, WeeklyMetrics)

    async def save_weekly(self, metrics: WeeklyMetrics) -> WeeklyMetrics:
        """Save weekly metrics.

        Args:
            metrics: Weekly metrics to save

        Returns:
            Saved metrics instance
        """
        path = f"metrics/weekly/week-{metrics.week_number:02d}.json"
        await self.storage.write(path, metrics, etag=metrics.etag)
        logger.info(f"Saved weekly metrics for week {metrics.week_number}")
        return metrics

    async def get_all_weekly(self, phase: Optional[Phase] = None) -> list[WeeklyMetrics]:
        """Get all weekly metrics, optionally filtered by phase.

        Args:
            phase: Optional phase filter

        Returns:
            List of weekly metrics
        """
        blobs = await self.storage.list_blobs("metrics/weekly/")
        weekly_metrics: list[WeeklyMetrics] = []

        for blob_path in blobs:
            metrics = await self.storage.read(blob_path, WeeklyMetrics)
            if metrics:
                if phase is None or metrics.phase == phase:
                    weekly_metrics.append(metrics)

        # Sort by week number
        weekly_metrics.sort(key=lambda x: x.week_number)
        return weekly_metrics

    async def get_phase1_summary(self) -> dict:
        """Get Phase 1 summary metrics.

        Returns:
            Dictionary with Phase 1 summary data
        """
        current = await self.get_current()
        if not current:
            return {}

        weekly = await self.get_all_weekly(Phase.PHASE_1)

        return {
            "current_metrics": current,
            "weekly_metrics": weekly,
            "total_weeks": len(weekly),
            "targets": current.phase1_targets if current else None,
        }
