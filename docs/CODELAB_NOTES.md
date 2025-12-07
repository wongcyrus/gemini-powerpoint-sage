# ADK Multimodal Tool Interaction - Part 2 Implementation Guide
## Video Generation Agent with Veo 3.1 and MCP Toolset

Based on Google's Codelab: ADK with Multimodal Tool Interaction Part 2 (MCP Toolset with Tool Callbacks)

---

## Overview

This guide covers implementing a video generation agent using:
- **Veo 3.1 API** for video generation
- **FastMCP** for creating MCP servers
- **Google ADK (Agent Development Kit)** for agent orchestration
- **Tool Callbacks** for parameter/response transformation

### Architecture Flow

1. **Agent** → Calls MCP Toolset with artifact_id
2. **before_tool_callback** → Converts artifact_id to base64
3. **MCP Server** → Generates video via Veo 3.1 API
4. **after_tool_callback** → Stores video as artifact, returns artifact_id
5. **Agent** → Receives artifact reference instead of huge base64

---

## Step 1: Initialize Veo MCP Server

### Create MCP Server Directory
```bash
mkdir veo_mcp
touch veo_mcp/main.py
```

### Veo MCP Server Code (`veo_mcp/main.py`)

```python
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
import base64
import asyncio
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

mcp = FastMCP("Veo MCP Server")

@mcp.tool
async def generate_video_with_image(
    prompt: Annotated[
        str,
        Field(description="Text description of the video to generate")
    ],
    image_data: Annotated[
        str,
        Field(description="Base64-encoded image data to use as starting frame")
    ],
    negative_prompt: Annotated[
        str | None,
        Field(description="Things to avoid in the generated video"),
    ] = None,
) -> dict:
    """Generates a professional product marketing video from text prompt and starting image using Google's Veo API.
    
    This function uses an image as the first frame of the generated video and automatically
    enriches your prompt with professional video production quality guidelines to create
    high-quality marketing assets suitable for commercial use.
    
    AUTOMATIC ENHANCEMENTS APPLIED:
    - 4K cinematic quality with professional color grading
    - Smooth, stabilized camera movements
    - Professional studio lighting setup
    - Shallow depth of field for product focus
    - Commercial-grade production quality
    - Marketing-focused visual style
    
    PROMPT WRITING TIPS:
    Describe what you want to see in the video. Focus on:
    - Product actions/movements (e.g., "rotating slowly", "zooming into details")
    - Desired camera angles (e.g., "close-up of the product", "wide shot")
    - Background/environment (e.g., "minimalist white backdrop", "lifestyle setting")
    - Any specific details about the product presentation
    
    The system will automatically enhance your prompt with professional production quality.
    
    Args:
        prompt: Description of the video to generate. Focus on the core product presentation
                you want. The system will automatically add professional quality enhancements.
        image_data: Base64-encoded image data to use as the starting frame
        negative_prompt: Optional prompt describing what to avoid in the video
    
    Returns:
        dict: A dictionary containing:
        - status: 'success' or 'error'
        - message: Description of the result
        - video_data: Base64-encoded video data (on success only)
    """
    
    try:
        # Initialize the Gemini client
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
        
        # Decode the image
        image_bytes = base64.b64decode(image_data)
        
        print(f"Successfully decoded image data: {len(image_bytes)} bytes")
        
        # Create image object
        image = types.Image(
            image_bytes=image_bytes,
            mime_type="image/png"
        )
        
        # Prepare the config
        config = types.GenerateVideosConfig(
            duration_seconds=8,
            number_of_videos=1,
        )
        
        if negative_prompt:
            config.negative_prompt = negative_prompt
        
        # Enrich the prompt for professional marketing quality
        enriched_prompt = enrich_prompt_for_marketing(prompt)
        
        # Generate the video (async operation)
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=enriched_prompt,
            image=image,
            config=config,
        )
        
        # Poll until the operation is complete
        poll_count = 0
        while not operation.done:
            poll_count += 1
            print(f"Waiting for video generation to complete... (poll {poll_count})")
            await asyncio.sleep(5)
            operation = client.operations.get(operation)
        
        # Download the video and convert to base64
        video = operation.response.generated_videos[0]
        
        # Get video bytes and encode to base64
        video_bytes = video.video.video_bytes
        
        video_base64 = base64.b64encode(video_bytes).decode("utf-8")
        
        print(f"Video generated successfully: {len(video_bytes)} bytes")
        
        return {
            "status": "success",
            "message": f"Video with image generated successfully after {poll_count * 5} seconds",
            "complete_prompt": enriched_prompt,
            "video_data": video_base64,
        }
        
    except Exception as e:
        logging.error(e)
        
        return {
            "status": "error",
            "message": f"Error generating video with image: {str(e)}",
        }

def enrich_prompt_for_marketing(user_prompt: str) -> str:
    """Enriches user prompt with professional video production quality enhancements.
    
    Adds cinematic quality, professional lighting, smooth camera work, and marketing-focused
    elements to ensure high-quality product marketing videos.
    """
    
    enhancement_prefix = """Create a high-quality, professional product marketing video with the following characteristics:
TECHNICAL SPECIFICATIONS:
- 4K cinematic quality with professional color grading
- Smooth, stabilized camera movements
- Professional studio lighting setup with soft, even illumination
- Shallow depth of field for product focus
- High dynamic range (HDR) for vibrant colors
VISUAL STYLE:
- Clean, minimalist aesthetic suitable for premium brand marketing
- Elegant and sophisticated presentation
- Commercial-grade production quality
- Attention to detail in product showcase
USER'S SPECIFIC REQUIREMENTS:
"""
    
    enhancement_suffix = """
ADDITIONAL QUALITY GUIDELINES:
- Ensure smooth transitions and natural motion
- Maintain consistent lighting throughout
- Keep the product as the clear focal point
- Use professional camera techniques (slow pans, tracking shots, or dolly movements)
- Apply subtle motion blur for cinematic feel
- Ensure brand-appropriate tone and style"""
    
    return f"{enhancement_prefix}{user_prompt}{enhancement_suffix}"

if __name__ == "__main__":
    mcp.run()
```

