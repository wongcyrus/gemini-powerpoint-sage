"""Veo 3.1 MCP Server - Production-Ready Sample Implementation.

This is a complete, production-ready FastMCP server that demonstrates:
- Proper server initialization and tool definition
- Integration with Google Vertex AI Veo API
- Error handling and logging best practices
- Input validation and type checking
- Async/await patterns
- Response formatting for ADK integration

This server can be used as a template for other MCP servers.
"""

import asyncio
import base64
import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP
from google import genai
from google.genai import types
from pydantic import Field

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Veo 3.1 MCP Server")


def _enrich_prompt_for_professional_video(base_prompt: str) -> str:
    """Enriches user prompt with professional video production guidelines.
    
    Adds cinematic quality, professional lighting, smooth camera work, and
    visual storytelling elements to ensure high-quality presentation videos.
    
    Args:
        base_prompt: User's video description
        
    Returns:
        Enhanced prompt with professional production guidelines
    """
    enrichment = """PROFESSIONAL VIDEO PRODUCTION STANDARDS:
- 4K cinematic quality with professional color grading
- Smooth, stabilized camera movements and transitions
- Professional studio lighting with soft, even illumination
- Shallow depth of field for subject focus
- High dynamic range (HDR) for vibrant colors
- Smooth transitions and natural motion flow
- Keep the subject as the clear focal point
- Professional camera techniques (slow pans, tracking shots, dolly movements)
- Subtle motion blur for cinematic feel
- Brand-appropriate tone and style
- Smooth, natural transitions between scenes

USER REQUIREMENTS:
"""
    return f"{enrichment}{base_prompt}"


