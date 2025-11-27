"""MCP Toolset configuration for Veo 3.1 video generation."""

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)
from mcp import StdioServerParameters
import os
import logging

logger = logging.getLogger(__name__)

# Get the veo_mcp directory relative to this file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
veo_mcp_path = os.path.join(project_root, "veo_mcp", "main.py")

# Initialize MCP Toolset for Veo video generation
mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=[
                "run",
                veo_mcp_path,
            ],
        ),
        timeout=300,  # 5 minutes for video generation
    ),
)

logger.info(
    "Veo MCP Toolset initialized. Server path: %s",
    veo_mcp_path
)

# Optional: Remote MCP server configuration example
# from google.adk.tools.mcp_tool.mcp_session_manager import (
#     StreamableHTTPConnectionParams,
# )
# mcp_toolset = MCPToolset(
#     connection_params=StreamableHTTPConnectionParams(
#         url="http://localhost:8000/mcp",
#         timeout=300,
#     ),
# )
