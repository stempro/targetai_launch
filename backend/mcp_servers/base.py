"""Base MCP server setup and utilities."""
import logging
from typing import Any, Callable

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """Base class for MCP servers."""

    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize base MCP server.

        Args:
            name: Server name
            version: Server version
        """
        self.name = name
        self.version = version
        self.server = Server(name)
        self.resources: dict[str, Resource] = {}
        self.tools: dict[str, Tool] = {}

        logger.info(f"Initialized MCP server: {name} v{version}")

    def add_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str = "application/json",
        handler: Callable[..., Any] | None = None,
    ) -> None:
        """Register a resource.

        Args:
            uri: Resource URI pattern (e.g., "counselor://{id}/profile")
            name: Resource name
            description: Resource description
            mime_type: MIME type
            handler: Optional handler function
        """
        self.resources[uri] = Resource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type,
        )
        logger.debug(f"Registered resource: {name} at {uri}")

    def add_tool(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON schema for tool inputs
            handler: Tool handler function
        """
        self.tools[name] = Tool(
            name=name,
            description=description,
            inputSchema=input_schema,
        )
        logger.debug(f"Registered tool: {name}")

    async def run(self) -> None:
        """Run the MCP server with stdio transport."""
        logger.info(f"Starting MCP server: {self.name}")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def create_text_content(text: str) -> list[TextContent]:
    """Create text content for MCP response.

    Args:
        text: Text content

    Returns:
        List with TextContent
    """
    return [TextContent(type="text", text=text)]


def create_json_content(data: Any) -> list[TextContent]:
    """Create JSON content for MCP response.

    Args:
        data: Data to serialize as JSON

    Returns:
        List with TextContent containing JSON
    """
    import json
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def create_error_content(error: str) -> list[TextContent]:
    """Create error content for MCP response.

    Args:
        error: Error message

    Returns:
        List with TextContent containing error
    """
    return [TextContent(type="text", text=f"Error: {error}")]
