"""Metrics API routes."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_metrics_repository
from models.metrics import CurrentMetrics, DailyMetrics, Phase, WeeklyMetrics
from repositories.metrics_repository import MetricsRepository

router = APIRouter()


@router.get("/current", response_model=CurrentMetrics)
async def get_current_metrics(
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Get current real-time metrics."""
    metrics = await repo.get_current()
    if not metrics:
        raise HTTPException(status_code=404, detail="Current metrics not initialized")
    return metrics


@router.put("/current", response_model=CurrentMetrics)
async def update_current_metrics(
    metrics: CurrentMetrics,
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Update current metrics."""
    return await repo.save_current(metrics)


@router.get("/daily/{target_date}", response_model=DailyMetrics)
async def get_daily_metrics(
    target_date: date,
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Get daily metrics for a specific date."""
    metrics = await repo.get_daily(target_date)
    if not metrics:
        raise HTTPException(
            status_code=404, detail=f"No metrics found for {target_date}"
        )
    return metrics


@router.post("/daily", response_model=DailyMetrics, status_code=201)
async def create_daily_metrics(
    metrics: DailyMetrics,
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Save daily metrics."""
    return await repo.save_daily(metrics)


@router.get("/weekly/{week_number}", response_model=WeeklyMetrics)
async def get_weekly_metrics(
    week_number: int,
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Get weekly metrics."""
    metrics = await repo.get_weekly(week_number)
    if not metrics:
        raise HTTPException(
            status_code=404, detail=f"No metrics found for week {week_number}"
        )
    return metrics


@router.post("/weekly", response_model=WeeklyMetrics, status_code=201)
async def create_weekly_metrics(
    metrics: WeeklyMetrics,
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Save weekly metrics."""
    return await repo.save_weekly(metrics)


@router.get("/weekly/all/{phase}", response_model=list[WeeklyMetrics])
async def get_all_weekly_metrics(
    phase: Phase,
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Get all weekly metrics for a phase."""
    return await repo.get_all_weekly(phase=phase)


@router.get("/phase1/summary")
async def get_phase1_summary(
    repo: MetricsRepository = Depends(get_metrics_repository),
):
    """Get Phase 1 summary with all metrics."""
    return await repo.get_phase1_summary()
