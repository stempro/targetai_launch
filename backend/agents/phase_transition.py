"""Phase Transition Agent - Evaluates readiness for Phase 1 → Phase 2."""
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from models.metrics import Phase
from repositories.metrics_repository import MetricsRepository
from repositories.timeline_repository import TimelineRepository

logger = logging.getLogger(__name__)


async def run_phase_transition_agent(
    input_data: dict[str, Any],
    metrics_repo: MetricsRepository,
    timeline_repo: TimelineRepository,
) -> dict[str, Any]:
    """Run phase transition readiness agent.

    Args:
        input_data: Empty or with force_check flag
        metrics_repo: Metrics repository
        timeline_repo: Timeline repository

    Returns:
        Readiness assessment and decision
    """
    # Get current metrics
    current = await metrics_repo.get_current()
    if not current:
        return {
            "output": {"error": "Metrics not initialized"},
            "recommendations": ["Initialize metrics before checking readiness"],
        }

    # Get current phase
    current_phase = await timeline_repo.get_current_phase()

    # Check each Phase 1 criterion
    targets = current.phase1_targets

    criteria = {
        "pilots_onboarded": {
            "current": current.total_pilots_onboarded,
            "target": f"{targets.pilots_onboarded_min}-{targets.pilots_onboarded_max}",
            "met": targets.pilots_onboarded_min <= current.total_pilots_onboarded <= targets.pilots_onboarded_max,
            "importance": "critical",
        },
        "nps": {
            "current": current.current_nps if current.current_nps else 0,
            "target": f"≥{targets.nps_target}",
            "met": (current.current_nps >= targets.nps_target) if current.current_nps else False,
            "importance": "critical",
        },
        "weekly_active_rate": {
            "current": f"{current.current_weekly_active_rate}%" if current.current_weekly_active_rate else "N/A",
            "target": f"≥{targets.weekly_active_rate_target}%",
            "met": (current.current_weekly_active_rate >= targets.weekly_active_rate_target) if current.current_weekly_active_rate else False,
            "importance": "important",
        },
        "referrals": {
            "current": current.total_referrals,
            "target": f"≥{targets.referrals_target}",
            "met": current.total_referrals >= targets.referrals_target,
            "importance": "important",
        },
        "feedback_items": {
            "current": current.total_feedback_items,
            "target": f"≥{targets.feedback_items_target}",
            "met": current.total_feedback_items >= targets.feedback_items_target,
            "importance": "nice-to-have",
        },
        "positioning_phrases": {
            "current": current.positioning_phrases_validated,
            "target": f"≥{targets.positioning_phrases_target}",
            "met": current.positioning_phrases_validated >= targets.positioning_phrases_target,
            "importance": "nice-to-have",
        },
    }

    # Calculate readiness score
    critical_met = sum(1 for c in criteria.values() if c["importance"] == "critical" and c["met"])
    critical_total = sum(1 for c in criteria.values() if c["importance"] == "critical")

    important_met = sum(1 for c in criteria.values() if c["importance"] == "important" and c["met"])
    important_total = sum(1 for c in criteria.values() if c["importance"] == "important")

    total_met = sum(1 for c in criteria.values() if c["met"])
    total_criteria = len(criteria)

    readiness_score = (total_met / total_criteria) * 100

    # Use GPT-4o for complex reasoning about transition decision
    settings = get_settings()
    model = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.openai_api_key,
        temperature=0.3,  # Lower temperature for more consistent reasoning
    )

    criteria_summary = "\n".join([
        f"- {name}: {info['current']} (target: {info['target']}) - {'✓' if info['met'] else '✗'} [{info['importance']}]"
        for name, info in criteria.items()
    ])

    system_prompt = """You are a launch strategist making go/no-go decisions for phase transitions.

Decision Framework:
- GO: All critical criteria met, most important criteria met
- CONDITIONAL GO: Critical criteria met, some important criteria need work (acceptable with plan)
- NO GO: Critical criteria not met, or significant concerns about foundation

Be balanced: perfectionism delays progress, but rushing creates problems.
Consider: Are the critical foundations solid? Can gaps be addressed in parallel with Phase 2?"""

    user_prompt = f"""Phase 1 → Phase 2 Transition Assessment

Current Status (Week {current.current_week}):
{criteria_summary}

Overall Readiness: {readiness_score:.1f}%
Critical Criteria: {critical_met}/{critical_total} met
Important Criteria: {important_met}/{important_total} met

Based on this data, provide:
1. Decision: GO / CONDITIONAL GO / NO GO
2. Reasoning (2-3 sentences)
3. If CONDITIONAL GO or NO GO, what gaps must be addressed?
4. Timeline impact (can start Phase 2 now, need 1-2 weeks, need significant delay)
5. 3-5 specific actions to take before/during Phase 2"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await model.invoke(messages)

    # Parse decision
    decision_text = response.content
    if "GO" in decision_text.split("\n")[0].upper():
        if "CONDITIONAL" in decision_text.split("\n")[0].upper():
            decision = "CONDITIONAL_GO"
        elif "NO GO" in decision_text.split("\n")[0].upper() or "NO-GO" in decision_text.split("\n")[0].upper():
            decision = "NO_GO"
        else:
            decision = "GO"
    else:
        decision = "NO_GO"

    return {
        "output": {
            "decision": decision,
            "readiness_score": round(readiness_score, 1),
            "criteria_met": total_met,
            "total_criteria": total_criteria,
            "critical_met": f"{critical_met}/{critical_total}",
            "important_met": f"{important_met}/{important_total}",
            "criteria_details": criteria,
            "analysis": response.content,
            "current_week": current.current_week,
        },
        "recommendations": [
            line.strip("- ").strip()
            for line in decision_text.split("\n")
            if line.strip().startswith("-") or line.strip().startswith("•") or line.strip().startswith(str(i) + ".") for i in range(1, 10)
        ][:5],  # Get top 5 recommendations
    }