@mcp.tool
async def generate_video_with_image(
    prompt: Annotated[
        str,
        Field(
            description=(
                "Text description of the video to generate. "
                "Describe what should happen: camera movements, environment, "
                "subject actions, style, and mood. For presentations, focus on "
                "visualizing the slide concept. Example: 'Show a rotating 3D chart "
                "with data points appearing smoothly, professional lighting, "
                "blue color scheme'"
            )
        ),
    ],
    image_data: Annotated[
        str,
        Field(
            description=(
                "Base64-encoded PNG image data to use as the starting frame. "
                "This image sets the visual style and starting point for the video. "
                "The ADK agent's before_tool_callback will convert artifact_id to base64 "
                "automatically - do not pass raw binary data."
            )
        ),
    ],
    duration_seconds: Annotated[
        int,
        Field(
            description="Duration of generated video in seconds (default: 8)",
            ge=1,
            le=30,
        ),
    ] = 8,
    negative_prompt: Annotated[
        str | None,
        Field(
            description="Optional: things to avoid in the generated video. "
            "Example: 'avoid text overlays, avoid rapid cuts, avoid blur'"
        ),
    ] = None,
) -> dict:
    """Generates a professional video from an image and text prompt using Veo 3.1.
    
    This function creates high-quality, cinematic videos perfect for presentations,
    marketing materials, and educational content. It uses Google's Veo 3.1 model
    via Vertex AI to generate smooth, professional-quality videos.
    
    HOW IT WORKS:
    1. Takes a starting image (PNG) as the visual foundation
    2. Enriches your text prompt with professional production guidelines
    3. Sends enriched prompt + image to Veo 3.1 API
    4. Polls operation until video generation completes
    5. Returns video data as base64 (which gets saved as artifact by after_tool_callback)
    
    PROMPT WRITING TIPS:
    - Be specific about camera movements: "slow zoom in", "rotating view", "tracking shot"
    - Describe subject actions: "objects appear one by one", "elements transition smoothly"
    - Mention visual style: "corporate blue theme", "minimalist design", "bright and energetic"
    - Include pacing: "slow and contemplative", "dynamic and fast-paced"
    - Example: "Slowly pan across a digital dashboard, with charts updating in real-time,
               professional blue lighting, smooth transitions"
    
    ARTIFACT INTEGRATION:
    - The ADK agent's before_tool_callback automatically converts artifact_id to base64
    - The after_tool_callback automatically saves video as artifact and returns artifact_id
    - This means: You pass artifact_id, we handle the base64 encoding/decoding
    
    Args:
        prompt: Text description of desired video content
        image_data: Base64-encoded PNG image (will be converted by before_tool_callback)
        duration_seconds: Video length (1-30 seconds, default 8)
        negative_prompt: Optional prompt for things to avoid
        
    Returns:
        dict: Response containing:
            - status: "success" or "error"
            - message: Human-readable status message
            - duration_seconds: Actual video duration generated
            - prompt_used: The enriched prompt sent to Veo API
            - video_data: Base64-encoded MP4 video data (will become artifact)
            - model_used: "veo-3.1-generate-preview"
            
    Example:
        >>> response = await generate_video_with_image(
        ...     prompt="Slow zoom into a digital concept map showing interconnected ideas",
        ...     image_data="base64_encoded_png...",
        ...     duration_seconds=8
        ... )
        >>> # After tool execution, after_tool_callback converts this to:
        >>> # {
        >>> #     "artifact_id": "video_abc123.mp4",
        >>> #     "status": "success",
        >>> #     ...
        >>> # }
    """
    
    try:
        logger.info(
            "Starting video generation: duration=%d seconds, prompt_length=%d",
            duration_seconds,
            len(prompt),
        )
        
        # Validate inputs
        if not prompt or not prompt.strip():
            return {
                "status": "error",
                "message": "Prompt cannot be empty",
            }
        
        if not image_data or not image_data.strip():
            return {
                "status": "error",
                "message": "Image data cannot be empty",
            }
        
        # Verify environment variables
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        
        if not project or not location:
            logger.error(
                "Missing Vertex AI credentials: project=%s, location=%s",
                project,
                location,
            )
            return {
                "status": "error",
                "message": (
                    "Missing Vertex AI configuration. "
                    "Set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment variables."
                ),
            }
        
        # Initialize Vertex AI client
        logger.info(f"Initializing Vertex AI client for project: {project}")
        client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )
        
        # Decode image data from base64
        logger.info("Decoding base64 image data...")
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return {
                "status": "error",
                "message": f"Invalid base64 image data: {str(e)}",
            }
        
        logger.info(f"Successfully decoded image: {len(image_bytes)} bytes")
        
        # Create image object
        image = types.Image(
            image_bytes=image_bytes,
            mime_type="image/png",
        )
        
        # Enrich prompt with professional guidelines
        enriched_prompt = _enrich_prompt_for_professional_video(prompt)
        logger.info(f"Enriched prompt length: {len(enriched_prompt)} characters")
        
        # Prepare video generation config
        config = types.GenerateVideosConfig(
            duration_seconds=duration_seconds,
            number_of_videos=1,
        )
        
        if negative_prompt and negative_prompt.strip():
            config.negative_prompt = negative_prompt
            logger.info(f"Added negative prompt: {len(negative_prompt)} characters")
        
        # Call Veo 3.1 API
        logger.info("Calling Veo 3.1 API for video generation...")
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=enriched_prompt,
            image=image,
            config=config,
        )
        
        logger.info(f"Video generation operation started: {operation.name}")
        
        # Poll for completion with timeout
        max_polls = 120  # 120 * 5 seconds = 600 seconds (10 minutes)
        poll_count = 0
        
        while not operation.done and poll_count < max_polls:
            poll_count += 1
            logger.info(f"Polling video generation status... (poll {poll_count})")
            await asyncio.sleep(5)
            operation = client.operations.get(operation.name)
        
        if poll_count >= max_polls:
            logger.error("Video generation timeout after 10 minutes")
            return {
                "status": "error",
                "message": f"Video generation timed out after {max_polls * 5} seconds",
            }
        
        if not operation.done:
            logger.error("Operation did not complete successfully")
            return {
                "status": "error",
                "message": "Video generation operation did not complete",
            }
        
        # Extract video from response
        logger.info("Video generation completed, extracting video data...")
        
        if not operation.response or not operation.response.generated_videos:
            logger.error("No videos in operation response")
            return {
                "status": "error",
                "message": "No video data in API response",
            }
        
        video = operation.response.generated_videos[0]
        video_bytes = video.video.video_bytes
        
        logger.info(f"Successfully generated video: {len(video_bytes)} bytes")
        
        # Encode video to base64
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")
        
        logger.info(f"Encoded video to base64: {len(video_base64)} characters")
        
        # Return success response
        return {
            "status": "success",
            "message": f"Video generated successfully in {poll_count * 5} seconds",
            "duration_seconds": duration_seconds,
            "prompt_used": enriched_prompt,
            "video_size_bytes": len(video_bytes),
            "video_data": video_base64,
            "model_used": "veo-3.1-generate-preview",
            "polls_required": poll_count,
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during video generation: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Video generation failed: {str(e)}",
        }


@mcp.tool
async def list_video_models() -> dict:
    """Lists available video generation models in Vertex AI.
    
    Returns information about available video models and their capabilities.
    Useful for checking which models are available in your project.
    
    Returns:
        dict: Response containing:
            - status: "success" or "error"
            - models: List of available video models with metadata
            - message: Status message
    """
    try:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        
        if not project or not location:
            return {
                "status": "error",
                "message": "Missing Vertex AI configuration",
            }
        
        logger.info("Listing available video models...")
        
        # For now, return known models since Veo is still in preview
        models = [
            {
                "name": "veo-3.1-generate-preview",
                "description": "Latest Veo 3.1 model for video generation",
                "max_duration_seconds": 30,
                "capabilities": [
                    "Image to video generation",
                    "Text to video generation",
                    "Professional quality output",
                ],
            },
        ]
        
        logger.info(f"Available models: {len(models)}")
        
        return {
            "status": "success",
            "models": models,
            "message": f"Found {len(models)} available video models",
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to list models: {str(e)}",
        }


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Veo 3.1 MCP Server")
    logger.info("=" * 60)
    logger.info("Listening on stdio...")
    logger.info("Available tools:")
    logger.info("  - generate_video_with_image")
    logger.info("  - list_video_models")
    logger.info("=" * 60)
    
    mcp.run()
