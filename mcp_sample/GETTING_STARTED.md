# Getting Started with MCP Sample

This file will help you get up and running in 5 minutes.

## What is This?

A **production-ready MCP (Model Context Protocol) Server sample** that shows you how to:
- Build FastMCP servers
- Integrate with Google ADK agents
- Handle large files efficiently
- Deploy to production

## Quick Start (5 Minutes)

### Step 1: Setup Environment (1 min)

```bash
# Navigate to the sample directory
cd mcp_sample

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Set: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION
```

### Step 2: Install Dependencies (1 min)

```bash
# Option A: Using pip
pip install -r requirements.txt

# Option B: Using uv (faster)
uv sync
```

### Step 3: Test the Server (2 min)

```bash
# Start the MCP server
python veo_server.py

# You should see:
# "MCP server started, listening on stdio..."

# Press Ctrl+C to stop
```

### Step 4: Run an Example (1 min)

```bash
# In a new terminal:
python example_usage.py
```

That's it! You now have a working MCP server. 🎉

---

## File Structure

```
mcp_sample/
├── README.md                    ← Overview and features
├── veo_server.py               ← Main MCP server ⭐
├── tool_callbacks.py           ← Artifact handling
├── agent_config.py             ← Agent setup
├── mcp_tools.py                ← MCP configuration
├── example_usage.py            ← Usage examples
├── .env.example                ← Environment template
├── pyproject.toml              ← Dependencies
└── tests/                       ← Test suite
```

---

## Next: Understanding the Code

### 1. Read the Overview (5 min)
- Open `README.md`
- Skim the architecture section
- Understand what an MCP server does

### 2. Study the Implementation (15 min)
- Open `veo_server.py`
- Read the docstrings
- Follow the tool implementation

### 3. Understand Artifact Handling (10 min)
- Open `tool_callbacks.py`
- Read the before/after callbacks
- See how artifacts optimize tokens

### 4. Learn the Patterns (30 min)
- Open `GUIDE.md`
- Read the implementation patterns
- Study the examples

---

## Common Tasks

### "I want to add my own tool"
1. Open `veo_server.py`
2. Copy the `@mcp.tool` function
3. Modify it for your use case
4. Update docstring
5. Add error handling

Example:
```python
@mcp.tool
async def my_new_tool(
    param: Annotated[str, Field(description="...")],
) -> dict:
    """Tool documentation."""
    try:
        result = do_work(param)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error("Error: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}
```

### "I want to deploy this"
- See `README.md` → Deployment Options
- Or see `GUIDE.md` → Deployment Options

### "I got an error"
- See `README.md` → Troubleshooting
- Check that `.env` variables are set
- Verify MCP server starts with `python veo_server.py`

### "I want to understand callbacks"
- See `tool_callbacks.py`
- Read before_tool_modifier (artifact_id → base64)
- Read after_tool_modifier (base64 → artifact_id)
- See `GUIDE.md` → Tool Callback Patterns

---

## Key Concepts

### MCP (Model Context Protocol)
A standard for connecting AI agents with tools. Think of it as an API that agents can call.

### FastMCP
A Python library that makes it easy to build MCP servers.

### Tool Callbacks
Functions that transform tool inputs/outputs:
- `before_tool_callback`: Convert artifact_id to base64
- `after_tool_callback`: Save base64 as artifact, return ID

### Artifacts
Large files stored separately from the agent context, saving ~99.98% tokens.

### Agent
The AI model that understands requests and calls tools (e.g., Gemini 2.5).

---

## File Recommendations

### For Beginners
1. `README.md` - Understand what this is
2. `veo_server.py` - See working code
3. `example_usage.py` - Try it out

### For Implementation
1. `veo_server.py` - Copy and modify
2. `tool_callbacks.py` - Adapt callbacks if needed
3. `agent_config.py` - Configure your agent

### For Deep Dive
1. `GUIDE.md` - Learn patterns
2. `tests/test_mcp_sample.py` - See test patterns
3. `IMPLEMENTATION_SUMMARY.md` - Project details

---

## Common Questions

**Q: Do I need to run the server in a separate terminal?**  
A: During development yes. In production, it can run as a service (Docker, Cloud Run, etc.).

**Q: How do artifacts save tokens?**  
A: Base64 video data in context = ~375,000 tokens. Artifact ID = ~50 tokens. That's 99.98% savings!

**Q: Can I add more tools?**  
A: Yes! Copy the `@mcp.tool` decorator and create your own function.

**Q: Does this work with other models?**  
A: The sample uses Gemini, but the pattern works with any ADK-compatible model.

**Q: How do I deploy this?**  
A: See deployment options in `GUIDE.md`. Docker and Cloud Run examples included.

---

## What's Inside Each File

### veo_server.py (440 lines)
**The Main Implementation** - This is what you need to customize for your use case.
- FastMCP server initialization
- Two tools: `generate_video_with_image()` and `list_video_models()`
- Complete error handling
- Comprehensive logging
- Vertex AI API integration

### tool_callbacks.py (160 lines)
**Token Optimization** - Shows how to handle large binary data efficiently.
- before_tool_callback: Load artifact, convert to base64
- after_tool_callback: Save base64 as artifact, return reference
- Artifact lifecycle management

### mcp_tools.py (50 lines)
**Configuration** - Sets up the connection between agent and server.
- STDIO connection (development)
- HTTP connection (production)

### agent_config.py (60 lines)
**Agent Setup** - Configures the ADK agent with MCP tools.
- Agent initialization
- Tool registration
- Callback integration
- System prompt

### example_usage.py (120 lines)
**Usage Examples** - Shows how to use the video agent.
- Single video generation
- Batch processing example
- Error handling

---

## Success Checklist

- [ ] Copied `.env.example` to `.env`
- [ ] Set `GOOGLE_CLOUD_PROJECT` in `.env`
- [ ] Set `GOOGLE_CLOUD_LOCATION` in `.env`
- [ ] Installed dependencies with `pip install`
- [ ] Started server with `python veo_server.py`
- [ ] Saw "MCP server started" message
- [ ] Read `README.md` for overview
- [ ] Studied `veo_server.py` for implementation
- [ ] Understood artifact pattern in `tool_callbacks.py`
- [ ] Ready to customize for your use case!

---

## Need Help?

1. **Understanding MCP?** → Read `GUIDE.md` → What is an MCP Server
2. **Implementation details?** → Read `veo_server.py` docstrings
3. **Artifact handling?** → Read `tool_callbacks.py` docstrings
4. **Deployment?** → Read `GUIDE.md` → Deployment Options
5. **Errors?** → Read `README.md` → Troubleshooting
6. **Design patterns?** → Read `GUIDE.md` → Implementation Patterns

---

## Next: Customize for Your Project

Once you understand how it works:

1. **Identify your use case** - What tools do you need?
2. **Design your tools** - What parameters? What outputs?
3. **Copy the structure** - Use the patterns from veo_server.py
4. **Implement your tools** - Write the actual logic
5. **Update callbacks** - Modify if handling different data
6. **Test thoroughly** - Write unit tests
7. **Deploy** - Follow deployment options

---

**Ready to start?** Open `README.md` → Quick Start section

**Time to next step**: ~5 minutes to get server running  
**Time to understand**: ~1 hour to understand all patterns  
**Time to customize**: ~2 hours for your first custom tool  

Let's go! 🚀
