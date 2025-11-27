# MCP Sample Implementation Guide

Complete, production-ready implementation guide for building and integrating MCP servers with Google ADK.

## What is an MCP Server?

**Model Context Protocol (MCP)** is a standard for connecting AI agents with tools and data sources. An MCP server:
- Exposes a set of tools that agents can call
- Runs as a separate process (STDIO) or service (HTTP)
- Handles tool execution and returns results
- Enables safe, sandboxed tool access

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│  Google ADK Agent (Vertex AI)                    │
│  ├─ Understands user requests                   │
│  ├─ Plans tool usage                            │
│  └─ Interprets results                          │
└────────────────┬─────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │ Tool Callbacks   │
        ├─ before: id→b64  │ Transform parameters
        └────────┬─────────┘
                 │
        ┌────────▼──────────┐
        │  MCP Server       │
        │ (FastMCP)         │ Execute tool
        │ ├─ Tool 1         │
        │ ├─ Tool 2         │
        │ └─ Tool N         │
        └────────┬──────────┘
                 │
        ┌────────▼─────────┐
        │ Tool Callbacks   │
        ├─ after: b64→id   │ Transform response
        └────────┬─────────┘
                 │
        ┌────────▼─────────────────┐
        │ Artifact Storage         │
        │ (Large files saved here) │
        └──────────────────────────┘
```

## File Structure

```
mcp_sample/
├── README.md                    # Overview and quick start
├── GUIDE.md                     # This file - implementation guide
├── veo_server.py               # Main MCP server implementation
├── mcp_tools.py                # MCP toolset configuration
├── tool_callbacks.py           # Input/output transformation
├── agent_config.py             # ADK agent setup
├── example_usage.py            # Usage examples
├── pyproject.toml              # Project dependencies
├── .env.example                # Environment variables template
└── tests/
    ├── test_mcp_server.py      # Unit tests
    └── test_integration.py     # Integration tests
```

## Building Your Own MCP Server

### Step 1: Create the Server File

```python
# my_mcp_server.py
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

mcp = FastMCP("My MCP Server")

@mcp.tool
async def my_tool(
    param1: Annotated[str, Field(description="Description of param1")],
    param2: Annotated[int, Field(description="Description of param2")] = 10,
) -> dict:
    """Tool documentation shown to the agent."""
    # Your implementation here
    result = do_something(param1, param2)
    return {
        "status": "success",
        "result": result,
    }

if __name__ == "__main__":
    mcp.run()
```

### Step 2: Create MCP Tools Configuration

```python
# mcp_tools_config.py
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["my_mcp_server.py"],
        ),
        timeout=60,
    ),
)
```

### Step 3: Create Tool Callbacks (if handling binary data)

```python
# mcp_callbacks.py
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool.mcp_tool import McpTool
from google.adk.tools.tool_context import ToolContext

async def before_tool_modifier(tool, args, tool_context):
    """Transform inputs before MCP tool call."""
    if isinstance(tool, McpTool) and tool.name == "my_tool":
        # Transform args if needed
        pass

async def after_tool_modifier(tool, args, tool_context, tool_response):
    """Transform outputs after MCP tool call."""
    if isinstance(tool, McpTool) and tool.name == "my_tool":
        # Transform response if needed
        pass
```

### Step 4: Configure ADK Agent

```python
# my_agent.py
from google.adk.agents.llm_agent import Agent
from mcp_tools_config import mcp_toolset
from mcp_callbacks import before_tool_modifier, after_tool_modifier

agent = Agent(
    model="gemini-2.5-flash",
    name="my-agent",
    instruction="Your system prompt here...",
    tools=[mcp_toolset],
    before_tool_callback=before_tool_modifier,
    after_tool_callback=after_tool_modifier,
)
```

## Key Implementation Patterns

### Pattern 1: Simple Tool (No Binary Data)

```python
@mcp.tool
async def calculate(
    operation: Annotated[str, Field(description="add|subtract|multiply")],
    a: Annotated[int, Field(description="First number")],
    b: Annotated[int, Field(description="Second number")],
) -> dict:
    """Performs basic math operations."""
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    else:
        result = a * b
    
    return {
        "status": "success",
        "result": result,
        "operation": operation,
    }
