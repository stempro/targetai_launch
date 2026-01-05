"""AI Agent API routes."""
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agents.task_advisor import get_task_recommendation
from dependencies import (
    get_counselor_repository,
    get_metrics_repository,
    get_timeline_repository,
)

router = APIRouter()


class AgentRequest(BaseModel):
    """Generic agent request."""

    agent_type: str
    input: dict[str, Any]


class AgentResponse(BaseModel):
    """Generic agent response."""

    agent_type: str
    output: dict[str, Any]
    recommendations: list[str] = []


@router.post("/outreach-coach", response_model=AgentResponse)
async def run_outreach_coach(
    request: AgentRequest,
    counselor_repo=Depends(get_counselor_repository),
    metrics_repo=Depends(get_metrics_repository),
    timeline_repo=Depends(get_timeline_repository),
):
    """Run outreach coach agent.

    Analyzes current outreach status and provides recommendations.
    """
    # Check if this is a task recommendation request
    if request.input.get("request_type") == "task_recommendation":
        task_desc = request.input.get("task_description", "")
        recommendation = await get_task_recommendation(task_desc)
        return AgentResponse(
            agent_type="task_advisor",
            output={"recommendations": recommendation},
            recommendations=[recommendation],
        )

    # Import agent here to avoid circular imports
    from agents.outreach_coach import run_outreach_coach_agent

    result = await run_outreach_coach_agent(
        input_data=request.input,
        counselor_repo=counselor_repo,
        metrics_repo=metrics_repo,
        timeline_repo=timeline_repo,
    )

    return AgentResponse(
        agent_type="outreach_coach",
        output=result["output"],
        recommendations=result.get("recommendations", []),
    )


@router.post("/demo-prep", response_model=AgentResponse)
async def run_demo_prep(
    request: AgentRequest,
    counselor_repo=Depends(get_counselor_repository),
):
    """Run demo preparation agent.

    Prepares customized demo script and talking points for a specific counselor.
    """
    from agents.demo_prep import run_demo_prep_agent

    result = await run_demo_prep_agent(
        input_data=request.input,
        counselor_repo=counselor_repo,
    )

    return AgentResponse(
        agent_type="demo_prep",
        output=result["output"],
        recommendations=result.get("recommendations", []),
    )


@router.post("/metrics-insights", response_model=AgentResponse)
async def run_metrics_insights(
    request: AgentRequest,
    metrics_repo=Depends(get_metrics_repository),
    counselor_repo=Depends(get_counselor_repository),
):
    """Run metrics insights agent.

    Analyzes current metrics and provides insights and forecasts.
    """
    from agents.metrics_insights import run_metrics_insights_agent

    result = await run_metrics_insights_agent(
        input_data=request.input,
        metrics_repo=metrics_repo,
        counselor_repo=counselor_repo,
    )

    return AgentResponse(
        agent_type="metrics_insights",
        output=result["output"],
        recommendations=result.get("recommendations", []),
    )


@router.post("/phase-transition", response_model=AgentResponse)
async def run_phase_transition(
    request: AgentRequest,
    metrics_repo=Depends(get_metrics_repository),
    timeline_repo=Depends(get_timeline_repository),
):
    """Run phase transition agent.

    Evaluates readiness to transition from Phase 1 to Phase 2.
    """
    from agents.phase_transition import run_phase_transition_agent

    result = await run_phase_transition_agent(
        input_data=request.input,
        metrics_repo=metrics_repo,
        timeline_repo=timeline_repo,
    )

    return AgentResponse(
        agent_type="phase_transition",
        output=result["output"],
        recommendations=result.get("recommendations", []),
    )


@router.get("/health")
async def agents_health():
    """Check if agent services are available."""
    return {
        "status": "healthy",
        "available_agents": [
            "outreach_coach",
            "demo_prep",
            "metrics_insights",
            "phase_transition",
        ],
    }
