"""MCP server for counselor data access."""
import asyncio
import json
import logging
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ResourceTemplate,
    Tool,
    TextContent,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

from config import setup_logging, get_settings
from dependencies import get_counselor_repository
from models.counselor import PipelineStage, Specialization

logger = logging.getLogger(__name__)

# Initialize server
server = Server("counselor-data-server")


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available counselor resources.

    Returns:
        List of available resources
    """
    repo = get_counselor_repository()
    counselors = await repo.get_all()

    resources = []
    for counselor in counselors:
        resources.append(
            Resource(
                uri=f"counselor://{counselor.id}/profile",
                name=f"Counselor Profile: {counselor.profile.first_name} {counselor.profile.last_name}",
                description=f"Profile data for {counselor.profile.email}",
                mimeType="application/json",
            )
        )

    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read counselor resource by URI.

    Args:
        uri: Resource URI (e.g., counselor://counsel-001/profile)

    Returns:
        JSON string of counselor data
    """
    try:
        # Parse URI: counselor://{id}/profile
        parts = uri.replace("counselor://", "").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid URI format: {uri}")

        counselor_id = parts[0]
        resource_type = parts[1]

        repo = get_counselor_repository()
        counselor = await repo.get_by_id(counselor_id)

        if not counselor:
            raise ValueError(f"Counselor not found: {counselor_id}")

        # Return appropriate resource
        if resource_type == "profile":
            return counselor.model_dump_json(indent=2)
        elif resource_type == "scoring":
            return json.dumps(counselor.scoring.model_dump(), indent=2)
        elif resource_type == "pipeline":
            return json.dumps(counselor.pipeline.model_dump(), indent=2)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools.

    Returns:
        List of tools
    """
    return [
        Tool(
            name="search_counselors",
            description="Search counselors by criteria (score, stage, specialization, region)",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum total score (0-15)",
                        "minimum": 0,
                        "maximum": 15,
                    },
                    "stage": {
                        "type": "string",
                        "description": "Pipeline stage filter",
                        "enum": [s.value for s in PipelineStage],
                    },
                    "specialization": {
                        "type": "array",
                        "items": {"type": "string", "enum": [s.value for s in Specialization]},
                        "description": "Specializations to match",
                    },
                    "region": {
                        "type": "string",
                        "description": "Geographic region",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="get_counselor",
            description="Get complete counselor profile by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "counselor_id": {
                        "type": "string",
                        "description": "Counselor ID",
                    }
                },
                "required": ["counselor_id"],
            },
        ),
        Tool(
            name="score_counselor",
            description="Calculate or retrieve counselor score breakdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "counselor_id": {
                        "type": "string",
                        "description": "Counselor ID",
                    }
                },
                "required": ["counselor_id"],
            },
        ),
        Tool(
            name="get_pipeline_stats",
            description="Get counselor distribution across pipeline stages",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_high_priority",
            description="Get high-priority counselors (score >= 12)",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum score (default: 12)",
                        "default": 12,
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool result as text content
    """
    try:
        repo = get_counselor_repository()

        if name == "search_counselors":
            # Extract arguments
            min_score = arguments.get("min_score")
            stage = PipelineStage(arguments["stage"]) if "stage" in arguments else None
            spec_list = arguments.get("specialization", [])
            specialization = [Specialization(s) for s in spec_list] if spec_list else None
            region = arguments.get("region")
            limit = arguments.get("limit", 50)

            # Search
            results = await repo.search(
                min_score=min_score,
                stage=stage,
                specialization=specialization,
                region=region,
            )

            # Limit results
            results = results[:limit]

            # Format response
            counselor_summaries = [
                {
                    "id": c.id,
                    "name": f"{c.profile.first_name} {c.profile.last_name}",
                    "email": c.profile.email,
                    "score": c.scoring.total_score,
                    "stage": c.pipeline.stage.value,
                    "specialization": [s.value for s in c.metadata.specialization],
                    "region": c.metadata.region.value,
                }
                for c in results
            ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "total_found": len(counselor_summaries),
                            "counselors": counselor_summaries,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "get_counselor":
            counselor_id = arguments["counselor_id"]
            counselor = await repo.get_by_id(counselor_id)

            if not counselor:
                return [TextContent(type="text", text=f"Counselor not found: {counselor_id}")]

            return [TextContent(type="text", text=counselor.model_dump_json(indent=2))]

        elif name == "score_counselor":
            counselor_id = arguments["counselor_id"]
            counselor = await repo.get_by_id(counselor_id)

            if not counselor:
                return [TextContent(type="text", text=f"Counselor not found: {counselor_id}")]

            score_breakdown = {
                "counselor_id": counselor.id,
                "name": f"{counselor.profile.first_name} {counselor.profile.last_name}",
                "total_score": counselor.scoring.total_score,
                "max_score": counselor.scoring.max_score,
                "breakdown": {
                    "active_caseload": counselor.scoring.active_caseload,
                    "tech_stack": counselor.scoring.tech_stack,
                    "feedback_commitment": counselor.scoring.feedback_commitment,
                    "industry_influence": counselor.scoring.industry_influence,
                    "ethical_alignment": counselor.scoring.ethical_alignment,
                },
                "notes": counselor.scoring.notes,
            }

            return [TextContent(type="text", text=json.dumps(score_breakdown, indent=2))]

        elif name == "get_pipeline_stats":
            stats = {}
            for stage in PipelineStage:
                count = await repo.count_by_stage(stage)
                stats[stage.value] = count

            total = await repo.count()

            return [
                TextContent(
                    type="text",
                    text=json.dumps({"total_counselors": total, "by_stage": stats}, indent=2),
                )
            ]

        elif name == "get_high_priority":
            min_score = arguments.get("min_score", 12)
            high_priority = await repo.get_high_priority(min_score=min_score)

            summaries = [
                {
                    "id": c.id,
                    "name": f"{c.profile.first_name} {c.profile.last_name}",
                    "score": c.scoring.total_score,
                    "stage": c.pipeline.stage.value,
                    "email": c.profile.email,
                }
                for c in high_priority
            ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"count": len(summaries), "counselors": summaries}, indent=2
                    ),
                )
            ]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    setup_logging()
    logger.info("Starting Counselor Data MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="counselor-data-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
