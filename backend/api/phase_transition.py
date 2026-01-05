"""Phase transition API routes."""
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dependencies import (
    get_metrics_repository,
    get_timeline_repository,
)
from models.timeline import Phase, PhaseTransition

router = APIRouter()


class TransitionRequest(BaseModel):
    """Request to transition to next phase."""
    to_phase: Phase
    decision: str = Field(..., description="go, no-go, conditional-go")
    readiness_score: float = Field(..., ge=0, le=100)
    notes: str


class TransitionResponse(BaseModel):
    """Response from phase transition."""
    success: bool
    message: str
    new_phase: Phase
    transition_record: dict[str, Any]


@router.post("/evaluate", response_model=dict[str, Any])
async def evaluate_phase_readiness(
    metrics_repo=Depends(get_metrics_repository),
    timeline_repo=Depends(get_timeline_repository),
):
    """Evaluate readiness to transition from current phase to next phase."""

    # Get current metrics and phase
    metrics = await metrics_repo.get_current()
    if not metrics:
        raise HTTPException(status_code=404, detail="Current metrics not found")

    current_timeline = await timeline_repo.get_current_phase()
    if not current_timeline:
        raise HTTPException(status_code=404, detail="Current phase not found")

    current_phase = current_timeline.phase
    phase_num = int(current_phase.value.replace('phase', ''))

    # Phase 1 → Phase 2 criteria
    if current_phase == Phase.PHASE_1:
        criteria = {
            "nps_achieved": {
                "met": (metrics.current_nps or 0) >= metrics.phase1_targets.nps_target,
                "current": metrics.current_nps or 0,
                "target": metrics.phase1_targets.nps_target,
                "description": "NPS Score",
            },
            "pilots_onboarded": {
                "met": metrics.total_pilots_onboarded >= metrics.phase1_targets.pilots_onboarded_min,
                "current": metrics.total_pilots_onboarded,
                "target": f"{metrics.phase1_targets.pilots_onboarded_min}-{metrics.phase1_targets.pilots_onboarded_max}",
                "description": "Pilots Onboarded",
            },
            "referrals": {
                "met": metrics.total_referrals >= metrics.phase1_targets.referrals_target,
                "current": metrics.total_referrals,
                "target": metrics.phase1_targets.referrals_target,
                "description": "Organic Referrals",
            },
        }

    # Phase 2 → Phase 3 criteria
    elif current_phase == Phase.PHASE_2:
        criteria = {
            "partner_firms": {
                "met": metrics.partner_firms >= metrics.phase2_targets.partner_firms_min,
                "current": metrics.partner_firms,
                "target": f"{metrics.phase2_targets.partner_firms_min}-{metrics.phase2_targets.partner_firms_max}",
                "description": "Partner Firms",
            },
            "total_students": {
                "met": metrics.total_students >= metrics.phase2_targets.total_students_target,
                "current": metrics.total_students,
                "target": metrics.phase2_targets.total_students_target,
                "description": "Total Students",
            },
        }

    # Phase 3 → Phase 4 criteria
    elif current_phase == Phase.PHASE_3:
        criteria = {
            "weekly_active_rate": {
                "met": (metrics.current_weekly_active_rate or 0) >= metrics.phase3_targets.weekly_active_rate_target,
                "current": f"{metrics.current_weekly_active_rate or 0}%",
                "target": f"{metrics.phase3_targets.weekly_active_rate_target}%",
                "description": "Weekly Active Rate",
            },
        }

    else:
        return {
            "current_phase": current_phase,
            "can_transition": False,
            "message": "Already in final phase (Phase 4)",
        }

    # Calculate readiness
    criteria_met = sum(1 for c in criteria.values() if c["met"])
    total_criteria = len(criteria)
    readiness_score = (criteria_met / total_criteria) * 100 if total_criteria > 0 else 0

    return {
        "current_phase": current_phase,
        "next_phase": f"phase{phase_num + 1}",
        "readiness_score": readiness_score,
        "criteria": criteria,
        "criteria_met": criteria_met,
        "total_criteria": total_criteria,
        "can_transition": readiness_score >= 70,  # 70% threshold
        "recommendation": "Go" if readiness_score >= 80 else "Conditional Go" if readiness_score >= 60 else "No-Go",
    }


@router.post("/transition", response_model=TransitionResponse)
async def transition_phase(
    request: TransitionRequest,
    metrics_repo=Depends(get_metrics_repository),
    timeline_repo=Depends(get_timeline_repository),
):
    """Execute phase transition."""

    # Get current phase
    current_timeline = await timeline_repo.get_current_phase()
    if not current_timeline:
        raise HTTPException(status_code=404, detail="Current phase not found")

    current_phase = current_timeline.phase

    # Validate transition
    current_num = int(current_phase.value.replace('phase', ''))
    target_num = int(request.to_phase.value.replace('phase', ''))

    if target_num != current_num + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Can only transition to next sequential phase. Current: {current_phase}, Requested: {request.to_phase}"
        )

    # Record transition
    transition = PhaseTransition(
        from_phase=current_phase,
        to_phase=request.to_phase,
        transition_date=date.today(),
        decision=request.decision,
        readiness_score=request.readiness_score,
        notes=request.notes,
    )

    # Update current phase
    await timeline_repo.transition_phase(request.to_phase, transition)

    # Update metrics current phase
    metrics = await metrics_repo.get_current()
    if metrics:
        metrics.current_phase = request.to_phase
        metrics.current_week = 1  # Reset to week 1 of new phase
        await metrics_repo.update_current(metrics)

    return TransitionResponse(
        success=True,
        message=f"Successfully transitioned from {current_phase} to {request.to_phase}",
        new_phase=request.to_phase,
        transition_record=transition.dict(),
    )


@router.get("/history")
async def get_transition_history(
    timeline_repo=Depends(get_timeline_repository),
):
    """Get history of all phase transitions."""
    timeline_data = await timeline_repo.get_timeline()
    if not timeline_data:
        return {"transitions": []}

    return {
        "transitions": [t.dict() for t in timeline_data.phase_history],
        "current_phase": timeline_data.current_phase.phase,
    }
