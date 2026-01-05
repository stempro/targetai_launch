"""Counselor data models."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class ExperienceLevel(str, Enum):
    """Counselor experience level."""
    NEWER = "newer"  # <5 years
    VETERAN = "veteran"  # 5+ years


class Region(str, Enum):
    """Geographic region."""
    WEST_COAST = "west-coast"
    EAST_COAST = "east-coast"
    MIDWEST = "midwest"
    SOUTH = "south"
    INTERNATIONAL = "international"


class Specialization(str, Enum):
    """Counselor specialization areas."""
    STEM = "stem"
    ENGINEERING = "engineering"
    BUSINESS = "business"
    ARTS = "arts"
    LIBERAL_ARTS = "liberal-arts"
    ATHLETICS = "athletics"
    GENERAL = "general"


class PipelineStage(str, Enum):
    """Counselor pipeline stages."""
    TARGET = "target"
    CONNECTED = "connected"
    DISCOVERY = "discovery"
    DEMO_SCHEDULED = "demo_scheduled"
    DEMO_COMPLETED = "demo_completed"
    PILOT = "pilot"
    ACTIVE = "active"
    ADVOCATE = "advocate"
    CHURNED = "churned"


class CounselorProfile(BaseModel):
    """Counselor profile information."""
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    linkedin_url: Optional[HttpUrl] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None


class CounselorScoring(BaseModel):
    """Counselor scoring based on selection criteria."""
    active_caseload: int = Field(..., ge=1, le=3, description="1: 10-20, 2: 20-40, 3: 40+")
    tech_stack: int = Field(..., ge=1, le=3, description="1: Basic, 2: Moderate, 3: Advanced")
    feedback_commitment: int = Field(
        ..., ge=1, le=3, description="1: Monthly, 2: Bi-weekly, 3: Weekly"
    )
    industry_influence: int = Field(..., ge=1, le=3, description="1: Low, 2: Medium, 3: High")
    ethical_alignment: int = Field(
        ..., ge=1, le=3, description="1: Unclear, 2: Aligned, 3: Champion"
    )
    total_score: int = Field(default=0, ge=0, le=15)
    max_score: int = Field(default=15)
    notes: Optional[str] = None

    def calculate_total(self) -> int:
        """Calculate total score."""
        return (
            self.active_caseload
            + self.tech_stack
            + self.feedback_commitment
            + self.industry_influence
            + self.ethical_alignment
        )


class CounselorMetadata(BaseModel):
    """Counselor metadata and attributes."""
    experience: ExperienceLevel
    region: Region
    specialization: list[Specialization] = Field(default_factory=list)
    student_demographics: str = Field(
        default="general", description="affluent, middle-income, scholarship-focused, etc."
    )
    social_presence: str = Field(
        default="low", description="low (<500), medium (500-1000), high (1000+)"
    )
    ieca_member: bool = Field(default=False)
    heca_member: bool = Field(default=False)
    former_admissions_officer: bool = Field(default=False)


class StageHistory(BaseModel):
    """Pipeline stage transition history."""
    stage: PipelineStage
    date: datetime
    notes: Optional[str] = None


class NextAction(BaseModel):
    """Next scheduled action for counselor."""
    type: str = Field(..., description="discovery_call, demo_session, check_in, etc.")
    scheduled_for: Optional[datetime] = None
    notes: Optional[str] = None
    completed: bool = Field(default=False)


class CounselorPipeline(BaseModel):
    """Counselor pipeline tracking."""
    stage: PipelineStage
    stage_history: list[StageHistory] = Field(default_factory=list)
    next_action: Optional[NextAction] = None


class CounselorReferrals(BaseModel):
    """Counselor referral tracking."""
    referred_by: Optional[str] = None  # counselor_id
    has_referred: list[str] = Field(default_factory=list)  # list of counselor_ids


class Counselor(BaseModel):
    """Complete counselor data model."""
    id: str = Field(..., description="Unique counselor identifier")
    profile: CounselorProfile
    scoring: CounselorScoring
    metadata: CounselorMetadata
    pipeline: CounselorPipeline
    interactions: list[str] = Field(
        default_factory=list, description="List of interaction IDs"
    )
    referrals: CounselorReferrals = Field(default_factory=CounselorReferrals)
    red_flags: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    etag: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing."""
        # Calculate total score
        self.scoring.total_score = self.scoring.calculate_total()
        # Update timestamp
        self.updated_at = datetime.utcnow()
