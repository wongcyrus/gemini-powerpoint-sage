"""Tool callbacks for Veo MCP video generation.

Handles conversion of slide artifacts to base64 data and vice versa,
enabling efficient multimodal tool interactions.
"""

import base64
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def before_video_tool_callback(
    tool_name: str,
    args: dict[str, Any],
    artifact_loader: Any = None,
) -> dict[str, Any]:
    """Transform tool arguments before MCP tool execution.

    Converts artifact references to base64-encoded image data that the
    Veo API expects.

    Args:
        tool_name: Name of the tool being called
        args: Tool arguments potentially containing artifact references
        artifact_loader: Optional artifact loading service

    Returns:
        Modified arguments with base64-encoded data
    """
    if tool_name == "generate_video_with_image" and artifact_loader:
        if "image_data" in args:
            artifact_id = args["image_data"]
            logger.info(
                "Loading artifact for video generation: %s",
                artifact_id
            )

            try:
                # Load artifact from storage
                artifact = await artifact_loader.load_artifact(
                    filename=artifact_id
                )

                # Extract binary data
                file_data = artifact.inline_data.data

                # Convert to base64
                base64_data = base64.b64encode(file_data).decode(
                    "utf-8"
                )

                # Replace artifact ID with base64 data
                args["image_data"] = base64_data

                logger.info(
                    "Successfully converted artifact to base64: %d bytes",
                    len(base64_data)
                )

            except Exception as e:
                logger.error(
                    "Failed to load artifact %s: %s",
                    artifact_id,
                    str(e)
                )
                raise

    return args


async def after_video_tool_callback(
    tool_name: str,
    tool_response: dict | Any,
    artifact_saver: Any = None,
    function_call_id: str = "",
) -> dict[str, Any]:
    """Transform tool responses after MCP tool execution.

    Saves large video data as artifacts and returns artifact references
    instead of base64 strings to avoid token overflow.

    Args:
        tool_name: Name of the tool that was called
        tool_response: Raw response from the MCP tool
        artifact_saver: Optional artifact saving service
        function_call_id: Unique ID for this function call

    Returns:
        Modified response with artifact reference instead of base64 data
    """
    if tool_name == "generate_video_with_image" and artifact_saver:
        try:
            # Parse tool response
            if isinstance(tool_response, dict):
                tool_result = tool_response
            elif isinstance(tool_response, str):
                tool_result = json.loads(tool_response)
            else:
                # Handle CallToolResult or similar objects
                response_text = getattr(
                    tool_response,
                    "text",
                    str(tool_response)
                )
                tool_result = json.loads(response_text)

            # Check if video data exists
            if "video_data" not in tool_result:
                logger.warning(
                    "No video_data in tool response"
                )
                return tool_result

            video_data = tool_result.get("video_data")
            artifact_filename = f"video_{function_call_id}.mp4"

            logger.info(
                "Saving video to artifact: %s",
                artifact_filename
            )

            try:
                # Convert base64 to bytes
                video_bytes = base64.b64decode(video_data)

                logger.info(
                    "Video data size: %d bytes",
                    len(video_bytes)
                )

                # Save to artifact storage
                await artifact_saver.save_artifact(
                    filename=artifact_filename,
                    data=video_bytes,
                    mime_type="video/mp4"
                )

                # Remove base64 data from response
                tool_result.pop("video_data", None)

                # Add artifact reference
                tool_result["video_artifact_id"] = artifact_filename

                logger.info(
                    "Video artifact saved successfully: %s",
                    artifact_filename
                )

            except Exception as e:
                logger.error(
                    "Failed to save video artifact: %s",
                    str(e)
                )
                # Return response as-is if artifact saving fails
                return tool_result

        except Exception as e:
            logger.error(
                "Error processing video tool response: %s",
                str(e)
            )
            return tool_response

    return tool_response