```

### Pattern 2: Tool with External API

```python
import httpx

@mcp.tool
async def fetch_data(
    url: Annotated[str, Field(description="URL to fetch from")],
) -> dict:
    """Fetches data from an HTTP endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
        
        return {
            "status": "success",
            "data": response.json(),
            "status_code": response.status_code,
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
```

### Pattern 3: Tool with Artifact Handling

```python
import base64

@mcp.tool
async def process_image(
    image_data: Annotated[str, Field(description="Base64-encoded image")],
    operation: Annotated[str, Field(description="blur|enhance|rotate")],
) -> dict:
    """Processes image data."""
    try:
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Process image (using PIL, OpenCV, etc.)
        result = apply_operation(image_bytes, operation)
        
        # Encode result back to base64
        result_base64 = base64.b64encode(result).decode("utf-8")
        
        return {
            "status": "success",
            "image_data": result_base64,
            "operation": operation,
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
```

### Pattern 4: Tool with Progress Tracking

```python
@mcp.tool
async def long_operation(
    task_id: Annotated[str, Field(description="Unique task identifier")],
    duration: Annotated[int, Field(description="Duration in seconds")],
) -> dict:
    """Long-running operation with progress."""
    steps = duration
    
    for i in range(steps):
        print(f"Progress: {i+1}/{steps}")
        await asyncio.sleep(1)
    
    return {
        "status": "success",
        "task_id": task_id,
        "completed_at": datetime.now().isoformat(),
    }
```

## Tool Callback Patterns

### Callback Pattern 1: Simple Transformation

```python
async def before_tool_modifier(tool, args, tool_context):
    """Normalize input parameters."""
    if isinstance(tool, McpTool):
        # Convert all string inputs to lowercase
        for key, value in args.items():
            if isinstance(value, str):
                args[key] = value.lower()
```

### Callback Pattern 2: Artifact Loading

```python
async def before_tool_modifier(tool, args, tool_context):
    """Convert artifact_id to actual data."""
    if isinstance(tool, McpTool) and "artifact_id" in args:
        artifact_id = args["artifact_id"]
        
        # Load from context
        artifact = await tool_context.load_artifact(artifact_id)
        
        # Convert to base64 for MCP tool
        data = base64.b64encode(artifact.inline_data.data).decode()
        
        # Replace in args
        args["data"] = data
        del args["artifact_id"]
```

### Callback Pattern 3: Response Artifact Saving

```python
async def after_tool_modifier(tool, args, tool_context, response):
    """Save response data as artifact."""
    if isinstance(tool, McpTool) and "output_data" in response:
        output_data = response["output_data"]
        
        # Decode base64 to bytes
        output_bytes = base64.b64decode(output_data)
        
        # Save as artifact
        artifact_id = f"output_{tool_context.function_call_id}.bin"
        await tool_context.save_artifact(
            artifact_id,
            Part(inline_data={
                "mime_type": "application/octet-stream",
                "data": output_bytes,
            }),
        )
        
        # Update response
        response.pop("output_data")
        response["artifact_id"] = artifact_id
        
        return response
```

## Best Practices

### 1. Error Handling

```python
@mcp.tool
async def robust_tool(param: str) -> dict:
    """Tool with comprehensive error handling."""
    
    try:
        # Validate input
        if not param or not param.strip():
            return {"status": "error", "message": "Parameter cannot be empty"}
        
        # Execute operation
        result = do_work(param)
        
        return {
            "status": "success",
            "result": result,
        }
    
    except ValueError as e:
        logger.error("Validation error: %s", e)
        return {"status": "error", "message": f"Invalid input: {str(e)}"}
    
    except TimeoutError:
        logger.error("Operation timed out")
        return {"status": "error", "message": "Operation took too long"}
    
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return {"status": "error", "message": "Internal server error"}
```

### 2. Logging

```python
import logging

logger = logging.getLogger(__name__)

@mcp.tool
async def well_logged_tool(param: str) -> dict:
    """Tool with comprehensive logging."""
    
    logger.info("Tool called with param: %s", param)
    
    try:
        logger.debug("Starting operation...")
        result = do_work(param)
        logger.info("Operation succeeded")
        
        return {"status": "success", "result": result}
    
    except Exception as e:
        logger.error("Operation failed: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}
```

### 3. Async/Await

```python
@mcp.tool
async def async_tool(url: str) -> dict:
    """Properly async tool using async operations."""
    
    try:
        # Use async operations
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        
        # Use await for async calls
        data = await process_response(response)
        
        return {"status": "success", "data": data}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### 4. Documentation

```python
@mcp.tool
async def well_documented_tool(
    param: Annotated[
        str,
        Field(
            description=(
                "Detailed description of this parameter. "
                "Explain expected format, valid values, examples."
            )
        ),
    ],
) -> dict:
    """Comprehensive tool documentation.
    
    This is shown to the agent and helps it understand
    how to use this tool effectively.
    
    Args:
        param: Description matches the Field description
        
    Returns:
        dict containing status and result fields
    """
    pass
```

## Testing MCP Servers

### Unit Test Example

```python
# test_mcp_server.py
import pytest
from mcp_sample.veo_server import generate_video_with_image

@pytest.mark.asyncio
async def test_generate_video_success():
    """Test successful video generation."""
    result = await generate_video_with_image(
        prompt="Test video",
        image_data="base64_test_image...",
    )
    
    assert result["status"] == "success"
    assert "video_data" in result
```

### Integration Test Example

```python
# test_integration.py
import pytest
from mcp_sample.agent_config import video_agent

@pytest.mark.asyncio
async def test_agent_integration():
    """Test agent with MCP server integration."""
    response = await video_agent.run({
        "role": "user",
        "content": "Generate a video",
    })
    
    assert response is not None
```

## Deployment Options

### Option 1: STDIO (Development)

```python
# Best for: Local development, testing
# Startup: MCP server runs as child process
# Communication: stdout/stdin pipes

mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["veo_server.py"],
        ),
        timeout=120,
    ),
)
```

### Option 2: HTTP (Production)

```python
# Best for: Production, remote servers
# Startup: MCP server runs independently
# Communication: HTTP REST API

mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://mcp-server.example.com:8000/mcp",
        timeout=120,
    ),
)
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "MCP server not found" | Command path wrong | Verify `python veo_server.py` works |
| "Tool not recognized" | Tool name mismatch | Check tool name matches in callbacks |
| "Timeout error" | Operation too slow | Increase timeout parameter |
| "Connection refused" | Server not running | Start MCP server first (HTTP mode) |
| "Memory leak" | Large responses in context | Implement artifact saving in callbacks |

## Performance Optimization

### 1. Token Efficiency

```python
# Bad: Returns large base64 string in context
return {"video_data": "base64_string..."}  # ~375,000 tokens

# Good: Saves as artifact, returns reference
# after_tool_callback saves artifact
return {"artifact_id": "video_123.mp4"}  # ~50 tokens
# Savings: 99.98% ✅
```

### 2. Timeout Configuration

```python
# Development (short timeouts)
timeout=30  # 30 seconds

# Production (allow long operations)
timeout=300  # 5 minutes
```

### 3. Connection Pooling

```python
# Reuse HTTP client connections
async with httpx.AsyncClient() as client:
    response = await client.get(url)  # Reuses connection
```

## Security Considerations

1. **Input Validation**: Always validate inputs before processing
2. **Error Messages**: Don't leak sensitive info in errors
3. **Timeouts**: Prevent resource exhaustion with timeouts
4. **Logging**: Don't log sensitive data
5. **Authentication**: Verify credentials before executing

## Next Steps

1. Copy this sample to your project
2. Modify `veo_server.py` for your use case
3. Update `tool_callbacks.py` if handling different data types
4. Configure `agent_config.py` with your agent requirements
5. Test with `example_usage.py`
6. Deploy following your deployment option

## References

- [FastMCP Documentation](https://gofastmcp.com/)
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Vertex AI Python SDK](https://cloud.google.com/python/docs/reference/vertexai/latest)
