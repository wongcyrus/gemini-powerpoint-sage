# MCP Server Sample Implementation

This directory contains a complete, production-ready **Model Context Protocol (MCP) Server** sample that demonstrates how to integrate with Google ADK agents.

## Overview

The MCP server sample shows:
- ✅ FastMCP server setup and configuration
- ✅ Tool definition with proper typing and documentation
- ✅ Error handling and logging best practices
- ✅ Integration with Google Vertex AI APIs
- ✅ Tool callbacks for parameter transformation
- ✅ Artifact management for large binary data
- ✅ Environment configuration and credentials

## Architecture

```
┌─────────────────────────────────────────┐
│   ADK Agent (Vertex AI)                 │
│   - Calls tool with parameters          │
│   - Receives tool responses             │
└──────────────┬──────────────────────────┘
               │ Tool Call (artifact_id)
               ▼
┌─────────────────────────────────────────┐
│   before_tool_callback                  │
│   - Converts artifact_id → base64       │
│   - Loads artifact data from context    │
└──────────────┬──────────────────────────┘
               │ Tool Call (base64 data)
               ▼
┌─────────────────────────────────────────┐
│   MCP Server (FastMCP)                  │
│   - Video Generation Tool               │
│   - Calls Vertex AI Veo API             │
│   - Returns base64 video data           │
└──────────────┬──────────────────────────┘
               │ Response (base64 data)
               ▼
┌─────────────────────────────────────────┐
│   after_tool_callback                   │
│   - Saves base64 → artifact file        │
│   - Returns artifact_id reference       │
└──────────────┬──────────────────────────┘
               │ Response (artifact_id)
               ▼
┌─────────────────────────────────────────┐
│   ADK Agent                             │
│   - Lightweight response in context     │
│   - Can reference artifact anytime      │
└─────────────────────────────────────────┘
```

## Files in This Sample

### Core MCP Server
- **`veo_server.py`** - Main MCP server with video generation tool
  - FastMCP initialization
  - `generate_video_with_image()` tool implementation
  - Vertex AI Veo 3.1 API integration
  - Error handling and logging

### ADK Integration
- **`mcp_tools.py`** - MCP toolset configuration
  - STDIO connection parameters
  - Timeout and retry configuration
  - Alternative HTTP connection example

- **`tool_callbacks.py`** - Tool callbacks for parameter transformation
  - `before_tool_modifier()` - artifact_id → base64
  - `after_tool_modifier()` - base64 → artifact_id
  - Artifact lifecycle management

### Configuration & Setup
- **`agent_config.py`** - ADK agent configuration with MCP tools
  - Agent initialization
  - Tool registration
  - Callback integration

- **`.env.example`** - Environment variable template
  - Google Cloud credentials
  - Project and location settings

- **`pyproject.toml`** - Project dependencies

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Google Cloud credentials
# Set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 3. Test MCP Server Standalone

```bash
# Start the MCP server
uv run veo_server.py

# Should output:
# INFO: MCP server started, listening on stdio...
```

### 4. Connect to ADK Agent

```python
from agent_config import video_agent

# Create or modify your agent to use the MCP server
agent = video_agent

# Test with a simple prompt
response = await agent.run({
    "role": "user",
    "content": "Generate a video of a rotating product with professional lighting"
})
```

## Key Concepts

### 1. FastMCP Server Setup
```python
from fastmcp import FastMCP

mcp = FastMCP("Veo MCP Server")

@mcp.tool
async def my_tool(param: str) -> dict:
    """Tool documentation."""
    return {"result": "data"}

if __name__ == "__main__":
    mcp.run()
```

### 2. Tool Callbacks
**Before Tool Callback** - Transforms inputs:
```python
async def before_tool_modifier(tool, args, tool_context):
    if tool.name == "generate_video_with_image":
        # Convert artifact_id to base64
        artifact = await tool_context.load_artifact(args["image_data"])
        args["image_data"] = base64.b64encode(artifact.inline_data.data).decode()
```

**After Tool Callback** - Transforms outputs:
```python
async def after_tool_modifier(tool, args, tool_context, tool_response):
    if tool.name == "generate_video_with_image":
        # Save video as artifact, return artifact_id
        video_bytes = base64.b64decode(tool_response["video_data"])
        artifact_id = f"video_{tool_context.function_call_id}.mp4"
        await tool_context.save_artifact(artifact_id, video_bytes)
        return {"artifact_id": artifact_id}
```

### 3. Artifact Management
Artifacts store large binary data outside context:
- **Save**: `await tool_context.save_artifact(filename, data)`
- **Load**: `await tool_context.load_artifact(filename)`
- **Benefits**: Smaller context, faster token usage, persistent storage

## Configuration Options

### MCP Connection Types

**STDIO (Recommended for development)**
```python
from mcp.types import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "veo_server.py"],
        ),
        timeout=120,
    ),
)
```

**HTTP (Production deployment)**
```python
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
        timeout=120,
    ),
)
```

### Vertex AI Authentication

