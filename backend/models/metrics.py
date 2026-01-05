"""Metrics data models."""
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


class MetricCategory(str, Enum):
    """Metric categories."""
    OUTREACH = "outreach"
    CONVERSION = "conversion"
    ENGAGEMENT = "engagement"
    SATISFACTION = "satisfaction"
    REFERRALS = "referrals"


class DailyMetrics(BaseModel):
    """Daily metrics snapshot."""
    date: date
    phase: Phase
    week_number: int = Field(..., ge=1)

    # Outreach metrics
    linkedin_connections_made: int = Field(default=0, ge=0)
    linkedin_dms_sent: int = Field(default=0, ge=0)
    emails_sent: int = Field(default=0, ge=0)
    content_posts: int = Field(default=0, ge=0)

    # Conversion metrics
    discovery_calls_scheduled: int = Field(default=0, ge=0)
    discovery_calls_completed: int = Field(default=0, ge=0)
    demo_sessions_scheduled: int = Field(default=0, ge=0)
    demo_sessions_completed: int = Field(default=0, ge=0)
    pilots_onboarded: int = Field(default=0, ge=0)

    # Engagement metrics
    active_pilots: int = Field(default=0, ge=0)
    check_ins_completed: int = Field(default=0, ge=0)

    # Satisfaction metrics
    nps_responses: int = Field(default=0, ge=0)
    nps_score: Optional[float] = Field(None, ge=-100, le=100)

    # Referrals
    referrals_received: int = Field(default=0, ge=0)

    # Feature feedback
    feedback_items_submitted: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    etag: Optional[str] = None


class WeeklyMetrics(BaseModel):
    """Weekly metrics rollup."""
    week_number: int = Field(..., ge=1)
    week_start_date: date
    week_end_date: date
    phase: Phase

    # Cumulative for week
    total_connections: int = Field(default=0, ge=0)
    total_dms: int = Field(default=0, ge=0)
    total_calls: int = Field(default=0, ge=0)
    total_demos: int = Field(default=0, ge=0)

    # Current state at end of week
    pilots_onboarded: int = Field(default=0, ge=0)
    active_pilots: int = Field(default=0, ge=0)

    # Conversion rates
    response_rate: Optional[float] = Field(None, ge=0, le=100, description="% of DMs with response")
    demo_conversion_rate: Optional[float] = Field(
        None, ge=0, le=100, description="% of discovery calls → demo"
    )
    pilot_conversion_rate: Optional[float] = Field(
        None, ge=0, le=100, description="% of demos → pilot"
    )

    # Engagement
    weekly_active_rate: Optional[float] = Field(
        None, ge=0, le=100, description="% of pilots active this week"
    )

    # Satisfaction
    nps_score: Optional[float] = Field(None, ge=-100, le=100)
    nps_promoters: int = Field(default=0, ge=0, description="Scores 9-10")
    nps_passives: int = Field(default=0, ge=0, description="Scores 7-8")
    nps_detractors: int = Field(default=0, ge=0, description="Scores 0-6")

    # Referrals
    referrals_received: int = Field(default=0, ge=0)

    # On track?
    on_track: bool = Field(default=True)
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    etag: Optional[str] = None


class Phase1Targets(BaseModel):
    """Phase 1 (Credibility Pilot) success criteria targets."""
    pilots_onboarded_min: int = Field(default=10)
    pilots_onboarded_max: int = Field(default=15)
    nps_target: float = Field(default=8.0)
    weekly_active_rate_target: float = Field(default=70.0)
    referrals_target: int = Field(default=10)
    feedback_items_target: int = Field(default=30)
    positioning_phrases_target: int = Field(default=3)


class Phase2Targets(BaseModel):
    """Phase 2 (Firm Distribution) success criteria targets."""
    partner_firms_min: int = Field(default=3)
    partner_firms_max: int = Field(default=5)
    students_per_firm_target: int = Field(default=50)
    renewal_intent_target: float = Field(default=80.0, description="% of firms intending to renew")
    total_students_target: int = Field(default=150)


class Phase3Targets(BaseModel):
    """Phase 3 (Student Activation) success criteria targets."""
    weekly_active_rate_target: float = Field(default=60.0, description="% of students active weekly")
    time_to_first_value_minutes: int = Field(default=10, description="Minutes to first value")
    student_nps_target: float = Field(default=7.0)
    feature_adoption_rate_target: float = Field(default=70.0, description="% using core features")


class Phase4Targets(BaseModel):
    """Phase 4 (Direct Growth) success criteria targets."""
    paid_conversion_rate_target: float = Field(default=5.0, description="% of signups converting to paid")
    retention_12mo_target: float = Field(default=70.0, description="% retained after 12 months")
    monthly_signups_target: int = Field(default=500)
    cac_target: float = Field(default=50.0, description="Customer Acquisition Cost in USD")


class CurrentMetrics(BaseModel):
    """Real-time current metrics."""
    as_of: datetime = Field(default_factory=datetime.utcnow)
    current_phase: Phase
    current_week: int

    # Cumulative totals (Phase 1 focused)
    total_counselors: int = Field(default=0, ge=0)
    total_connections: int = Field(default=0, ge=0)
    total_discovery_calls: int = Field(default=0, ge=0)
    total_demos: int = Field(default=0, ge=0)
    total_pilots_onboarded: int = Field(default=0, ge=0)
    active_pilots: int = Field(default=0, ge=0)

    # Phase 2+ metrics
    partner_firms: int = Field(default=0, ge=0)
    total_students: int = Field(default=0, ge=0)
    active_students: int = Field(default=0, ge=0)

    # Phase 4+ metrics
    monthly_signups: int = Field(default=0, ge=0)
    paid_users: int = Field(default=0, ge=0)
    mrr: float = Field(default=0.0, ge=0, description="Monthly Recurring Revenue")

    # Current rates
    current_nps: Optional[float] = Field(None, ge=-100, le=100)
    current_weekly_active_rate: Optional[float] = Field(None, ge=0, le=100)

    # Referrals & feedback
    total_referrals: int = Field(default=0, ge=0)
    total_feedback_items: int = Field(default=0, ge=0)
    positioning_phrases_validated: int = Field(default=0, ge=0)

    # All phase targets
    phase1_targets: Phase1Targets = Field(default_factory=Phase1Targets)
    phase2_targets: Phase2Targets = Field(default_factory=Phase2Targets)
    phase3_targets: Phase3Targets = Field(default_factory=Phase3Targets)
    phase4_targets: Phase4Targets = Field(default_factory=Phase4Targets)

    etag: Optional[str] = None
