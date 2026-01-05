"""Weekly activity log models."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.metrics import Phase


class ActivityLog(BaseModel):
    """Individual activity completion log."""
    task_id: str
    task_description: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class WeeklyLog(BaseModel):
    """Weekly activity tracking and progress log."""
    week_number: int = Field(..., ge=1)  # Remove max constraint for all phases
    phase: Phase
    week_start_date: date
    week_end_date: date

    # Activities from action plan
    activities: list[ActivityLog] = Field(default_factory=list)

    # Phase 1 metrics (counselor outreach)
    connections_made: int = Field(default=0, ge=0)
    dms_sent: int = Field(default=0, ge=0)
    discovery_calls: int = Field(default=0, ge=0)
    demos_completed: int = Field(default=0, ge=0)
    pilots_onboarded_this_week: int = Field(default=0, ge=0)
    referrals_received: int = Field(default=0, ge=0)

    # Phase 2 metrics (firm partnerships)
    firms_contacted: int = Field(default=0, ge=0)
    partnership_agreements_signed: int = Field(default=0, ge=0)
    students_onboarded_this_week: int = Field(default=0, ge=0)
    firm_demos_completed: int = Field(default=0, ge=0)

    # Phase 3 metrics (student activation)
    active_students_this_week: int = Field(default=0, ge=0)
    student_sessions: int = Field(default=0, ge=0)
    feature_adoption_events: int = Field(default=0, ge=0)
    student_feedback_collected: int = Field(default=0, ge=0)

    # Phase 4 metrics (direct growth)
    new_signups: int = Field(default=0, ge=0)
    paid_conversions: int = Field(default=0, ge=0)
    churn_count: int = Field(default=0, ge=0)
    marketing_spend: float = Field(default=0.0, ge=0)
    revenue_this_week: float = Field(default=0.0, ge=0)

    # Reflection (universal across all phases)
    wins: list[str] = Field(default_factory=list, description="This week's wins")
    challenges: list[str] = Field(default_factory=list, description="This week's challenges")
    learnings: list[str] = Field(default_factory=list, description="Key learnings")
    next_week_focus: Optional[str] = Field(None, description="What to focus on next week")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted: bool = Field(default=False, description="Whether log is finalized")
    etag: Optional[str] = None


class WeeklyReminder(BaseModel):
    """Weekly reminder settings and status."""
    enabled: bool = True
    reminder_day: str = Field(default="friday", description="Day of week for reminder")
    reminder_time: str = Field(default="17:00", description="Time for reminder (HH:MM)")
    last_reminded: Optional[datetime] = None
    email: Optional[str] = None
    slack_webhook: Optional[str] = None