### Copy Environment File
```bash
cp product_photo_editor/.env veo_mcp/
```

### Test MCP Server
```bash
uv run veo_mcp/main.py
```

Expected output shows FastMCP starting the server.

---

## Step 2: Connect MCP Server to ADK Agent

### Create MCP Tools Configuration (`product_photo_editor/mcp_tools.py`)

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=[
                "run",
                "veo_mcp/main.py",
            ],
        ),
        timeout=120,  # seconds
    ),
)

# Option to connect to remote MCP server
# from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
# mcp_toolset = MCPToolset(
#     connection_params=StreamableHTTPConnectionParams(
#         url="http://localhost:8000/mcp",
#         timeout=120,
#     ),
# )
```

---

## Step 3: Tool Call Parameter Modification (before_tool_callback)

### Create Tool Callbacks (`product_photo_editor/tool_callbacks.py`)

```python
# product_photo_editor/tool_callbacks.py
from google.genai.types import Part
from typing import Any
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool.mcp_tool import McpTool
import base64
import logging
import json
from mcp.types import CallToolResult

async def before_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
):
    """Modify tool arguments before execution.
    
    Converts artifact_id references to base64-encoded data for tools that require it.
    """
    
    # Identify which tool input should be modified
    if isinstance(tool, McpTool) and tool.name == "generate_video_with_image":
        logging.info(
            "Modify tool args for artifact: %s",
            args["image_data"]
        )
        
        # Get the artifact filename from the tool input argument
        artifact_filename = args["image_data"]
        
        artifact = await tool_context.load_artifact(
            filename=artifact_filename
        )
        
        file_data = artifact.inline_data.data
        
        # Convert byte data to base64 string
        base64_data = base64.b64encode(file_data).decode("utf-8")
        
        # Then modify the tool input argument
        args["image_data"] = base64_data


async def after_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict | CallToolResult,
) -> dict:
    """Modify tool responses after execution.
    
    Stores large video data as artifacts and returns artifact references instead.
    """
    
    if isinstance(tool, McpTool) and tool.name == "generate_video_with_image":
        tool_result = json.loads(tool_response.content[0].text)
        
        # Get the expected response field which contains the video data
        video_data = tool_result["video_data"]
        
        artifact_filename = f"video_{tool_context.function_call_id}.mp4"
        
        # Convert base64 string to byte data
        video_bytes = base64.b64decode(video_data)
        
        # Save the video as artifact
        await tool_context.save_artifact(
            filename=artifact_filename,
            artifact=Part(
                inline_data={
                    "mime_type": "video/mp4",
                    "data": video_bytes
                }
            ),
        )
        
        # Remove the video data from the tool response
        tool_result.pop("video_data")
        
        # Then modify the tool response to include the artifact filename and remove the base64 string
        tool_result["video_artifact_id"] = artifact_filename
        
        logging.info(
            "Modify tool response for artifact: %s",
            tool_result["video_artifact_id"]
        )
        
        return tool_result