MCP server uses Vertex AI credentials from environment:
```python
client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)
```

Required environment variables:
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_CLOUD_LOCATION` - Region (us-central1, europe-west1, etc.)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON (optional, uses ADC by default)

## Performance & Optimization

| Metric | Value |
|--------|-------|
| Video generation time | 30-60 seconds per 8-second video |
| API polling interval | 5 seconds (configurable) |
| MCP server timeout | 120 seconds (configurable) |
| Video file size | 2-5 MB per video |
| Token usage | Dramatically reduced with artifacts |

**Token Savings Example**:
- Without artifacts: 1 video (5MB) = ~375,000 tokens in context
- With artifacts: 1 video reference = ~50 tokens in context
- **Savings: ~99.98% token reduction**

## Error Handling

The sample includes comprehensive error handling:

```python
try:
    # Vertex AI API call
    operation = client.models.generate_videos(...)
    
    # Poll until complete
    while not operation.done:
        await asyncio.sleep(5)
        operation = client.operations.get(operation)
        
    # Extract video
    video = operation.response.generated_videos[0]
    video_data = video.video.video_bytes
    
except google.api_core.exceptions.GoogleAPIError as e:
    logger.error(f"Vertex AI API error: {e}")
    return {"status": "error", "message": str(e)}
    
except asyncio.TimeoutError:
    logger.error("Video generation timed out")
    return {"status": "error", "message": "Timeout"}
    
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return {"status": "error", "message": str(e)}
```

## Testing

### Unit Tests
```bash
# Run tests
uv run pytest tests/

# With coverage
uv run pytest --cov=mcp_sample tests/
```

### Manual Testing

**Test 1: MCP Server Availability**
```bash
uv run veo_server.py
# Should output: "MCP server started, listening on stdio..."
# Ctrl+C to stop
```

**Test 2: Artifact Handling**
```python
# Load artifact
artifact = await tool_context.load_artifact("video_123.mp4")

# Verify data
assert artifact.inline_data.mime_type == "video/mp4"
assert len(artifact.inline_data.data) > 0
```

**Test 3: Full Integration**
```bash
# Start MCP server in one terminal
uv run veo_server.py

# Run agent in another terminal
python -c "
from agent_config import video_agent
import asyncio

result = asyncio.run(video_agent.run({
    'role': 'user',
    'content': 'Create a 8-second video of a product spinning'
}))
print(result)
"
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "MCP server not found" | STDIO command incorrect | Verify `uv run veo_server.py` works standalone |
| "Failed to generate video" | Vertex AI API disabled | Enable Veo API in Google Cloud console |
| "Missing credentials" | Missing env vars | Set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` |
| "Token limit exceeded" | Large base64 in context | Ensure `after_tool_callback` saves artifact |
| "Timeout during generation" | Video generation too slow | Increase timeout to 180+ seconds |
| "Artifact not found" | Wrong filename | Check artifact_id matches between callbacks |

## Implementation Checklist

When implementing MCP servers for your project:

- [ ] Create FastMCP server with tool(s)
- [ ] Define tool parameters with Annotated and Field
- [ ] Add comprehensive docstrings
- [ ] Test MCP server standalone with `mcp.run()`
- [ ] Create `mcp_tools.py` with connection configuration
- [ ] Implement `before_tool_callback` for input transformation
- [ ] Implement `after_tool_callback` for output transformation
- [ ] Add agent configuration with MCP toolset
- [ ] Test with ADK agent in web UI or Python
- [ ] Add error handling and logging
- [ ] Document tool usage and parameters
- [ ] Set up environment variables

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Veo API Documentation](https://ai.google.dev/gemini-api/docs/vision)
- [Google Vertex AI Python SDK](https://cloud.google.com/python/docs/reference/vertexai/latest)

## Examples

### Example 1: Simple Tool Without Artifacts

```python
@mcp.tool
async def simple_tool(text: Annotated[str, Field(description="Input text")]) -> dict:
    """A simple tool that doesn't deal with binary data."""
    return {"output": f"Processed: {text}"}
```

### Example 2: Tool with Progress Tracking

```python
@mcp.tool
async def long_running_tool(task_id: str) -> dict:
    """Tool that reports progress."""
    for i in range(10):
        print(f"Progress: {i+1}/10")
        await asyncio.sleep(1)
    return {"status": "completed", "task_id": task_id}
```

### Example 3: Tool with Multiple Parameters

```python
@mcp.tool
async def multi_param_tool(
    text: Annotated[str, Field(description="Input text")],
    count: Annotated[int, Field(description="Number of repetitions")] = 1,
    style: Annotated[str, Field(description="Text style")] = "normal"
) -> dict:
    """Tool with multiple parameters."""
    result = text * count
    return {"result": result, "style": style}
```

## Contributing

To extend this sample:

1. Add new tools to `veo_server.py`
2. Update `mcp_tools.py` to register new tools
3. Add callbacks in `tool_callbacks.py` if needed
4. Document in README.md
5. Add tests in `tests/`

## License

This sample is provided as-is for educational purposes.
