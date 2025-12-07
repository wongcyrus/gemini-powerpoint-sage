"""Agent tool factory for Gemini Powerpoint Sage."""

import logging
from typing import Callable, Optional

from PIL import Image
from google.adk.agents import LlmAgent

from config.constants import LanguageConfig
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
        translator_agent: Optional[LlmAgent] = None,
        image_translator_agent: Optional[LlmAgent] = None,
    ):
        """
        Initialize the tool factory.

        Args:
            analyst_agent: Agent for analyzing slides
            writer_agent: Agent for writing speaker notes
            auditor_agent: Agent for auditing existing notes
            translator_agent: Agent for translating speaker notes
            image_translator_agent: Agent for translating slide visuals
        """
        self.analyst_agent = analyst_agent
        self.writer_agent = writer_agent
        self.auditor_agent = auditor_agent
        self.translator_agent = translator_agent
        self.image_translator_agent = image_translator_agent

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
        language: str = "en",
        english_notes: dict = None,
        speaker_style: str = "Professional",
    ) -> Callable:
        """
        Create the writer tool function.

        Args:
            presentation_theme: Theme of the presentation
            global_context: Global context from overviewer
            language: Language locale code (e.g., en, zh-CN, yue-HK)
            english_notes: Dict of English notes for translation mode
            speaker_style: Speaking style/tone for speaker notes

        Returns:
            Async function that writes speaker notes
        """

        
        async def speech_writer(
            analysis: str,
            previous_context: str,
            theme: str = presentation_theme,
            global_ctx: str = global_context,
            slide_idx: int = None,
        ) -> str:
            """Tool: Writes the speaker note script."""
            logger.info("[Tool] speech_writer invoked.")

            # Translation mode: use English notes as source
            if language != "en" and english_notes and slide_idx:
                en_note = english_notes.get(slide_idx)
                if en_note:
                    lang_name = LanguageConfig.get_language_name(language)
                    prompt = (
                        f"TRANSLATION TASK:\n"
                        f"Translate the following English speaker notes to {lang_name}.\n"
                        f"Maintain the same tone, style, and level of detail.\n\n"
                        f"ENGLISH NOTES:\n{en_note}\n\n"
                        f"SLIDE CONTEXT:\n{analysis}\n\n"
                        f"IMPORTANT: Provide ONLY the translated speaker notes in {lang_name}. "
                        f"Do not include explanations or metadata."
                    )
                else:
                    # Fallback if no English note found
                    lang_name = LanguageConfig.get_language_name(language)
                    prompt = (
                        f"SLIDE_ANALYSIS:\n{analysis}\n\n"
                        f"PRESENTATION_THEME: {theme}\n"
                        f"PREVIOUS_CONTEXT: {previous_context}\n"
                        f"GLOBAL_CONTEXT: {global_ctx}\n\n"
                        f"IMPORTANT: Write the speaker notes in {lang_name}. "
                        f"All content must be in {lang_name}."
                    )
            else:
                # Original English generation mode
                language_instruction = ""
                if language and language.lower() != "en":
                    lang_name = LanguageConfig.get_language_name(language)
                    language_instruction = (
                        f"\n\nIMPORTANT: Write the speaker notes in {lang_name}. "
                        f"All content must be in {lang_name}."
                    )

                prompt = (
                    f"SLIDE_ANALYSIS:\n{analysis}\n\n"
                    f"PRESENTATION_THEME: {theme}\n"
                    f"PREVIOUS_CONTEXT: {previous_context}\n"
                    f"GLOBAL_CONTEXT: {global_ctx}\n"
                    f"SPEAKER STYLE: {speaker_style}{language_instruction}\n"
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

    def create_translator_tool(
        self,
        target_language: str,
    ) -> Callable:
        """
        Create the translator tool function.

        Args:
            target_language: Target language name (e.g., "Simplified Chinese")

        Returns:
            Async function that translates speaker notes
        """
        if not self.translator_agent:
            raise ValueError("Translator agent not provided")

        async def call_translator(english_notes: str) -> str:
            """Tool: Translates speaker notes to target language."""
            logger.info(
                "[Tool] call_translator invoked for %s", target_language
            )

            if not english_notes or not english_notes.strip():
                return "ERROR: No English notes provided for translation."

            prompt = (
                f"Translate the following speaker notes to {target_language}."
                f" Maintain technical accuracy and educational clarity.\n\n"
                f"English notes:\n{english_notes}"
            )
            return await run_stateless_agent(self.translator_agent, prompt)

        return call_translator

    def create_image_translator_tool(
        self,
        target_language: str,
    ) -> Callable:
        """
        Create the image translator tool function.

        Args:
            target_language: Target language name (e.g., "Simplified Chinese")

        Returns:
            Async function that translates slide visuals
        """
        if not self.image_translator_agent:
            raise ValueError("Image translator agent not provided")

        async def call_image_translator(
            slide_image: Image.Image, english_description: str = ""
        ) -> str:
            """Tool: Translates slide visual text to target language."""
            logger.info(
                "[Tool] call_image_translator invoked for %s",
                target_language
            )

            if not slide_image:
                return "ERROR: No slide image provided for translation."

            context = (
                f"Analyze this slide image and translate all text elements "
                f"to {target_language}. Provide a complete description for "
                f"regenerating the visual in the target language."
            )

            if english_description:
                context += (
                    f"\n\nOriginal English description:\n{english_description}"
                )

            prompt = context + (
                "\n\nProvide:\n"
                "1. List of all text elements with translations\n"
                "2. Complete visual description in target language\n"
                "3. Any cultural adaptations needed\n"
                "4. Design specifications (colors, fonts, layout)"
            )

            return await run_stateless_agent(
                self.image_translator_agent, prompt, slide_image
            )

        return call_image_translator

