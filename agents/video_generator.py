"""Video Planning Agent.

This module exposes an LLM-based planner that selects a few high-value
presentation moments for downstream video treatment. It never calls Veo or
any other video generation service.
"""

import os
try:
    raise ImportError("Video planner agent uses LLM fallback only")
except Exception:
    from google.adk.agents import LlmAgent
    from . import prompt

    video_generator_agent = LlmAgent(
        name="video_generator",
        model=os.getenv("MODEL_VIDEO_GENERATOR", "gemini-2.5-flash"),
        description="Plans which presentation moments deserve video treatment.",
        instruction=prompt.VIDEO_GENERATOR_PROMPT,
    )
