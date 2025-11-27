"""ADK Agent Configuration with MCP Tools Integration.

This module shows how to configure an ADK agent to use the Veo MCP server
for video generation. It demonstrates:
1. Loading MCP tools
2. Registering tool callbacks
3. Agent initialization with proper system prompts
"""

from google.adk.agents.llm_agent import Agent

from mcp_sample.mcp_tools import mcp_toolset
from mcp_sample.tool_callbacks import (
    after_tool_modifier,
    before_tool_modifier,
)

# System prompt for the video generation agent
VIDEO_AGENT_INSTRUCTION = """You are a professional video generation assistant.

Your role is to help users create high-quality presentation videos by:
1. Understanding their video requirements
2. Describing the video content in detail
3. Specifying camera movements and visual style
4. Calling the video generation tool with optimized prompts

IMPORTANT - Artifact Handling:
When you need to use an image as the starting frame for a video:
- Use the artifact_id (filename) provided by the user or system
- NEVER ask for base64 data or raw binary
- The system automatically converts artifact_id to base64 before sending to the MCP tool
- After the tool returns, the video is automatically saved as an artifact

PROMPT OPTIMIZATION TIPS:
- Be specific about camera movements: "slow zoom in", "rotating view", "tracking shot"
- Describe timing: "gradually appear", "fade smoothly", "transition quickly"
- Mention visual style: "professional blue theme", "minimalist", "corporate"
- Include duration: typically 8-15 seconds for presentation videos

Example workflow:
User: "Create a video of a rotating chart from slide 1"
You: "I'll generate a video showing a rotating 3D chart with smooth transitions.
     I'll use the chart image from your slide as the starting frame."
System: Calls video tool with artifact_id from user's image
Result: Video saved as artifact, ready to use in presentation
"""


def create_video_agent(
    agent_name: str = "presentation-video-generator",
    model: str = "gemini-2.5-flash",
) -> Agent:
    """Create a video generation agent with MCP tools.
    
    Args:
        agent_name: Name for the agent
        model: Gemini model to use (default: gemini-2.5-flash)
        
    Returns:
        Configured ADK agent with video generation capabilities
    """
    return Agent(
        model=model,
        name=agent_name,
        description="Generates high-quality presentation videos using Veo 3.1",
        instruction=VIDEO_AGENT_INSTRUCTION,
        tools=[
            mcp_toolset,
        ],
        before_tool_callback=before_tool_modifier,
        after_tool_callback=after_tool_modifier,
    )


# Create default agent instance
video_agent = create_video_agent()
