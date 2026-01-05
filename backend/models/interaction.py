"""Interaction data models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    """Types of interactions with counselors."""
    LINKEDIN_CONNECTION = "linkedin_connection"
    LINKEDIN_DM = "linkedin_dm"
    LINKEDIN_COMMENT = "linkedin_comment"
    EMAIL = "email"
    DISCOVERY_CALL = "discovery_call"
    DEMO_SESSION = "demo_session"
    ONBOARDING = "onboarding"
    CHECK_IN = "check_in"
    SUPPORT = "support"
    OTHER = "other"


class InteractionOutcome(str, Enum):
    """Outcome of interaction."""
    SUCCESS = "success"
    PENDING = "pending"
    NO_RESPONSE = "no_response"
    NEGATIVE = "negative"
    SCHEDULED_NEXT = "scheduled_next"


class Interaction(BaseModel):
    """Interaction with a counselor."""
    id: str = Field(..., description="Unique interaction identifier")
    counselor_id: str = Field(..., description="Associated counselor ID")
    type: InteractionType
    date: datetime = Field(default_factory=datetime.utcnow)
    outcome: Optional[InteractionOutcome] = None
    subject: Optional[str] = Field(None, description="Subject line or summary")
    notes: Optional[str] = Field(None, description="Detailed notes")
    message_sent: Optional[str] = Field(None, description="Message content if applicable")
    response_received: Optional[str] = Field(None, description="Their response if applicable")
    duration_minutes: Optional[int] = Field(None, description="Duration for calls/meetings")
    next_action: Optional[str] = Field(None, description="Follow-up action needed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    etag: Optional[str] = None
