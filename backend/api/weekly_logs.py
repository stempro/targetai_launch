"""Weekly log API routes."""
from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_weekly_log_repository
from models.metrics import Phase
from models.weekly_log import WeeklyLog
from repositories.weekly_log_repository import WeeklyLogRepository

router = APIRouter()


@router.get("/current", response_model=WeeklyLog)
async def get_current_week_log(
    phase: Phase,
    week: int,
    repo: WeeklyLogRepository = Depends(get_weekly_log_repository),
):
    """Get or create log for current week."""
    return await repo.get_current_week_log(phase, week)


@router.get("/{phase}/{week}", response_model=WeeklyLog)
async def get_week_log(
    phase: Phase,
    week: int,
    repo: WeeklyLogRepository = Depends(get_weekly_log_repository),
):
    """Get weekly log for specific phase and week."""
    log = await repo.get_log(phase, week)
    if not log:
        raise HTTPException(
            status_code=404, detail=f"Log not found for {phase} week {week}"
        )
    return log


@router.put("/{phase}/{week}", response_model=WeeklyLog)
async def update_week_log(
    phase: Phase,
    week: int,
    log: WeeklyLog,
    repo: WeeklyLogRepository = Depends(get_weekly_log_repository),
):
    """Update weekly log."""
    log.phase = phase
    log.week_number = week
    return await repo.save_log(log)


@router.post("/", response_model=WeeklyLog, status_code=201)
async def create_week_log(
    log: WeeklyLog,
    repo: WeeklyLogRepository = Depends(get_weekly_log_repository),
):
    """Create new weekly log."""
    return await repo.save_log(log)


@router.get("/phase/{phase}", response_model=list[WeeklyLog])
async def get_all_phase_logs(
    phase: Phase,
    repo: WeeklyLogRepository = Depends(get_weekly_log_repository),
):
    """Get all weekly logs for a phase."""
    return await repo.get_all_logs(phase)
