"""MCP server for accessing strategy documents and scripts."""
import asyncio
import json
import logging
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent

from config import setup_logging
from dependencies import get_storage_client

logger = logging.getLogger(__name__)

server = Server("documents-server")


# Document metadata (would be loaded from blob storage in real implementation)
DOCUMENTS = {
    "product-intro": {
        "name": "TargetAI Product Introduction",
        "description": "Complete product feature documentation",
        "path": "documents/product-intro.json",
    },
    "gtm-roadmap": {
        "name": "Go-To-Market Roadmap",
        "description": "4-phase GTM strategy and timeline",
        "path": "documents/gtm-roadmap.json",
    },
    "phase1-action-plan": {
        "name": "Phase 1 Action Plan",
        "description": "Detailed 8-week execution plan for Phase 1",
        "path": "documents/phase1-action-plan.json",
    },
}

SCRIPTS = {
    "discovery-call": {
        "name": "Discovery Call Script",
        "description": "20-30 minute discovery call script with questions",
        "content": """
DISCOVERY CALL SCRIPT (20-30 minutes)

OPENING (2 min):
"Thanks for taking the time, [Name]. Before I tell you about what we're building,
I'd love to understand your practice better. This helps me know if we'd actually
be useful to you—I'd rather be honest upfront than waste your time."

DISCOVERY QUESTIONS (10-15 min):
1. "Walk me through a typical week during peak season. Where do you spend most of your time?"
2. "What tools do you currently use to manage students and track applications?"
3. "How do you currently handle meeting notes and follow-ups?"
4. "What's your biggest pain point—the thing that makes you think 'there has to be a better way'?"
5. "How do you feel about AI in counseling? What excites you or concerns you?"

BRIEF PITCH (5 min):
"Based on what you've shared, here's where I think TargetAI could help: [customize to their pain points].
We're specifically built for counselors—not students, not parents. The AI assists you; it doesn't
replace your judgment. And we have a hard rule: no AI essay writing, no acceptance guarantees."

CLOSE & NEXT STEPS (3 min):
"I'd love to show you the platform in action. I can do a 45-minute demo where you'll see exactly
how this works with your workflow. Would [date/time] work for you?"
""",
    },
    "demo-session": {
        "name": "Demo Session Script",
        "description": "45-60 minute platform demo flow",
        "content": """
DEMO SESSION SCRIPT (45-60 minutes)

0-5 min: RECONNECT & AGENDA
- Recap pain points from discovery call
- Set expectations for demo

5-15 min: STUDENT MANAGEMENT DEMO
- Show dashboard, add student flow, profile completion tracking

15-25 min: AI FEATURES SHOWCASE
- AI chat assistant, meeting reports, college gap analysis

25-35 min: ESSAY & COLLEGE TOOLS
- Essay positioning map, college list builder, compare students

35-45 min: Q&A + PILOT DISCUSSION
- Answer questions, discuss pilot terms, secure commitment

45-60 min: (OPTIONAL) LIVE SETUP
- If ready to commit, begin hands-on setup immediately
""",
    },
    "linkedin-dm": {
        "name": "LinkedIn DM Template",
        "description": "Personalized LinkedIn outreach message",
        "content": """
LINKEDIN DM TEMPLATE

Hi [Name],

I've been following your work on [specific post/topic]. Your perspective on [specific insight]
really resonated with me.

I'm building a counselor-first AI platform at StemPro Academy—designed to amplify your expertise,
not replace it. No AI essay writing. No acceptance guarantees. Just intelligent tools that save
you time on admin so you can focus on what matters.

Would you be open to a 20-minute call? I'd love your perspective—even if it's just to tell me
what we're getting wrong.

— [Your name]
""",
    },
}


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available document resources."""
    resources = []

    # Strategy documents
    for doc_id, doc_meta in DOCUMENTS.items():
        resources.append(
            Resource(
                uri=f"docs://{doc_id}",
                name=doc_meta["name"],
                description=doc_meta["description"],
                mimeType="application/json",
            )
        )

    # Scripts
    for script_id, script_meta in SCRIPTS.items():
        resources.append(
            Resource(
                uri=f"docs://scripts/{script_id}",
                name=script_meta["name"],
                description=script_meta["description"],
                mimeType="text/plain",
            )
        )

    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read document resource by URI."""
    try:
        storage = get_storage_client()

        if uri.startswith("docs://scripts/"):
            # Return script content
            script_id = uri.replace("docs://scripts/", "")
            if script_id in SCRIPTS:
                return SCRIPTS[script_id]["content"]
            else:
                raise ValueError(f"Unknown script: {script_id}")

        elif uri.startswith("docs://"):
            # Return document from storage
            doc_id = uri.replace("docs://", "")
            if doc_id in DOCUMENTS:
                doc_data = await storage.read_raw(DOCUMENTS[doc_id]["path"])
                if doc_data:
                    return json.dumps(doc_data, indent=2)
                else:
                    # Document not yet in storage, return placeholder
                    return json.dumps(
                        {
                            "id": doc_id,
                            "name": DOCUMENTS[doc_id]["name"],
                            "note": "Document content to be uploaded from PDF",
                        },
                        indent=2,
                    )
            else:
                raise ValueError(f"Unknown document: {doc_id}")

        else:
            raise ValueError(f"Invalid URI format: {uri}")

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_documentation",
            description="Search strategy documents for specific information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_script",
            description="Get a call script by type",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_type": {
                        "type": "string",
                        "description": "Script type",
                        "enum": ["discovery-call", "demo-session", "linkedin-dm"],
                    }
                },
                "required": ["script_type"],
            },
        ),
        Tool(
            name="get_selection_criteria",
            description="Get counselor selection criteria and scoring rubric",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_phase_details",
            description="Get details about a specific phase from the GTM roadmap",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "description": "Phase number",
                        "enum": ["phase1", "phase2", "phase3", "phase4"],
                    }
                },
                "required": ["phase"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_documentation":
            query = arguments["query"].lower()

            # Simple keyword search across documents (in real implementation, use vector search)
            results = []

            for doc_id, doc_meta in DOCUMENTS.items():
                if query in doc_meta["name"].lower() or query in doc_meta["description"].lower():
                    results.append(
                        {
                            "document": doc_meta["name"],
                            "uri": f"docs://{doc_id}",
                            "relevance": "high",
                        }
                    )

            if not results:
                results.append({"message": f"No documents found matching '{query}'"})

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "get_script":
            script_type = arguments["script_type"]

            if script_type in SCRIPTS:
                return [TextContent(type="text", text=SCRIPTS[script_type]["content"])]
            else:
                return [TextContent(type="text", text=f"Unknown script type: {script_type}")]

        elif name == "get_selection_criteria":
            criteria = {
                "must_have_criteria": {
                    "active_caseload": "10+ students annually",
                    "tech_comfort": "Uses digital tools (CRM, Zoom, Google Workspace)",
                    "firm_type": "Independent or small firm (<5 counselors)",
                    "ethical_alignment": "Values integrity in admissions process",
                    "feedback_willingness": "Agrees to bi-weekly check-ins, NPS survey",
                },
                "scoring_rubric": {
                    "active_caseload": {"1pt": "10-20", "2pt": "20-40", "3pt": "40+"},
                    "tech_stack": {"1pt": "Basic", "2pt": "Moderate", "3pt": "Advanced"},
                    "feedback_commitment": {"1pt": "Monthly", "2pt": "Bi-weekly", "3pt": "Weekly"},
                    "industry_influence": {"1pt": "Low", "2pt": "Medium", "3pt": "High"},
                    "ethical_alignment": {"1pt": "Unclear", "2pt": "Aligned", "3pt": "Champion"},
                },
                "total_score": "0-15 points (minimum 8 to proceed, prioritize 12+)",
                "red_flags": [
                    "Makes outcome guarantees",
                    "Negative industry reputation",
                    "Direct competitor",
                    "Won't commit to feedback schedule",
                    "Hostile toward AI",
                ],
            }

            return [TextContent(type="text", text=json.dumps(criteria, indent=2))]

        elif name == "get_phase_details":
            phase = arguments["phase"]

            # Phase details from GTM roadmap
            phases = {
                "phase1": {
                    "name": "Counselor Credibility Pilot",
                    "duration": "Months 0-2",
                    "objective": "Build trust, validate product-market fit, refine messaging",
                    "target_audience": "Independent counselors, small counseling firms",
                    "success_metrics": {
                        "pilots_onboarded": "10-15",
                        "nps": "≥ 8",
                        "weekly_active_rate": "≥ 70%",
                        "referrals": "10+",
                    },
                    "timing_note": "Target summer months (May-August) when counselors have bandwidth",
                },
                "phase2": {
                    "name": "Firm Distribution",
                    "duration": "Months 2-4",
                    "objective": "Scale usage through established counseling firms",
                    "target_audience": "Counseling firms with existing student rosters",
                    "success_metrics": {
                        "active_students_per_firm": "50+",
                        "renewal_intent": "≥ 80%",
                    },
                },
                "phase3": {
                    "name": "Student Activation",
                    "duration": "Months 4-6",
                    "objective": "Drive direct student engagement within firm ecosystem",
                    "target_audience": "Students enrolled through counseling firms",
                    "success_metrics": {
                        "weekly_active_rate": "≥ 60%",
                        "time_to_first_value": "< 10 minutes",
                    },
                },
                "phase4": {
                    "name": "Direct Student & Parent Growth",
                    "duration": "Month 6+",
                    "objective": "Platform expansion to consumer market",
                    "target_audience": "Parents and students outside existing firm relationships",
                    "success_metrics": {
                        "paid_conversion_rate": "≥ 5%",
                        "12_month_retention": "≥ 70%",
                    },
                },
            }

            if phase in phases:
                return [TextContent(type="text", text=json.dumps(phases[phase], indent=2))]
            else:
                return [TextContent(type="text", text=f"Unknown phase: {phase}")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    setup_logging()
    logger.info("Starting Documents MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="documents-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
