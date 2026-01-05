"""MCP server for timeline and phase tracking."""
import asyncio
import json
import logging
from datetime import date, timedelta
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

from config import setup_logging
from dependencies import get_timeline_repository
from models.timeline import MilestoneStatus

logger = logging.getLogger(__name__)

server = Server("timeline-server")


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available timeline resources."""
    return [
        Resource(
            uri="timeline://current-phase",
            name="Current Phase",
            description="Current phase and week information",
            mimeType="application/json",
        ),
        Resource(
            uri="timeline://milestones",
            name="Milestones",
            description="All milestones and deadlines",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read timeline resource by URI."""
    try:
        repo = get_timeline_repository()

        if uri == "timeline://current-phase":
            current_phase = await repo.get_current_phase()
            if not current_phase:
                return json.dumps({"error": "Current phase not initialized"})
            return current_phase.model_dump_json(indent=2)

        elif uri == "timeline://milestones":
            milestones = await repo.get_milestones()
            return json.dumps(
                [m.model_dump() for m in milestones], indent=2, default=str
            )

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
            name="get_current_phase",
            description="Get current phase, week number, and timeline status",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="check_if_on_track",
            description="Check if currently on schedule for phase timeline",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_upcoming_deadlines",
            description="Get upcoming milestones/deadlines within N days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead",
                        "default": 7,
                    }
                },
            },
        ),
        Tool(
            name="calculate_days_remaining",
            description="Calculate days remaining in current phase",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_phase_history",
            description="Get history of phase transitions",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        repo = get_timeline_repository()

        if name == "get_current_phase":
            current_phase = await repo.get_current_phase()
            if not current_phase:
                return [TextContent(type="text", text="Current phase not initialized")]

            result = {
                "phase": current_phase.phase.value,
                "week_number": current_phase.week_number,
                "phase_start_date": current_phase.phase_start_date.isoformat(),
                "current_date": current_phase.current_date.isoformat(),
                "days_in_phase": current_phase.days_in_phase,
                "on_schedule": current_phase.on_schedule,
                "weeks_remaining": current_phase.weeks_remaining_in_phase,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "check_if_on_track":
            current_phase = await repo.get_current_phase()
            if not current_phase:
                return [TextContent(type="text", text="Current phase not initialized")]

            # Phase 1 is 8 weeks (2 months)
            expected_weeks = 8
            expected_end = current_phase.phase_start_date + timedelta(weeks=expected_weeks)
            today = date.today()

            on_track = today <= expected_end

            result = {
                "on_track": on_track,
                "current_week": current_phase.week_number,
                "expected_end_date": expected_end.isoformat(),
                "days_until_expected_end": (expected_end - today).days,
                "status": (
                    "On schedule"
                    if on_track
                    else f"Behind schedule by {(today - expected_end).days} days"
                ),
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_upcoming_deadlines":
            days_ahead = arguments.get("days", 7)
            milestones = await repo.get_milestones()

            today = date.today()
            cutoff = today + timedelta(days=days_ahead)

            upcoming = [
                {
                    "id": m.id,
                    "name": m.name,
                    "phase": m.phase.value,
                    "target_date": m.target_date.isoformat(),
                    "days_away": (m.target_date - today).days,
                    "status": m.status.value,
                }
                for m in milestones
                if today <= m.target_date <= cutoff and m.status != MilestoneStatus.COMPLETED
            ]

            # Sort by date
            upcoming.sort(key=lambda x: x["target_date"])

            result = {
                "looking_ahead_days": days_ahead,
                "upcoming_count": len(upcoming),
                "deadlines": upcoming,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "calculate_days_remaining":
            current_phase = await repo.get_current_phase()
            if not current_phase:
                return [TextContent(type="text", text="Current phase not initialized")]

            # Phase 1 = 8 weeks
            expected_weeks = 8
            expected_end = current_phase.phase_start_date + timedelta(weeks=expected_weeks)
            today = date.today()
            days_remaining = (expected_end - today).days

            result = {
                "phase": current_phase.phase.value,
                "expected_duration_weeks": expected_weeks,
                "current_week": current_phase.week_number,
                "days_elapsed": current_phase.days_in_phase,
                "days_remaining": days_remaining,
                "expected_end_date": expected_end.isoformat(),
                "completion_percentage": round(
                    (current_phase.days_in_phase / (expected_weeks * 7)) * 100, 1
                ),
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_phase_history":
            timeline = await repo.get_timeline()
            if not timeline:
                return [TextContent(type="text", text="Timeline not initialized")]

            history = [
                {
                    "from_phase": t.from_phase.value if t.from_phase else None,
                    "to_phase": t.to_phase.value,
                    "transition_date": t.transition_date.isoformat(),
                    "decision": t.decision,
                    "readiness_score": t.readiness_score,
                    "notes": t.notes,
                }
                for t in timeline.phase_history
            ]

            return [TextContent(type="text", text=json.dumps(history, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    setup_logging()
    logger.info("Starting Timeline MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="timeline-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
