"""Agent execution utilities for Gemini Powerpoint Sage."""

import logging
from typing import List, Optional

from PIL import Image
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.adk.agents import LlmAgent

from .image_utils import create_image_part

logger = logging.getLogger(__name__)


def _get_session_id(session) -> str:
    """
    Safely extract session ID from a session object.
    
    Different SDK versions may have different attribute names.
    
    Args:
        session: Session object
        
    Returns:
        Session ID string
    """
    try:
        if hasattr(session, "session_id"):
            return session.session_id
        elif hasattr(session, "id"):
            return session.id
    except Exception:
        pass
    
    return "session_system_user"


async def run_stateless_agent(
    agent: LlmAgent,
    prompt: str,
    images: Optional[List[Image.Image]] = None,
) -> str:
    """
    Run a stateless single-turn agent and return text output.
    
    Creates a new session for each invocation to ensure no state is preserved.
    
    Args:
        agent: The LLM agent to run
        prompt: Text prompt for the agent
        images: Optional list of PIL Images to include
        
    Returns:
        Agent's text response
    """
    runner = InMemoryRunner(agent=agent, app_name=agent.name)
    user_id = "system_user"
    
    # Build content parts
    parts = [types.Part.from_text(text=prompt)]
    if images:
        for img in images:
            try:
                parts.append(create_image_part(img))
            except Exception as e:
                logger.error(f"Failed to attach image part: {e}")

    content = types.Content(role='user', parts=parts)
    
    # Create new session for statelessness
    session = await runner.session_service.create_session(
        app_name=agent.name,
        user_id=user_id,
    )
    
    resolved_session_id = _get_session_id(session)

    # Log execution
    print(f"\n┌── [Agent: {agent.name}]")
    truncated_prompt = prompt.strip()[:500].replace('\n', ' ')
    if len(prompt) > 500:
        truncated_prompt += '...'
    print(f"│ Task: {truncated_prompt}")
    
    if images:
        print(f"│ [{len(images)} Images Attached]")

    response_text = ""
    
    try:
        # Run agent
        for event in runner.run(
            user_id=user_id,
            session_id=resolved_session_id,
            new_message=content,
        ):
            if getattr(event, "content", None) and event.content.parts:
                for part in event.content.parts:
                    # Only extract text parts
                    txt = getattr(part, "text", "") or ""
                    response_text += txt
    except Exception as e:
        logger.error(f"Error running agent {agent.name}: {e}")
        return f"Error: {e}"
    
    if not response_text.strip():
        logger.warning(f"Agent {agent.name} returned empty text.")
    
    # Log response
    truncated_response = response_text.strip()[:500].replace('\n', ' ')
    if len(response_text) > 500:
        truncated_response += '...'
    print(f"└-> Response: {truncated_response}")
    
    return response_text.strip()


async def run_visual_agent(
    agent: LlmAgent,
    prompt: str,
    images: Optional[List[Image.Image]] = None,
) -> Optional[bytes]:
    """
    Run a stateless agent and capture generated image output.
    
    Args:
        agent: The LLM agent to run (must support image generation)
        prompt: Text prompt for the agent
        images: Optional list of PIL Images to include as input
        
    Returns:
        Generated image as bytes, or None if no image was generated
    """
    runner = InMemoryRunner(agent=agent, app_name=agent.name)
    user_id = "system_user"
    
    # Build content parts
    parts = [types.Part.from_text(text=prompt)]
    if images:
        for img in images:
            try:
                parts.append(create_image_part(img))
            except Exception as e:
                logger.error(f"Failed to attach image part: {e}")

    content = types.Content(role='user', parts=parts)
    
    # Create new session
    session = await runner.session_service.create_session(
        app_name=agent.name,
        user_id=user_id,
    )
    
    resolved_session_id = _get_session_id(session)

    # Log execution
    print(f"\n┌── [Agent: {agent.name} (Visual)]")
    truncated_prompt = prompt.strip()[:500].replace('\n', ' ')
    if len(prompt) > 500:
        truncated_prompt += '...'
    print(f"│ Task: {truncated_prompt}")

    generated_image_bytes = None

    try:
        for event in runner.run(
            user_id=user_id,
            session_id=resolved_session_id,
            new_message=content,
        ):
            if getattr(event, "content", None) and event.content.parts:
                for part in event.content.parts:
                    # Check for inline_data or file_data
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data:
                        generated_image_bytes = inline_data.data
                        print("│ [Received Image Data]")
    except Exception as e:
        logger.error(f"Error running visual agent {agent.name}: {e}")
        return None

    # Log result
    if generated_image_bytes:
        print(f"└-> Response: [Image Generated ({len(generated_image_bytes)} bytes)]")
    else:
        print(f"└-> Response: [No Image Generated]")
        
    return generated_image_bytes