```

---

## Step 4: Update Agent Configuration

### Modify Agent (`product_photo_editor/agent.py`)

```python
# product_photo_editor/agent.py
from google.adk.agents.llm_agent import Agent
from product_photo_editor.custom_tools import edit_product_asset
from product_photo_editor.mcp_tools import mcp_toolset
from product_photo_editor.model_callbacks import before_model_modifier
from product_photo_editor.tool_callbacks import (
    before_tool_modifier,
    after_tool_modifier,
)
from product_photo_editor.prompt import AGENT_INSTRUCTION

root_agent = Agent(
    model="gemini-2.5-flash",
    name="product_photo_editor",
    description="""A friendly product photo editor assistant that helps small business
owners edit and enhance their product photos. Perfect for improving photos of handmade
goods, food products, crafts, and small retail items""",
    instruction=AGENT_INSTRUCTION
    + """
**IMPORTANT: Base64 Argument Rule on Tool Call**
If you found any tool call arguments that requires base64 data,
ALWAYS provide the artifact_id of the referenced file to
the tool call. NEVER ask user to provide base64 data.
Base64 data encoding process is out of your
responsibility and will be handled in another part of the system.
""",
    tools=[
        edit_product_asset,
        mcp_toolset,
    ],
    before_model_callback=before_model_modifier,
    before_tool_callback=before_tool_modifier,
    after_tool_callback=after_tool_modifier,
)
```

---

## Key Concepts

### Tool Callbacks Workflow

```
User Request
    ↓
before_model_callback (optional)
    ↓
Agent calls tool with artifact_id
    ↓
before_tool_callback (transform artifact_id → base64)
    ↓
MCP Tool executes (Veo 3.1 generates video)
    ↓
after_tool_callback (save base64 → artifact, return artifact_id)
    ↓
Agent receives artifact reference (lightweight)
    ↓
Agent responds to user
```

### Why Callbacks?

1. **Parameter Transformation**: Convert artifact IDs to base64 before sending to MCP
2. **Token Efficiency**: Store large base64 responses as artifacts instead of in context
3. **Clean Interface**: Agent works with artifact references, not raw binary data

---

## Implementation Steps for Your Project

For your `gemini-powerpoint-sage` project:

1. **Create Veo MCP Server** in `veo_mcp/main.py`
   - Follow the code template above
   - Customize `enrich_prompt_for_marketing()` for presentation videos
   
2. **Create MCP Toolset Config** in `services/mcp_tools.py`
   - Setup STDIO connection to veo_mcp process
   
3. **Create Tool Callbacks** in `services/tool_callbacks.py`
   - `before_tool_modifier`: artifact_id → base64
   - `after_tool_modifier`: base64 → artifact_id
   
4. **Update Video Generator Agent**
   - Add `mcp_toolset` to tools list
   - Add callbacks: `before_tool_callback`, `after_tool_callback`
   - Update instructions to use artifact_id pattern
   
5. **Environment Setup**
   - Ensure `.env` has `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`
   - Enable Vertex AI API in Google Cloud

---

## Testing

```bash
# Run the web UI
uv run adk web --port 8080

# Then:
# 1. Upload a slide image
# 2. Ask: "Generate a slow zoom in and moving from left and right animation"
# 3. Agent calls Veo 3.1 via MCP server
# 4. Video is generated and saved as artifact
```

---

## Dependencies

Add to your `requirements.txt`:
```
google-adk>=1.0.0
fastmcp>=2.0.0
google-genai>=0.3.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

## Performance Notes

- **Video generation time**: ~30-60 seconds for 8-second video via Veo 3.1
- **API polling interval**: 5 seconds by default (configurable)
- **Timeout**: 120 seconds for MCP server operations
- **Video size**: ~2-5 MB per video (varies by quality/content)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to generate video" | Check Vertex AI API is enabled, credentials valid |
| Token limit exceeded | Ensure `after_tool_callback` removes base64 data |
| MCP server not connecting | Verify `uv run` command works standalone |
| Artifact not found | Check artifact filenames match between callbacks |

---

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Veo API Documentation](https://ai.google.dev/gemini-api/docs/vision)
- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
