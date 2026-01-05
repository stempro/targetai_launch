"""Timeline API routes."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_timeline_repository
from models.timeline import CurrentPhase, Milestone, TimelineData
from repositories.timeline_repository import TimelineRepository

router = APIRouter()


@router.get("/current-phase", response_model=CurrentPhase)
async def get_current_phase(
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Get current phase information."""
    current = await repo.get_current_phase()
    if not current:
        raise HTTPException(status_code=404, detail="Current phase not initialized")

    # Calculate week boundaries
    if current.phase_start_date and current.week_number:
        week_offset_days = (current.week_number - 1) * 7
        current.week_start_date = current.phase_start_date + timedelta(days=week_offset_days)
        current.week_end_date = current.week_start_date + timedelta(days=6)

    return current


@router.put("/current-phase", response_model=CurrentPhase)
async def update_current_phase(
    current_phase: CurrentPhase,
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Update current phase."""
    return await repo.save_current_phase(current_phase)


@router.get("/timeline", response_model=TimelineData)
async def get_timeline(
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Get complete timeline data."""
    timeline = await repo.get_timeline()
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not initialized")
    return timeline


@router.put("/timeline", response_model=TimelineData)
async def update_timeline(
    timeline: TimelineData,
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Update complete timeline."""
    return await repo.save_timeline(timeline)


@router.get("/milestones", response_model=list[Milestone])
async def get_milestones(
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Get all milestones."""
    return await repo.get_milestones()


@router.post("/milestones", response_model=Milestone, status_code=201)
async def add_milestone(
    milestone: Milestone,
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Add a new milestone."""
    await repo.add_milestone(milestone)
    return milestone


@router.put("/milestones/{milestone_id}", response_model=Milestone)
async def update_milestone(
    milestone_id: str,
    milestone: Milestone,
    repo: TimelineRepository = Depends(get_timeline_repository),
):
    """Update a milestone."""
    milestone.id = milestone_id
    await repo.update_milestone(milestone)
    return milestone
