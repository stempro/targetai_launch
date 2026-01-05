"""Timeline and phase tracking models."""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Phase(str, Enum):
    """Launch phases."""
    PHASE_1 = "phase1"
    PHASE_2 = "phase2"
    PHASE_3 = "phase3"
    PHASE_4 = "phase4"


class MilestoneStatus(str, Enum):
    """Status of milestones."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"


class Milestone(BaseModel):
    """A milestone or deadline."""
    id: str
    phase: Phase
    name: str
    description: Optional[str] = None
    target_date: date
    completed_date: Optional[date] = None
    status: MilestoneStatus = Field(default=MilestoneStatus.PENDING)
    notes: Optional[str] = None


class PhaseTransition(BaseModel):
    """Record of phase transition."""
    from_phase: Optional[Phase] = None
    to_phase: Phase
    transition_date: date
    decision: str = Field(..., description="go, no-go, conditional-go")
    readiness_score: float = Field(..., ge=0, le=100, description="% of criteria met")
    notes: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CurrentPhase(BaseModel):
    """Current phase information."""
    phase: Phase
    week_number: int = Field(..., ge=1)
    phase_start_date: date
    current_date: date = Field(default_factory=date.today)
    days_in_phase: int = Field(default=0, ge=0)

    # Week boundaries (calculated from phase_start_date and week_number)
    week_start_date: Optional[date] = None
    week_end_date: Optional[date] = None

    # Calculated
    weeks_remaining_in_phase: Optional[int] = None
    on_schedule: bool = Field(default=True)

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    etag: Optional[str] = None


class TimelineData(BaseModel):
    """Complete timeline data."""
    current_phase: CurrentPhase
    milestones: list[Milestone] = Field(default_factory=list)
    phase_history: list[PhaseTransition] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    etag: Optional[str] = None
