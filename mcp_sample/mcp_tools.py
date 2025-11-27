"""MCP Toolset Configuration for ADK Agent Integration.

This module sets up the connection between an ADK agent and the Veo MCP server.
Supports both STDIO (development) and HTTP (production) connection types.
"""

from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters


def create_stdio_mcp_toolset() -> MCPToolset:
    """Create MCP toolset with STDIO connection (development mode).
    
    This is the recommended setup for development and testing. The MCP server
    runs as a child process and communicates via stdio.
    
    Returns:
        MCPToolset configured for STDIO connection to veo_server.py
    """
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=[
                    "-m",
                    "mcp_sample.veo_server",
                ],
            ),
            timeout=180,  # 3 minutes for video generation
        ),
    )


def create_http_mcp_toolset(url: str = "http://localhost:8000/mcp") -> MCPToolset:
    """Create MCP toolset with HTTP connection (production mode).
    
    For production deployments, run the MCP server as a separate service
    and connect via HTTP. This allows the server to be hosted remotely.
    
    Args:
        url: HTTP URL of the running MCP server
        
    Returns:
        MCPToolset configured for HTTP connection
    """
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        StreamableHTTPConnectionParams,
    )

    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=url,
            timeout=180,  # 3 minutes for video generation
        ),
    )


# Default toolset (STDIO for development)
mcp_toolset = create_stdio_mcp_toolset()
