"""MCP server for metrics data access."""
import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

from config import setup_logging
from dependencies import get_metrics_repository, get_counselor_repository
from models.metrics import Phase

logger = logging.getLogger(__name__)

server = Server("metrics-server")


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available metrics resources."""
    return [
        Resource(
            uri="metrics://current",
            name="Current Metrics",
            description="Real-time current metrics snapshot",
            mimeType="application/json",
        ),
        Resource(
            uri="metrics://phase1/summary",
            name="Phase 1 Summary",
            description="Complete Phase 1 metrics summary",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read metrics resource by URI."""
    try:
        repo = get_metrics_repository()

        if uri == "metrics://current":
            current = await repo.get_current()
            if not current:
                return json.dumps({"error": "Current metrics not initialized"})
            return current.model_dump_json(indent=2)

        elif uri == "metrics://phase1/summary":
            summary = await repo.get_phase1_summary()
            return json.dumps(summary, indent=2, default=str)

        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_current_metrics",
            description="Get real-time current metrics",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_weekly_metrics",
            description="Get weekly metrics for a specific week",
            inputSchema={
                "type": "object",
                "properties": {
                    "week_number": {
                        "type": "integer",
                        "description": "Week number (1-8 for Phase 1)",
                        "minimum": 1,
                    }
                },
                "required": ["week_number"],
            },
        ),
        Tool(
            name="check_phase_readiness",
            description="Check if ready to transition from Phase 1 to Phase 2",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="forecast_metric",
            description="Forecast if a metric will hit target by end of phase",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "Metric to forecast",
                        "enum": ["nps", "pilots_onboarded", "weekly_active_rate", "referrals"],
                    },
                    "weeks_ahead": {
                        "type": "integer",
                        "description": "How many weeks to forecast",
                        "default": 1,
                    },
                },
                "required": ["metric_name"],
            },
        ),
        Tool(
            name="calculate_conversion_rates",
            description="Calculate conversion rates across the funnel",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        metrics_repo = get_metrics_repository()

        if name == "get_current_metrics":
            current = await metrics_repo.get_current()
            if not current:
                return [TextContent(type="text", text="Current metrics not initialized")]

            return [TextContent(type="text", text=current.model_dump_json(indent=2))]

        elif name == "get_weekly_metrics":
            week_number = arguments["week_number"]
            weekly = await metrics_repo.get_weekly(week_number)

            if not weekly:
                return [TextContent(type="text", text=f"No data for week {week_number}")]

            return [TextContent(type="text", text=weekly.model_dump_json(indent=2))]

        elif name == "check_phase_readiness":
            current = await metrics_repo.get_current()
            if not current:
                return [TextContent(type="text", text="Metrics not initialized")]

            targets = current.phase1_targets

            # Check each criterion
            readiness = {
                "pilots_onboarded": {
                    "current": current.total_pilots_onboarded,
                    "target": f"{targets.pilots_onboarded_min}-{targets.pilots_onboarded_max}",
                    "met": (
                        targets.pilots_onboarded_min
                        <= current.total_pilots_onboarded
                        <= targets.pilots_onboarded_max
                    ),
                },
                "nps": {
                    "current": current.current_nps,
                    "target": f">= {targets.nps_target}",
                    "met": (
                        current.current_nps >= targets.nps_target if current.current_nps else False
                    ),
                },
                "weekly_active_rate": {
                    "current": current.current_weekly_active_rate,
                    "target": f">= {targets.weekly_active_rate_target}%",
                    "met": (
                        current.current_weekly_active_rate >= targets.weekly_active_rate_target
                        if current.current_weekly_active_rate
                        else False
                    ),
                },
                "referrals": {
                    "current": current.total_referrals,
                    "target": f">= {targets.referrals_target}",
                    "met": current.total_referrals >= targets.referrals_target,
                },
                "feedback_items": {
                    "current": current.total_feedback_items,
                    "target": f">= {targets.feedback_items_target}",
                    "met": current.total_feedback_items >= targets.feedback_items_target,
                },
                "positioning_phrases": {
                    "current": current.positioning_phrases_validated,
                    "target": f">= {targets.positioning_phrases_target}",
                    "met": (
                        current.positioning_phrases_validated >= targets.positioning_phrases_target
                    ),
                },
            }

            # Calculate readiness score
            criteria_met = sum(1 for c in readiness.values() if c["met"])
            total_criteria = len(readiness)
            readiness_score = (criteria_met / total_criteria) * 100

            # Recommendation
            if criteria_met == total_criteria:
                decision = "GO - All criteria met"
            elif criteria_met >= total_criteria * 0.8:
                decision = "CONDITIONAL GO - Most criteria met, review gaps"
            else:
                decision = "NO GO - Significant gaps remain"

            result = {
                "readiness_score": round(readiness_score, 1),
                "criteria_met": criteria_met,
                "total_criteria": total_criteria,
                "decision": decision,
                "details": readiness,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "forecast_metric":
            metric_name = arguments["metric_name"]
            weeks_ahead = arguments.get("weeks_ahead", 1)

            current = await metrics_repo.get_current()
            if not current:
                return [TextContent(type="text", text="Metrics not initialized")]

            # Get recent weekly data for trend
            all_weekly = await metrics_repo.get_all_weekly(Phase.PHASE_1)
            if len(all_weekly) < 2:
                return [
                    TextContent(
                        type="text",
                        text="Not enough historical data to forecast (need at least 2 weeks)",
                    )
                ]

            # Simple linear forecast based on recent trend
            recent_weeks = all_weekly[-3:]  # Last 3 weeks

            if metric_name == "nps":
                values = [w.nps_score for w in recent_weeks if w.nps_score]
                if len(values) < 2:
                    return [TextContent(type="text", text="Insufficient NPS data for forecast")]

                # Calculate trend
                avg_change = (values[-1] - values[0]) / len(values)
                forecasted = values[-1] + (avg_change * weeks_ahead)
                target = current.phase1_targets.nps_target

                result = {
                    "metric": "nps",
                    "current": values[-1],
                    "forecasted": round(forecasted, 2),
                    "target": target,
                    "trend": "increasing" if avg_change > 0 else "decreasing",
                    "will_hit_target": forecasted >= target,
                }

            elif metric_name == "pilots_onboarded":
                # Count pilots onboarded per week
                counselor_repo = get_counselor_repository()
                pilots = await counselor_repo.count_by_stage(
                    "pilot"
                ) + await counselor_repo.count_by_stage("active")

                # Simple projection (not enough data for real forecast)
                weekly_rate = pilots / max(current.current_week, 1)
                forecasted = pilots + (weekly_rate * weeks_ahead)
                target_min = current.phase1_targets.pilots_onboarded_min

                result = {
                    "metric": "pilots_onboarded",
                    "current": pilots,
                    "forecasted": int(forecasted),
                    "target": f"{current.phase1_targets.pilots_onboarded_min}-{current.phase1_targets.pilots_onboarded_max}",
                    "weekly_rate": round(weekly_rate, 1),
                    "will_hit_target": forecasted >= target_min,
                }

            else:
                return [
                    TextContent(
                        type="text", text=f"Forecasting not yet implemented for {metric_name}"
                    )
                ]

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "calculate_conversion_rates":
            current = await metrics_repo.get_current()
            if not current:
                return [TextContent(type="text", text="Metrics not initialized")]

            # Calculate funnel conversion rates
            connections = current.total_connections
            discovery_calls = current.total_discovery_calls
            demos = current.total_demos
            pilots = current.total_pilots_onboarded

            rates = {
                "connection_to_discovery": (
                    round((discovery_calls / connections) * 100, 1) if connections > 0 else 0
                ),
                "discovery_to_demo": (
                    round((demos / discovery_calls) * 100, 1) if discovery_calls > 0 else 0
                ),
                "demo_to_pilot": round((pilots / demos) * 100, 1) if demos > 0 else 0,
                "connection_to_pilot": (
                    round((pilots / connections) * 100, 1) if connections > 0 else 0
                ),
            }

            result = {
                "funnel": {
                    "connections": connections,
                    "discovery_calls": discovery_calls,
                    "demos": demos,
                    "pilots": pilots,
                },
                "conversion_rates": rates,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    setup_logging()
    logger.info("Starting Metrics MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="metrics-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
