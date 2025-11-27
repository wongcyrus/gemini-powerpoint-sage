"""Tool Callbacks for ADK Agent MCP Integration.

This module implements the callback pattern that transforms tool inputs/outputs:
1. before_tool_callback: Converts artifact_id → base64 data for MCP tools
2. after_tool_callback: Saves base64 response → artifact, returns artifact_id

This pattern enables efficient handling of large binary data (images, videos)
without loading them entirely into the LLM context.
"""

import base64
import logging
from typing import Any

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool.mcp_tool import McpTool
from google.adk.tools.tool_context import ToolContext
from google.genai.types import Part
from mcp.types import CallToolResult

logger = logging.getLogger(__name__)


async def before_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> None:
    """Transform tool arguments before execution.
    
    Converts artifact_id references to base64-encoded data for MCP tools.
    This allows agents to pass lightweight artifact references instead of
    raw binary data, which are expanded here before sending to the MCP server.
    
    Example:
        Agent calls tool with: {"image_data": "slide_1.png"}
        We convert to: {"image_data": "base64encoded..."}
        MCP server receives base64 data and processes it
    
    Args:
        tool: The tool being called
        args: Tool arguments to transform
        tool_context: Context for loading artifacts
        
    Returns:
        None (modifies args dict in-place)
    """
    
    # Check if this is an MCP tool for video generation
    if not isinstance(tool, McpTool):
        return
    
    if tool.name != "generate_video_with_image":
        return
    
    # Log the transformation
    artifact_filename = args.get("image_data")
    logger.info("Converting artifact_id to base64: %s", artifact_filename)
    
    try:
        # Load artifact from tool context
        artifact = await tool_context.load_artifact(
            filename=artifact_filename
        )
        
        # Extract binary data from artifact
        file_data = artifact.inline_data.data
        logger.info("Loaded artifact: %d bytes", len(file_data))
        
        # Convert bytes to base64 string
        base64_data = base64.b64encode(file_data).decode("utf-8")
        logger.info("Encoded to base64: %d characters", len(base64_data))
        
        # Replace artifact_id with base64 data in tool args
        args["image_data"] = base64_data
        
    except FileNotFoundError:
        logger.error("Artifact not found: %s", artifact_filename)
        raise
    except Exception as e:
        logger.error(
            "Error converting artifact to base64: %s",
            str(e),
            exc_info=True,
        )
        raise


async def after_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict | CallToolResult,
) -> dict:
    """Transform tool responses after execution.
    
    Saves large video data as artifacts and returns artifact references
    instead of embedding base64 strings in the context. This dramatically
    reduces token usage (99%+ savings for video data).
    
    Example:
        MCP tool returns: {"video_data": "base64encoded..."}
        We save artifact: video_abc123.mp4 (5MB file)
        We return: {"artifact_id": "video_abc123.mp4", ...other fields}
    
    Args:
        tool: The tool that was called
        args: Original tool arguments
        tool_context: Context for saving artifacts
        tool_response: Response from MCP tool
        
    Returns:
        Modified response with artifact_id instead of base64 data
    """
    
    # Check if this is an MCP tool for video generation
    if not isinstance(tool, McpTool):
        return tool_response
    
    if tool.name != "generate_video_with_image":
        return tool_response
    
    # Parse tool response
    if isinstance(tool_response, CallToolResult):
        # Extract text content from CallToolResult
        import json
        tool_result = json.loads(tool_response.content[0].text)
    else:
        tool_result = tool_response
    
    # Check if this is a successful response with video data
    if tool_result.get("status") != "success":
        logger.warning("Tool returned error status: %s", tool_result)
        return tool_result
    
    if "video_data" not in tool_result:
        logger.warning("No video_data in tool response")
        return tool_result
    
    try:
        # Extract video data
        video_data = tool_result["video_data"]
        logger.info("Extracting video data: %d characters", len(video_data))
        
        # Decode base64 to bytes
        video_bytes = base64.b64decode(video_data)
        logger.info("Decoded video: %d bytes", len(video_bytes))
        
        # Create artifact filename
        artifact_filename = f"video_{tool_context.function_call_id}.mp4"
        logger.info("Saving artifact: %s", artifact_filename)
        
        # Save as artifact in tool context
        await tool_context.save_artifact(
            filename=artifact_filename,
            artifact=Part(
                inline_data={
                    "mime_type": "video/mp4",
                    "data": video_bytes,
                }
            ),
        )
        
        logger.info("Artifact saved successfully: %s", artifact_filename)
        
        # Remove video_data from response (large base64 string)
        tool_result.pop("video_data")
        
        # Add artifact reference
        tool_result["artifact_id"] = artifact_filename
        tool_result["token_savings"] = f"~{len(video_data) // 4} tokens"
        
        logger.info("Tool response modified: artifact_id=%s", artifact_filename)
        
        return tool_result
        
    except Exception as e:
        logger.error(
            "Error saving video artifact: %s",
            str(e),
            exc_info=True,
        )
        # Return original response on error
        return tool_result
