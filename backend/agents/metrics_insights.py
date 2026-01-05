"""Metrics Insights Agent - Analyzes metrics and provides forecasts."""
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from models.counselor import PipelineStage
from models.metrics import Phase
from repositories.counselor_repository import CounselorRepository
from repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)


async def run_metrics_insights_agent(
    input_data: dict[str, Any],
    metrics_repo: MetricsRepository,
    counselor_repo: CounselorRepository,
) -> dict[str, Any]:
    """Run metrics insights agent.

    Args:
        input_data: Optional analysis_type (overview, forecast, alerts)
        metrics_repo: Metrics repository
        counselor_repo: Counselor repository

    Returns:
        Metrics analysis and insights
    """
    analysis_type = input_data.get("analysis_type", "overview")

    # Get current metrics
    current = await metrics_repo.get_current()
    if not current:
        return {
            "output": {"error": "Metrics not initialized"},
            "recommendations": ["Initialize metrics tracking"],
        }

    # Get weekly metrics
    weekly_metrics = await metrics_repo.get_all_weekly(Phase.PHASE_1)

    # Get counselor pipeline stats
    total_counselors = await counselor_repo.count()
    pilots = await counselor_repo.count_by_stage(PipelineStage.PILOT)
    active = await counselor_repo.count_by_stage(PipelineStage.ACTIVE)
    discovery = await counselor_repo.count_by_stage(PipelineStage.DISCOVERY)
    demo = await counselor_repo.count_by_stage(PipelineStage.DEMO_SCHEDULED) + await counselor_repo.count_by_stage(PipelineStage.DEMO_COMPLETED)

    # Build context
    metrics_context = f"""Current Metrics (Week {current.current_week}):
- Total Counselors: {total_counselors}
- In Discovery: {discovery}
- Demos: {demo}
- Pilots Onboarded: {current.total_pilots_onboarded}
- Active Pilots: {current.active_pilots}
- NPS: {current.current_nps if current.current_nps else 'N/A'}
- Weekly Active Rate: {current.current_weekly_active_rate}%
- Referrals: {current.total_referrals}
- Feedback Items: {current.total_feedback_items}

Phase 1 Targets:
- Pilots: {current.phase1_targets.pilots_onboarded_min}-{current.phase1_targets.pilots_onboarded_max}
- NPS: ≥{current.phase1_targets.nps_target}
- Weekly Active: ≥{current.phase1_targets.weekly_active_rate_target}%
- Referrals: ≥{current.phase1_targets.referrals_target}
- Feedback: ≥{current.phase1_targets.feedback_items_target}

Weekly Trend ({len(weekly_metrics)} weeks tracked):
{chr(10).join([f"Week {w.week_number}: {w.total_demos} demos, {w.pilots_onboarded} pilots" for w in weekly_metrics[-3:]])}
"""

    # Generate insights
    settings = get_settings()
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        temperature=0.7,
    )

    if analysis_type == "overview":
        user_prompt = f"""{metrics_context}

Provide a comprehensive analysis:
1. Overall progress toward Phase 1 targets
2. Strengths (what's working well)
3. Concerns (what needs attention)
4. Trend analysis (improving or declining)
5. 3-5 actionable recommendations"""

    elif analysis_type == "forecast":
        user_prompt = f"""{metrics_context}

Based on current trends, forecast:
1. Will we hit Phase 1 targets by week 8?
2. Which metrics are on track, which are at risk?
3. What needs to accelerate to hit targets?
4. Recommended actions for the next 2 weeks"""

    else:  # alerts
        user_prompt = f"""{metrics_context}

Identify urgent issues requiring immediate attention:
1. Any metrics significantly behind target?
2. Negative trends that need intervention?
3. Critical actions needed this week?"""

    system_prompt = """You are a metrics analyst for a product launch.
Provide data-driven insights with specific numbers and actionable recommendations.
Be honest about both progress and challenges."""

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

    return {
        "output": {
            "analysis_type": analysis_type,
            "current_week": current.current_week,
            "pilots_onboarded": current.total_pilots_onboarded,
            "target_pilots": f"{current.phase1_targets.pilots_onboarded_min}-{current.phase1_targets.pilots_onboarded_max}",
            "nps": current.current_nps,
            "target_nps": current.phase1_targets.nps_target,
            "insights": response.content,
        },
        "recommendations": recommendations if recommendations else [response.content],
    }
