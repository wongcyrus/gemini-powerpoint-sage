"""Agent tool factory for Gemini Powerpoint Sage."""

import logging
from typing import Callable, Optional

from PIL import Image
from google.adk.agents import LlmAgent

from utils.agent_utils import run_stateless_agent
from utils.image_utils import get_image

logger = logging.getLogger(__name__)


class AgentToolFactory:
    """Factory for creating agent tools used by the supervisor."""

    def __init__(
        self,
        analyst_agent: LlmAgent,
        writer_agent: LlmAgent,
        auditor_agent: LlmAgent,
    ):
        """
        Initialize the tool factory.

        Args:
            analyst_agent: Agent for analyzing slides
            writer_agent: Agent for writing speaker notes
            auditor_agent: Agent for auditing existing notes
        """
        self.analyst_agent = analyst_agent
        self.writer_agent = writer_agent
        self.auditor_agent = auditor_agent

        # Track last writer output for fallback
        self._last_writer_output = ""

    def create_analyst_tool(self) -> Callable:
        """
        Create the analyst tool function.

        Returns:
            Async function that analyzes slide images
        """
        async def call_analyst(image_id: str) -> str:
            """Tool: Analyzes the slide image."""
            logger.info(f"[Tool] call_analyst invoked for image_id: {image_id}")

            image = get_image(image_id)
            if not image:
                return "Error: Image not found."

            prompt_text = "Analyze this slide image."
            return await run_stateless_agent(
                self.analyst_agent,
                prompt_text,
                images=[image]
            )

        return call_analyst

    def create_writer_tool(
        self,
        presentation_theme: str,
        global_context: str,
    ) -> Callable:
        """
        Create the writer tool function.

        Args:
            presentation_theme: Theme of the presentation
            global_context: Global context from overviewer

        Returns:
            Async function that writes speaker notes
        """
        async def speech_writer(
            analysis: str,
            previous_context: str,
            theme: str = presentation_theme,
            global_ctx: str = global_context,
        ) -> str:
            """Tool: Writes the speaker note script."""
            logger.info("[Tool] speech_writer invoked.")

            prompt = (
                f"SLIDE_ANALYSIS:\n{analysis}\n\n"
                f"PRESENTATION_THEME: {theme}\n"
                f"PREVIOUS_CONTEXT: {previous_context}\n"
                f"GLOBAL_CONTEXT: {global_ctx}\n"
            )

            result = await run_stateless_agent(self.writer_agent, prompt)

            if not result or not result.strip():
                logger.warning(
                    "[Tool] speech_writer returned empty text. "
                    "Returning fallback."
                )
                return (
                    "Error: The writer agent failed to generate a script. "
                    "Please try again or use a placeholder."
                )

            # Capture successful output for fallback
            self._last_writer_output = result
            return result

        return speech_writer

    def create_auditor_tool(self) -> Callable:
        """
        Create the auditor tool function.

        Returns:
            Async function that audits existing notes
        """
        async def call_auditor(existing_notes: str) -> str:
            """Tool: Audits existing speaker notes."""
            logger.info("[Tool] call_auditor invoked.")

            if not existing_notes or not existing_notes.strip():
                return "USELESS: No existing notes to audit."

            prompt = f"Audit these existing notes:\n{existing_notes}"
            return await run_stateless_agent(self.auditor_agent, prompt)

        return call_auditor

    @property
    def last_writer_output(self) -> str:
        """Get the last successful writer output."""
        return self._last_writer_output

    def reset_writer_output(self) -> None:
        """Reset the last writer output."""
        self._last_writer_output = ""
