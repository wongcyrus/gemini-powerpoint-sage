"""
Agent Factory - Single Source of Truth for Agent Creation.

This module is the ONLY place where agents should be created.
All agents are created with prompt rewriting for style integration.
"""

import os
import logging
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from .prompts import (
    SUPERVISOR_PROMPT,
    ANALYST_PROMPT,
    WRITER_PROMPT,
    AUDITOR_PROMPT,
    OVERVIEWER_PROMPT,
    DESIGNER_PROMPT,
    TRANSLATOR_PROMPT,
    IMAGE_TRANSLATOR_PROMPT,
    VIDEO_GENERATOR_PROMPT,
    TITLE_GENERATOR_PROMPT,
    REFINER_PROMPT,
)
from services.prompt_rewriter import PromptRewriter

logger = logging.getLogger(__name__)


def create_designer_agent(visual_style: str = "Professional") -> LlmAgent:
    """
    Create designer agent with rewritten prompt including visual style.
    
    Args:
        visual_style: Visual style description
        
    Returns:
        Designer agent with rewritten instruction
    """
    rewriter = PromptRewriter(visual_style=visual_style)
    instruction = rewriter.rewrite_designer_prompt(DESIGNER_PROMPT)
    
    return LlmAgent(
        name="slide_designer",
        model=os.getenv("MODEL_DESIGNER", "gemini-3-pro-image-preview"),
        description="Generates high-fidelity slide images with custom visual style.",
        instruction=instruction
    )


def create_writer_agent(speaker_style: str = "Professional") -> LlmAgent:
    """
    Create writer agent with rewritten prompt including speaker style.
    
    Args:
        speaker_style: Speaking style description
        
    Returns:
        Writer agent with rewritten instruction
    """
    rewriter = PromptRewriter(speaker_style=speaker_style)
    instruction = rewriter.rewrite_writer_prompt(WRITER_PROMPT)
    
    return LlmAgent(
        name="speech_writer",
        model=os.getenv("MODEL_WRITER", "gemini-2.5-flash"),
        description="Generates presentation scripts with custom speaking style.",
        instruction=instruction,
        tools=[google_search]
    )


def create_title_generator_agent(speaker_style: str = "Professional") -> LlmAgent:
    """
    Create title generator agent with rewritten prompt including speaker style.
    
    Args:
        speaker_style: Speaking style description
        
    Returns:
        Title generator agent with rewritten instruction
    """
    rewriter = PromptRewriter(speaker_style=speaker_style)
    instruction = rewriter.rewrite_title_generator_prompt(TITLE_GENERATOR_PROMPT)
    
    return LlmAgent(
        name="title_generator",
        model=os.getenv("MODEL_TITLE_GENERATOR", "gemini-2.5-flash"),
        description="Generates short, catchy titles with custom speaking style.",
        instruction=instruction
    )


def create_translator_agent(speaker_style: str = "Professional") -> LlmAgent:
    """
    Create translator agent with rewritten prompt including speaker style.
    
    Args:
        speaker_style: Speaking style description
        
    Returns:
        Translator agent with rewritten instruction for style-aware translation
    """
    rewriter = PromptRewriter(speaker_style=speaker_style)
    instruction = rewriter.rewrite_translator_prompt(TRANSLATOR_PROMPT)
    
    return LlmAgent(
        name="translator_styled",
        model=os.getenv("MODEL_TRANSLATOR", "gemini-2.5-flash"),
        description="Translates speaker notes with custom speaker style application.",
        instruction=instruction
    )


def create_all_agents(visual_style: str = "Professional", speaker_style: str = "Professional") -> dict:
    """
    Create all agents with custom styles using prompt rewriter.
    
    Args:
        visual_style: Visual style for designer
        speaker_style: Speaking style for writer and title generator
        
    Returns:
        Dictionary of all agents
    """
    from .analyst import analyst_agent
    from .auditor import auditor_agent
    from .overviewer import overviewer_agent
    from .translator import translator_agent
    from .image_translator import image_translator_agent
    from .video_generator import video_generator_agent
    from .refiner import refiner_agent
    from .prompt_rewriter import prompt_rewriter_agent
    
    # Log the rewrite process
    logger.info("\n" + "╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 20 + "CREATING AGENTS WITH PROMPT REWRITER" + " " * 21 + "║")
    logger.info("╚" + "═" * 78 + "╝\n")
    
    rewriter = PromptRewriter(visual_style=visual_style, speaker_style=speaker_style)
    rewriter.log_rewrite_summary()
    
    # Create styled agents with rewritten prompts
    designer = create_designer_agent(visual_style)
    writer = create_writer_agent(speaker_style)
    title_generator = create_title_generator_agent(speaker_style)
    translator = create_translator_agent(speaker_style)
    
    # Create supervisor (tools will be configured dynamically by PresentationProcessor)
    supervisor = LlmAgent(
        name="supervisor",
        model=os.getenv("MODEL_SUPERVISOR", "gemini-2.5-flash"),
        description="The orchestrator that manages the slide generation workflow.",
        instruction=SUPERVISOR_PROMPT,
        tools=[]  # Tools configured dynamically with language enforcement
    )
    
    logger.info("✓ All agents created successfully with rewritten prompts\n")
    
    return {
        "supervisor": supervisor,
        "analyst": analyst_agent,
        "writer": writer,
        "auditor": auditor_agent,
        "overviewer": overviewer_agent,
        "designer": designer,
        "translator": translator,
        "image_translator": image_translator_agent,
        "video_generator": video_generator_agent,
        "refiner": refiner_agent,
        "title_generator": title_generator,
        "prompt_rewriter": prompt_rewriter_agent,
    }
