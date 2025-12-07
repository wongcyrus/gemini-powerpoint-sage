"""Video Generation Agent.

This module prefers an MCP-backed video agent when the environment is
configured to use the MCP Veo server (`USE_MCP_VIDEO_AGENT=1`). When that
flag is not set or the MCP sample agent cannot be imported, it falls back to
an LLM-based stub that only generates text prompts.
"""

import os
try:
    if os.getenv("USE_MCP_VIDEO_AGENT", "0") == "1":
        # Use the MCP-backed agent from mcp_sample
        # Requires mcp_sample to be on PYTHONPATH and MCP server running
        from mcp_sample.agent_config import (
            video_agent as video_generator_agent,
        )  # type: ignore
    else:
        raise ImportError("MCP agent not requested")
except Exception:
    # Fallback: lightweight LLM agent for text prompts only
    from google.adk.agents import LlmAgent
    from . import prompt

    video_generator_agent = LlmAgent(
        name="video_generator",
        model=os.getenv("MODEL_VIDEO_GENERATOR", "gemini-2.5-flash"),
        description="Generates video prompts from slide speaker notes.",
        instruction=prompt.VIDEO_GENERATOR_PROMPT,
    )

