"""Example: Using the Video Generation Agent with MCP Server.

This example shows how to:
1. Initialize the video agent
2. Call it with a prompt and image
3. Handle the generated video artifact
"""

import asyncio
import logging
from pathlib import Path

from mcp_sample.agent_config import video_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def example_generate_video_from_slide() -> None:
    """Example: Generate a video from a slide image.
    
    Demonstrates the typical workflow:
    1. User provides a slide image and description
    2. Agent creates an enhanced prompt
    3. Agent calls video generation tool
    4. Video is automatically saved as artifact
    5. Agent returns reference to the video
    """
    logger.info("Starting video generation example...")
    
    # Example: User has a slide image (already saved as artifact)
    slide_image = "slide_1.png"  # Artifact filename
    
    # User's video request
    user_request = f"""
    I have a slide image at artifact '{slide_image}'.
    
    Please generate a professional 8-second video that:
    - Shows the slide image as the starting frame
    - Includes a smooth zoom effect focusing on key elements
    - Uses professional lighting and cinematography
    - Maintains a corporate blue color theme
    - Has subtle animations and smooth transitions
    """
    
    logger.info("User request: %s", user_request)
    
    # Call the agent
    logger.info("Calling video generation agent...")
    response = await video_agent.run(
        {
            "role": "user",
            "content": user_request,
        }
    )
    
    logger.info("Agent response: %s", response)
    
    # The response should contain artifact_id reference
    # Example output:
    # {
    #     "artifact_id": "video_abc123.mp4",
    #     "status": "success",
    #     "message": "Video generated successfully in 120 seconds"
    # }


async def example_batch_generate_videos() -> None:
    """Example: Generate videos for multiple slides.
    
    Demonstrates batch processing where videos are generated
    for each slide in a presentation.
    """
    logger.info("Starting batch video generation example...")
    
    # List of slide artifacts
    slides = [
        "slide_1.png",
        "slide_2.png",
        "slide_3.png",
    ]
    
    # Video requests for each slide
    requests = [
        "A rotating 3D concept map with smooth transitions",
        "A dynamic dashboard with real-time data updates",
        "A product showcase with professional lighting",
    ]
    
    generated_videos = []
    
    for slide, request in zip(slides, requests):
        logger.info("Generating video for %s: %s", slide, request)
        
        prompt = f"""
        Generate a professional 8-second video using the slide image
        at artifact '{slide}'.
        
        Video description: {request}
        """
        
        response = await video_agent.run(
            {
                "role": "user",
                "content": prompt,
            }
        )
        
        # Extract artifact_id from response
        artifact_id = response.get("artifact_id")
        if artifact_id:
            generated_videos.append(
                {
                    "slide": slide,
                    "video": artifact_id,
                    "description": request,
                }
            )
            logger.info("Video generated: %s -> %s", slide, artifact_id)
        else:
            logger.error("Failed to generate video for %s", slide)
    
    logger.info("Batch processing complete: %d videos generated",
                len(generated_videos))
    
    return generated_videos


async def main():
    """Run examples."""
    logger.info("=" * 70)
    logger.info("MCP Server Video Generation Examples")
    logger.info("=" * 70)
    
    try:
        # Example 1: Single video generation
        logger.info("\nExample 1: Generate single video")
        logger.info("-" * 70)
        await example_generate_video_from_slide()
        
    except Exception as e:
        logger.error("Example failed: %s", str(e), exc_info=True)
    
    logger.info("=" * 70)
    logger.info("Examples complete")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
