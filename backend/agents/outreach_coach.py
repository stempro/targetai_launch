"""Outreach Coach Agent - Analyzes outreach status and provides recommendations."""
import logging
from datetime import datetime, date, timedelta
from typing import Any, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from config import get_settings
from models.counselor import PipelineStage
from repositories.counselor_repository import CounselorRepository
from repositories.metrics_repository import MetricsRepository
from repositories.timeline_repository import TimelineRepository

logger = logging.getLogger(__name__)


class OutreachState(TypedDict):
    """State for outreach coach agent."""

    week_number: int
    target_volume: int
    current_connections: int
    warm_leads: list[dict]
    recommendations: list[str]
    analysis: str


async def analyze_outreach_status(
    state: OutreachState,
    counselor_repo: CounselorRepository,
    timeline_repo: TimelineRepository,
) -> OutreachState:
    """Analyze current outreach status."""
    logger.info(f"Analyzing outreach for week {state['week_number']}")

    # Get current phase info
    current_phase = await timeline_repo.get_current_phase()
    week_number = current_phase.week_number if current_phase else state["week_number"]

    # Define targets based on week (from Phase 1 action plan)
    if week_number <= 2:
        target_volume = 20  # connections/week
    elif week_number <= 4:
        target_volume = 15  # DMs/week
    else:
        target_volume = 10  # DMs/week + referrals

    # Get connected counselors (warm leads)
    connected = await counselor_repo.get_by_stage(PipelineStage.CONNECTED)
    warm_leads = [
        {
            "id": c.id,
            "name": f"{c.profile.first_name} {c.profile.last_name}",
            "score": c.scoring.total_score,
            "email": c.profile.email,
            "specialization": [s.value for s in c.metadata.specialization],
        }
        for c in connected
    ]

    # Calculate gap
    gap = target_volume - state.get("current_connections", 0)

    state["week_number"] = week_number
    state["target_volume"] = target_volume
    state["warm_leads"] = warm_leads
    state["analysis"] = f"Week {week_number}: Target {target_volume}, Current {state.get('current_connections', 0)}, Gap: {gap}"

    return state


async def generate_recommendations(
    state: OutreachState,
) -> OutreachState:
    """Generate AI-powered recommendations using Claude."""
    settings = get_settings()
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        temperature=0.7,
    )

    # Prepare context
    gap = state["target_volume"] - state.get("current_connections", 0)
    warm_leads_summary = "\n".join(
        [
            f"- {lead['name']} (score: {lead['score']}, {', '.join(lead['specialization'])})"
            for lead in state["warm_leads"][:5]
        ]
    )

    system_prompt = """You are an outreach coach for a college counseling platform launch.
Your job is to analyze the current outreach status and provide actionable recommendations.

Context:
- This is Phase 1 (Counselor Credibility Pilot)
- Goal: Onboard 10-15 high-quality counselor pilots
- Approach: Personalized, founder-led outreach
- Channels: LinkedIn (primary), professional associations, warm intros

Be specific and actionable. Focus on quality over quantity."""

    user_prompt = f"""Current Situation:
{state['analysis']}

Warm Leads Available:
{warm_leads_summary}

Gap: {gap} {'connections' if state['week_number'] <= 2 else 'outreach messages'} needed this week.

Provide 3-5 specific, actionable recommendations to hit this week's target."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await model.ainvoke(messages)

    # Parse recommendations
    recommendations_text = response.content
    recommendations = [
        line.strip("- ").strip()
        for line in recommendations_text.split("\n")
        if line.strip().startswith("-") or line.strip().startswith("•")
    ]

    state["recommendations"] = recommendations if recommendations else [recommendations_text]

    return state


# Build workflow
def create_outreach_coach_workflow(
    counselor_repo: CounselorRepository,
    timeline_repo: TimelineRepository,
) -> StateGraph:
    """Create outreach coach workflow."""
    workflow = StateGraph(OutreachState)

    # Add nodes
    workflow.add_node(
        "analyze",
        lambda s: analyze_outreach_status(s, counselor_repo, timeline_repo),
    )
    workflow.add_node("recommend", generate_recommendations)

    # Define edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "recommend")
    workflow.add_edge("recommend", END)

    return workflow.compile()


async def run_outreach_coach_agent(
    input_data: dict[str, Any],
    counselor_repo: CounselorRepository,
    metrics_repo: MetricsRepository,
    timeline_repo: TimelineRepository,
) -> dict[str, Any]:
    """Run the outreach coach agent.

    Args:
        input_data: Input data with optional current_connections count
        counselor_repo: Counselor repository
        metrics_repo: Metrics repository
        timeline_repo: Timeline repository

    Returns:
        Agent output with recommendations
    """
    # Create workflow
    workflow = create_outreach_coach_workflow(counselor_repo, timeline_repo)

    # Initial state
    initial_state: OutreachState = {
        "week_number": input_data.get("week_number", 1),
        "target_volume": 0,
        "current_connections": input_data.get("current_connections", 0),
        "warm_leads": [],
        "recommendations": [],
        "analysis": "",
    }

    # Run workflow
    result = await workflow.ainvoke(initial_state)

    return {
        "output": {
            "week_number": result["week_number"],
            "target_volume": result["target_volume"],
            "current_connections": result["current_connections"],
            "gap": result["target_volume"] - result["current_connections"],
            "warm_leads_count": len(result["warm_leads"]),
            "analysis": result["analysis"],
        },
        "recommendations": result["recommendations"],
    }
