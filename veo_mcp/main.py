"""Veo 3.1 MCP Server for video generation.

FastMCP-based server that exposes video generation capabilities to ADK agents.
Generates professional promotional videos from images and text prompts.
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

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Veo MCP Server")


@mcp.tool
async def generate_video_with_image(
    prompt: Annotated[
        str,
        Field(
            description=(
                "Text description of the video to generate. "
                "Include camera movements, environment, and style."
            )
        ),
    ],
    image_data: Annotated[
        str,
        Field(
            description=(
                "Base64-encoded image data to use as starting frame"
            )
        ),
    ],
    negative_prompt: Annotated[
        str | None,
        Field(
            description="Things to avoid in the generated video"
        ),
    ] = None,
) -> dict:
    """Generate a professional promotional video using Veo 3.1.

    Creates an 8-second video from a slide image and text prompt,
    automatically enhancing with professional production guidelines.

    AUTOMATIC ENHANCEMENTS:
    - 4K cinematic quality with professional color grading
    - Smooth, stabilized camera movements
    - Professional studio lighting setup
    - Shallow depth of field for content focus
    - Commercial-grade production quality

    PROMPT GUIDELINES:
    - Describe product/content actions and movements
    - Specify camera angles and perspectives
    - Include background and environment preferences
    - Use clear, descriptive language
    - Focus on visual storytelling

    Args:
        prompt: Video description focused on core presentation
        image_data: Base64-encoded image to use as first frame
        negative_prompt: Optional descriptions of what to avoid

    Returns:
        dict: Contains status, message, complete_prompt, and video_data
    """
    try:
        # Initialize Gemini client with Vertex AI
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )

        logger.info("Decoding image data for video generation")

        # Decode image from base64
        image_bytes = base64.b64decode(image_data)
        logger.info("Successfully decoded image: %d bytes", len(
            image_bytes
        ))

        # Create image object for Veo API
        image = types.Image(
            image_bytes=image_bytes,
            mime_type="image/png"
        )

        # Configure video generation
        config = types.GenerateVideosConfig(
            duration_seconds=8,
            number_of_videos=1,
        )

        if negative_prompt:
            config.negative_prompt = negative_prompt

        # Enrich prompt with professional guidelines
        enriched_prompt = _enrich_prompt_for_presentation(prompt)

        logger.info(
            "Calling Veo 3.1 API with enriched prompt. "
            "This may take 30-60 seconds..."
        )

        # Call Veo API
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=enriched_prompt,
            image=image,
            config=config,
        )

        # Poll for completion
        poll_count = 0
        while not operation.done:
            poll_count += 1
            logger.info(
                "Waiting for video generation... (poll %d, %d seconds)",
                poll_count,
                poll_count * 5
            )
            await asyncio.sleep(5)
            operation = client.operations.get(operation)

        logger.info(
            "Video generation completed after %d polls",
            poll_count
        )

        # Extract generated video
        video = operation.response.generated_videos[0]
        video_bytes = video.video.video_bytes

        # Encode to base64
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")

        logger.info(
            "Video generated successfully: %d bytes",
            len(video_bytes)
        )

        return {
            "status": "success",
            "message": (
                f"Video generated successfully in "
                f"{poll_count * 5} seconds"
            ),
            "complete_prompt": enriched_prompt,
            "video_data": video_base64,
        }

    except Exception as e:
        logger.error("Video generation failed: %s", str(e))
        return {
            "status": "error",
            "message": f"Error generating video: {str(e)}",
        }


def _enrich_prompt_for_presentation(
    user_prompt: str,
) -> str:
    """Enrich user prompt with professional production guidelines.

    Args:
        user_prompt: Original user-provided prompt

    Returns:
        Enhanced prompt with professional guidelines
    """
    enhancement_prefix = """Create a high-quality, professional \
presentation video with these specifications:

TECHNICAL SPECIFICATIONS:
- 4K cinematic quality with professional color grading
- Smooth, stabilized camera movements
- Professional studio lighting with soft, even illumination
- Shallow depth of field for content focus
- High dynamic range (HDR) for vibrant, accurate colors

VISUAL STYLE:
- Clean, professional aesthetic suitable for business presentations
- Elegant and sophisticated presentation
- Commercial-grade production quality
- Attention to detail in content showcase
- Smooth transitions and natural motion

USER'S SPECIFIC REQUIREMENTS:
"""

    enhancement_suffix = """
QUALITY GUIDELINES:
- Maintain professional, polished appearance throughout
- Keep content as clear focal point
- Use professional camera techniques (dolly, tracking, slow pans)
- Apply subtle motion for cinematic feel
- Ensure brand-appropriate tone
"""

    return f"{enhancement_prefix}{user_prompt}{enhancement_suffix}"


if __name__ == "__main__":
    mcp.run()
