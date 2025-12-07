"""Speaker notes generation service."""

import asyncio
import logging
from typing import Optional

from PIL import Image
from pptx.slide import Slide
from google.adk.runners import InMemoryRunner
from google.genai import types

from config.constants import LanguageConfig
from utils.agent_utils import run_stateless_agent
from utils.error_handling import RetryStrategy, SlideProcessingError
from utils.image_utils import register_image, unregister_image
from tools.agent_tools import AgentToolFactory

logger = logging.getLogger(__name__)


class NotesGenerator:
    """Service for generating speaker notes."""
    
    def __init__(
        self,
        tool_factory: AgentToolFactory,
        supervisor_runner: InMemoryRunner,
        language: str = "en",
        english_notes: Optional[dict[int, str]] = None,
    ):
        """
        Initialize notes generator.
        
        Args:
            tool_factory: Factory for creating agent tools
            supervisor_runner: Supervisor agent runner
            language: Target language locale code
            english_notes: English notes for translation mode
        """
        self.tool_factory = tool_factory
        self.supervisor_runner = supervisor_runner
        self.language = language
        self.english_notes = english_notes or {}
        self.retry_strategy = RetryStrategy()
    
    async def generate_notes(
        self,
        slide_idx: int,
        slide_image: Image.Image,
        existing_notes: str,
        previous_slide_summary: str,
        presentation_theme: str,
        global_context: str,
        user_id: str = "supervisor_user",
        session_id: str = "supervisor_session",
    ) -> tuple[str, str]:
        """
        Generate speaker notes for a slide.
        
        Args:
            slide_idx: Slide index (1-based)
            slide_image: Slide image from PDF
            existing_notes: Existing notes on the slide
            previous_slide_summary: Summary of previous slide
            presentation_theme: Presentation theme
            global_context: Global context from overviewer
            user_id: User ID for session
            session_id: Session ID for supervisor
            
        Returns:
            Tuple of (generated_notes, status)
        """
        # Translation mode: translate from English if available
        if self._should_translate(slide_idx):
            return await self._translate_notes(slide_idx)
        
        # Generation mode: use supervisor workflow
        return await self._generate_with_supervisor(
            slide_idx,
            slide_image,
            existing_notes,
            previous_slide_summary,
            presentation_theme,
            global_context,
            user_id,
            session_id,
        )
    
    def _should_translate(self, slide_idx: int) -> bool:
        """Check if slide should use translation mode."""
        return (
            self.language != "en"
            and slide_idx in self.english_notes
        )
    
    async def _translate_notes(
        self, slide_idx: int
    ) -> tuple[str, str]:
        """
        Translate notes from English.
        
        Args:
            slide_idx: Slide index
            
        Returns:
            Tuple of (translated_notes, status)
        """
        english_note = self.english_notes[slide_idx]
        lang_name = LanguageConfig.get_language_name(self.language)
        
        logger.info(
            f"Translation mode: Translating slide {slide_idx} "
            f"from English to {lang_name}"
        )
        
        # Get translator tool from factory
        translator_tool = self.tool_factory.create_translator_tool(lang_name)
        
        try:
            translated = await translator_tool(english_note)
            if translated and translated.strip():
                return translated.strip(), "success"
            else:
                logger.warning(
                    f"Translation returned empty for slide {slide_idx}"
                )
                return "", "error"
        except Exception as e:
            logger.error(
                f"Translation failed for slide {slide_idx}: {e}",
                exc_info=True
            )
            return "", "error"
    
    async def _generate_with_supervisor(
        self,
        slide_idx: int,
        slide_image: Image.Image,
        existing_notes: str,
        previous_slide_summary: str,
        presentation_theme: str,
        global_context: str,
        user_id: str,
        session_id: str,
    ) -> tuple[str, str]:
        """
        Generate notes using supervisor workflow.
        
        Args:
            slide_idx: Slide index
            slide_image: Slide image
            existing_notes: Existing notes
            previous_slide_summary: Previous slide summary
            presentation_theme: Presentation theme
            global_context: Global context
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Tuple of (generated_notes, status)
        """
        # Register slide image
        image_id = f"slide_{slide_idx}"
        register_image(image_id, slide_image)
        
        try:
            # Build supervisor prompt
            prompt = self._build_supervisor_prompt(
                slide_idx,
                image_id,
                existing_notes,
                previous_slide_summary,
                presentation_theme,
                global_context,
            )
            
            content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=prompt)]
            )
            
            # Execute with retry
            result = await self.retry_strategy.execute(
                self._run_supervisor,
                slide_idx,
                content,
                user_id,
                session_id,
            )
            
            if result:
                final_response, status = result
                return final_response, status
            else:
                return "", "error"
                
        finally:
            unregister_image(image_id)
    
    async def _run_supervisor(
        self,
        slide_idx: int,
        content: types.Content,
        user_id: str,
        session_id: str,
    ) -> tuple[str, str]:
        """
        Run supervisor agent for a single attempt.
        
        Args:
            slide_idx: Slide index
            content: Message content
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Tuple of (response_text, status)
        """
        final_response = ""
        
        for event in self.supervisor_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if getattr(event, "content", None) and event.content.parts:
                for part in event.content.parts:
                    # Log function calls
                    fn_call = getattr(part, "function_call", None)
                    if fn_call:
                        print(
                            f"\n[Supervisor] 📞 calling tool: {fn_call.name}"
                        )
                    
                    # Collect text
                    text = getattr(part, "text", "") or ""
                    final_response += text
        
        # Check if we got a response
        final_response = final_response.strip()
        if final_response:
            self.tool_factory.reset_writer_output()
            return final_response, "success"
        
        # Try fallback to last writer output
        last_output = self.tool_factory.last_writer_output
        if last_output:
            logger.info(
                f"Supervisor returned empty text, "
                f"using fallback content ({len(last_output)} chars)."
            )
            self.tool_factory.reset_writer_output()
            return last_output, "success"
        
        # No response - raise error for retry
        raise SlideProcessingError(
            slide_idx,
            "Supervisor returned empty response"
        )
    
    def _build_supervisor_prompt(
        self,
        slide_idx: int,
        image_id: str,
        existing_notes: str,
        previous_slide_summary: str,
        presentation_theme: str,
        global_context: str,
    ) -> str:
        """Build the prompt for the supervisor agent."""
        return (
            f"Here is Slide {slide_idx}.\n"
            f"Existing Notes: \"{existing_notes}\"\n"
            f"Image ID: \"{image_id}\"\n"
            f"Previous Slide Summary: \"{previous_slide_summary}\"\n"
            f"Theme: \"{presentation_theme}\"\n"
            f"Global Context: \"{global_context}\"\n\n"
            f"Please proceed with the workflow."
        )
