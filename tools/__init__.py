"""Tool factory modules for Gemini Powerpoint Sage."""

try:
    from .veo_mcp_tools import mcp_toolset  # noqa: F401
    __all__ = ["mcp_toolset"]
except ImportError:
    # MCP tools may not be available if dependencies not installed
    __all__ = []


