"""Demo Prep Agent - Prepares customized demo for specific counselor."""
import logging
from typing import Any, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from models.counselor import Counselor
from repositories.counselor_repository import CounselorRepository

logger = logging.getLogger(__name__)


async def run_demo_prep_agent(
    input_data: dict[str, Any],
    counselor_repo: CounselorRepository,
) -> dict[str, Any]:
    """Run demo preparation agent.

    Args:
        input_data: Must contain 'counselor_id'
        counselor_repo: Counselor repository

    Returns:
        Customized demo script and prep notes
    """
    counselor_id = input_data.get("counselor_id")
    if not counselor_id:
        raise ValueError("counselor_id required")

    # Get counselor
    counselor = await counselor_repo.get_by_id(counselor_id)
    if not counselor:
        raise ValueError(f"Counselor not found: {counselor_id}")

    # Generate customized demo prep
    settings = get_settings()
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        temperature=0.7,
    )

    system_prompt = """You are a demo preparation specialist for TargetAI, a college counseling platform.

Your job is to customize the standard 45-minute demo flow based on the counselor's specific profile,
needs, and specialization.

Standard Demo Flow:
1. (5 min) Reconnect & set expectations
2. (10 min) Student management demo
3. (10 min) AI features showcase
4. (10 min) Essay & college tools
5. (10 min) Q&A + pilot discussion

Be specific about what examples to show, which features to emphasize, and what pain points to address."""

    # Build counselor context
    counselor_context = f"""Counselor Profile:
Name: {counselor.profile.first_name} {counselor.profile.last_name}
Email: {counselor.profile.email}
Score: {counselor.scoring.total_score}/15

Specialization: {', '.join([s.value for s in counselor.metadata.specialization])}
Experience: {counselor.metadata.experience.value}
Region: {counselor.metadata.region.value}
IECA Member: {counselor.metadata.ieca_member}

Current Stage: {counselor.pipeline.stage.value}
Tags: {', '.join(counselor.tags)}
"""

    user_prompt = f"""{counselor_context}

Generate a customized demo preparation guide including:
1. Key insights about this counselor
2. Customizations to make to the standard demo
3. Specific examples to showcase (relevant to their specialization)
4. Pain points to address
5. Questions they might ask (and how to answer)
6. 3-5 talking points to emphasize"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await model.ainvoke(messages)

    return {
        "output": {
            "counselor_id": counselor_id,
            "counselor_name": f"{counselor.profile.first_name} {counselor.profile.last_name}",
            "score": counselor.scoring.total_score,
            "specialization": [s.value for s in counselor.metadata.specialization],
            "demo_prep": response.content,
        },
        "recommendations": [
            f"Focus on {', '.join([s.value for s in counselor.metadata.specialization])} features",
            "Use relevant student examples matching their specialty",
            f"Address their experience level: {counselor.metadata.experience.value}",
        ],
    }
