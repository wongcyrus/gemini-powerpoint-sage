"""Presentation processing service for Gemini Powerpoint Sage."""

import asyncio
import logging
import os
from typing import Optional, Dict, Any

import pymupdf
from PIL import Image
from pptx import Presentation
from google.genai import types
from google.adk.runners import InMemoryRunner
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from config import Config
from utils.agent_utils import run_stateless_agent
from utils.image_utils import register_image, unregister_image
from utils.progress_utils import (
    load_progress,
    save_progress,
    create_slide_key,
    get_progress_file_path,
    should_retry_errors,
)
from tools.agent_tools import AgentToolFactory
from services.visual_generator import VisualGenerator

logger = logging.getLogger(__name__)


class PresentationProcessor:
    """Main service for processing presentations and generating speaker notes."""

    def __init__(
        self,
        config: Config,
        supervisor_agent: LlmAgent,
        analyst_agent: LlmAgent,
        writer_agent: LlmAgent,
        auditor_agent: LlmAgent,
        overviewer_agent: LlmAgent,
        designer_agent: LlmAgent,
        translator_agent: Optional[LlmAgent] = None,
        image_translator_agent: Optional[LlmAgent] = None,
    ):
        """
        Initialize the presentation processor.

        Args:
            config: Configuration object
            supervisor_agent: Supervisor agent for orchestration
            analyst_agent: Agent for slide analysis
            writer_agent: Agent for writing speaker notes
            auditor_agent: Agent for auditing existing notes
            overviewer_agent: Agent for generating global context
            designer_agent: Agent for generating visuals
            translator_agent: Agent for translating speaker notes
            image_translator_agent: Agent for translating slide visuals
        """
        self.config = config
        self.supervisor_agent = supervisor_agent
        self.analyst_agent = analyst_agent
        self.writer_agent = writer_agent
        self.auditor_agent = auditor_agent
        self.overviewer_agent = overviewer_agent
        self.designer_agent = designer_agent
        self.translator_agent = translator_agent
        self.image_translator_agent = image_translator_agent

        # Initialize tool factory
        self.tool_factory = AgentToolFactory(
            analyst_agent=analyst_agent,
            writer_agent=writer_agent,
            auditor_agent=auditor_agent,
            translator_agent=translator_agent,
            image_translator_agent=image_translator_agent,
        )

        # Initialize visual generator
        fallback_model = os.getenv("FALLBACK_IMAGEN_MODEL", "imagen-4.0-generate-001")
        self.visual_generator = VisualGenerator(
            designer_agent=designer_agent,
            output_dir=config.visuals_dir,
            skip_generation=config.skip_visuals,
            fallback_imagen_model=fallback_model,
        )

        # Progress tracking
        self.progress_file = get_progress_file_path(
            config.pptx_path,
            config.language
        )
        self.retry_errors = should_retry_errors()

        logger.info(f"Initialized processor with config: {config}")
        logger.info(f"Progress file: {self.progress_file}")
        logger.info(f"Retry errors: {self.retry_errors}")

    async def process(self) -> tuple[str, str]:
        """
        Process the presentation and generate speaker notes.

        Returns:
            Tuple of (notes_only_path, with_visuals_path)
        """
        logger.info(f"Processing PPTX: {self.config.pptx_path}")
        logger.info(f"Region: {os.environ.get('GOOGLE_CLOUD_LOCATION')}")
        logger.info(f"Language: {self.config.language}")

        # Load files - create two separate presentations
        prs_notes = Presentation(self.config.pptx_path)
        prs_visuals = Presentation(self.config.pptx_path)
        pdf_doc = pymupdf.open(self.config.pdf_path)
        limit = min(len(prs_notes.slides), len(pdf_doc))

        # Load progress
        progress = load_progress(self.progress_file)

        # Load English notes if processing non-English language
        self.english_notes = {}
        if self.config.language != "en":
            from utils.progress_utils import get_progress_file_path
            en_progress_file = get_progress_file_path(
                self.config.pptx_path, "en"
            )
            if os.path.exists(en_progress_file):
                en_progress = load_progress(en_progress_file)
                for slide_data in en_progress.get("slides", {}).values():
                    if slide_data.get("status") == "success":
                        slide_idx = slide_data.get("slide_index")
                        note = slide_data.get("note")
                        if slide_idx and note:
                            self.english_notes[slide_idx] = note
                logger.info(
                    f"Loaded {len(self.english_notes)} English notes "
                    "for translation"
                )
            else:
                logger.warning(
                    f"English notes not found at {en_progress_file}. "
                    "Translation mode will fall back to generation mode."
                )

        # Generate or load global context
        global_context = await self._get_global_context(
            pdf_doc, limit, progress
        )

        # Get presentation theme
        presentation_theme = self.config.get_presentation_theme()

        # Setup supervisor tools
        self._configure_supervisor_tools(
            presentation_theme,
            global_context,
            self.english_notes
        )

        # Initialize supervisor runner
        supervisor_runner = await self._initialize_supervisor()

        # Process slides
        missing_visuals_count = await self._process_slides(
            prs_notes, prs_visuals, pdf_doc, limit, progress,
            supervisor_runner, presentation_theme,
            global_context
        )

        # Save both presentations
        output_path_notes = self.config.output_path
        output_path_visuals = self.config.output_path_with_visuals

        prs_notes.save(output_path_notes)
        logger.info(f"Saved presentation with notes to: {output_path_notes}")

        # Only save visuals presentation if all images were generated
        if missing_visuals_count == 0:

            # Force 16:9 aspect ratio for visuals presentation
            from pptx.util import Inches
            prs_visuals.slide_width = Inches(10)
            prs_visuals.slide_height = Inches(5.625)
            
            prs_visuals.save(output_path_visuals)
            logger.info(f"Saved presentation with visuals to: {output_path_visuals}")
        else:
            logger.warning(
                "Skipping visuals presentation save: %d slide(s) missing images" % missing_visuals_count
            )
            output_path_visuals = None

        return output_path_notes, output_path_visuals

    async def _get_global_context(
        self,
        pdf_doc,
        limit: int,
        progress: Dict[str, Any]
    ) -> str:
        """Generate or retrieve cached global context."""
        # Check if cached
        if (
            "global_context" in progress
            and progress["global_context"]
            and len(progress["global_context"]) > 50
            and not self.retry_errors
        ):
            logger.info("Using cached Global Context from progress file.")
            return progress["global_context"]

        # For non-English, try to translate from English global context
        if self.config.language != "en":
            from utils.progress_utils import get_progress_file_path
            en_progress_file = get_progress_file_path(
                self.config.pptx_path, "en"
            )
            if os.path.exists(en_progress_file):
                en_progress = load_progress(en_progress_file)
                en_global_context = en_progress.get("global_context")
                if en_global_context and len(en_global_context) > 50:
                    logger.info(
                        "--- Pass 1: Translating Global Context from English ---"
                    )
                    
                    locale_map = {
                        "zh-CN": "Simplified Chinese (简体中文)",
                        "zh-TW": "Traditional Chinese (繁體中文)",
                        "yue-HK": "Cantonese (廣東話)",
                        "es": "Spanish (Español)",
                        "fr": "French (Français)",
                        "ja": "Japanese (日本語)",
                        "ko": "Korean (한국어)",
                    }
                    lang_name = locale_map.get(
                        self.config.language,
                        self.config.language
                    )
                    
                    translate_prompt = (
                        f"Translate the following presentation overview "
                        f"to {lang_name}:\n\n{en_global_context}"
                    )
                    
                    global_context = await run_stateless_agent(
                        self.translator_agent,
                        translate_prompt
                    )
                    
                    logger.info(
                        f"Global Context Translated: {len(global_context)} chars"
                    )
                    
                    # Cache it
                    progress["global_context"] = global_context
                    save_progress(self.progress_file, progress)
                    
                    return global_context

        # Generate new context
        logger.info("--- Pass 1: Generating Global Context ---")

        all_images = []
        for i in range(limit):
            pix = pdf_doc[i].get_pixmap(dpi=75)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            all_images.append(img)

        global_context = await run_stateless_agent(
            self.overviewer_agent,
            "Here are the slides for the entire presentation. Analyze them.",
            images=all_images
        )

        logger.info(f"Global Context Generated: {len(global_context)} chars")

        # Cache it
        progress["global_context"] = global_context
        save_progress(self.progress_file, progress)

        return global_context

    def _configure_supervisor_tools(
        self,
        presentation_theme: str,
        global_context: str,
        english_notes: dict = None,
    ) -> None:
        """Configure the supervisor agent's tools."""
        self.supervisor_agent.tools = [
            AgentTool(agent=self.auditor_agent),
            self.tool_factory.create_analyst_tool(),
            self.tool_factory.create_writer_tool(
                presentation_theme,
                global_context,
                self.config.language,
                english_notes
            ),
        ]

    async def _initialize_supervisor(self) -> InMemoryRunner:
        """Initialize and create supervisor session."""
        supervisor_runner = InMemoryRunner(
            agent=self.supervisor_agent,
            app_name="agents"
        )

        user_id = "supervisor_user"
        session_id = "supervisor_session"

        await supervisor_runner.session_service.create_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )

        return supervisor_runner

    async def _process_slides(
        self,
        prs_notes: Presentation,
        prs_visuals: Presentation,
        pdf_doc,
        limit: int,
        progress: Dict[str, Any],
        supervisor_runner: InMemoryRunner,
        presentation_theme: str,
        global_context: str,
    ) -> int:
        """Process all slides in both presentations.
        
        Returns:
            Number of slides with missing visuals
        """
        user_id = "supervisor_user"
        session_id = "supervisor_session"

        # PHASE 1: Generate all speaker notes
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: Generating speaker notes for all slides")
        logger.info("="*60)
        
        slide_data = []  # Store slide data for visual processing
        previous_slide_summary = "Start of presentation."

        for i in range(limit):
            slide_idx = i + 1
            slide_notes = prs_notes.slides[i]
            slide_visuals = prs_visuals.slides[i]
            pdf_page = pdf_doc[i]

            logger.info(f"--- Processing Notes for Slide {slide_idx} ---")

            # Get existing notes (from notes presentation)
            existing_notes = self._get_existing_notes(slide_notes)
            skey = create_slide_key(slide_idx, existing_notes)
            entry = progress["slides"].get(skey)

            # Register slide image
            image_id = f"slide_{slide_idx}"
            slide_image = self._extract_slide_image(pdf_page)
            register_image(image_id, slide_image)

            # Generate or retrieve speaker notes
            final_response, status = await self._process_slide_notes(
                slide_idx, image_id, existing_notes,
                previous_slide_summary, presentation_theme,
                global_context, entry, supervisor_runner,
                user_id, session_id
            )

            # Update slide notes in both presentations
            if status == "success":
                # Update notes in notes-only presentation
                self._update_slide_notes(slide_notes, final_response)
                
                # Update notes in visuals presentation
                self._update_slide_notes(slide_visuals, final_response)
                
                previous_slide_summary = final_response[:200]

            # Update progress
            progress["slides"][skey] = {
                "slide_index": slide_idx,
                "existing_notes_hash": skey.split("_")[-1],
                "original_notes": existing_notes,
                "note": final_response,
                "status": status,
            }
            save_progress(self.progress_file, progress)

            # Store data for visual generation phase
            slide_data.append({
                "slide_idx": slide_idx,
                "slide_visuals": slide_visuals,
                "slide_image": slide_image,
                "speaker_notes": final_response,
                "status": status,
            })

            # Cleanup
            unregister_image(image_id)

        # PHASE 2: Generate all visuals
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: Generating visuals for all slides")
        logger.info("="*60)
        
        # For non-English languages, check if we can translate English visuals
        english_visuals_dir = None
        translate_visuals = False
        if self.config.language != "en" and self.image_translator_agent:
            pptx_dir = os.path.dirname(self.config.pptx_path)
            pptx_base = os.path.splitext(
                os.path.basename(self.config.pptx_path)
            )[0]
            english_visuals_dir = os.path.join(
                pptx_dir, f"{pptx_base}_en_visuals"
            )
            if os.path.exists(english_visuals_dir):
                logger.info(
                    f"Found English visuals directory: {english_visuals_dir}"
                )
                logger.info(
                    "Will translate visuals from English using "
                    "Image Translator Agent"
                )
                translate_visuals = True
            else:
                logger.info(
                    "No English visuals found, will generate new visuals"
                )
        
        missing_visuals_count = 0
        for slide_info in slide_data:
            slide_idx = slide_info["slide_idx"]
            slide_visuals = slide_info["slide_visuals"]
            slide_image = slide_info["slide_image"]
            speaker_notes = slide_info["speaker_notes"]
            status = slide_info["status"]

            if status == "success":
                # For non-English, translate from English visuals if available
                translated = False
                if translate_visuals and english_visuals_dir:
                    en_img_path = os.path.join(
                        english_visuals_dir,
                        f"slide_{slide_idx}_reimagined.png"
                    )
                    target_img_path = os.path.join(
                        self.config.visuals_dir,
                        f"slide_{slide_idx}_reimagined.png"
                    )
                    
                    # Check if translated visual already exists
                    if os.path.exists(target_img_path):
                        logger.info(
                            f"Visual already translated for Slide {slide_idx}. "
                            "Skipping translation."
                        )
                        # Replace slide with existing translated visual
                        self.visual_generator.replace_slide_with_visual(
                            prs_visuals, slide_visuals,
                            target_img_path, speaker_notes
                        )
                        translated = True
                    elif os.path.exists(en_img_path):
                        # Load English visual and regenerate with translated notes
                        from PIL import Image as PILImage
                        english_visual = PILImage.open(en_img_path)
                        
                        logger.info(
                            f"Translating visual for slide {slide_idx} using "
                            f"English visual as reference"
                        )
                        
                        # Use designer to regenerate with translated notes
                        # and English visual as reference
                        from utils.agent_utils import run_visual_agent
                        
                        locale_map = {
                            "zh-CN": "Simplified Chinese (简体中文)",
                            "zh-TW": "Traditional Chinese (繁體中文)",
                            "yue-HK": "Cantonese (廣東話)",
                            "es": "Spanish (Español)",
                            "fr": "French (Français)",
                            "ja": "Japanese (日本語)",
                            "ko": "Korean (한국어)",
                        }
                        lang_name = locale_map.get(
                            self.config.language,
                            self.config.language
                        )
                        
                        design_prompt = (
                            f"Generate a slide visual in {lang_name} "
                            f"based on the reference image and these speaker "
                            f"notes:\n\n{speaker_notes}\n\n"
                            f"IMPORTANT:\n"
                            f"- Translate all text to {lang_name}\n"
                            f"- Maintain the same layout and design style as "
                            f"the reference\n"
                            f"- Keep colors and branding consistent\n"
                            f"- Make it professional and educational"
                        )
                        
                        img_bytes = await run_visual_agent(
                            self.designer_agent,
                            design_prompt,
                            images=[english_visual]
                        )
                        
                        if img_bytes:
                            # Save translated visual
                            os.makedirs(
                                self.config.visuals_dir, exist_ok=True
                            )
                            
                            with open(target_img_path, "wb") as f:
                                f.write(img_bytes)
                            
                            logger.info(
                                f"Translated visual for Slide {slide_idx}"
                            )
                            
                            # Replace slide with translated visual
                            self.visual_generator.replace_slide_with_visual(
                                prs_visuals, slide_visuals,
                                target_img_path, speaker_notes
                            )
                            translated = True
                
                if not translated:
                    # Generate visual and replace slide in visuals
                    img_bytes = await self.visual_generator.generate_visual(
                        slide_idx, slide_image, speaker_notes,
                        self.retry_errors
                    )

                    if img_bytes:
                        img_path = os.path.join(
                            self.config.visuals_dir,
                            f"slide_{slide_idx}_reimagined.png"
                        )
                        # Replace the slide content with the visual
                        self.visual_generator.replace_slide_with_visual(
                            prs_visuals, slide_visuals, img_path, speaker_notes
                        )
                    else:
                        logger.warning(
                            "No image generated for Slide %d; visuals "
                            "presentation will be skipped" % slide_idx
                        )
                        missing_visuals_count += 1
            else:
                logger.warning(
                    f"Skipping visual generation for Slide {slide_idx} "
                    f"due to notes generation failure"
                )
                missing_visuals_count += 1
        
        return missing_visuals_count

    def _get_existing_notes(self, slide) -> str:
        """Extract existing notes from a slide."""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            return slide.notes_slide.notes_text_frame.text.strip()
        return ""

    def _extract_slide_image(self, pdf_page) -> Image.Image:
        """Extract image from PDF page."""
        pix = pdf_page.get_pixmap(dpi=150)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    async def _process_slide_notes(
        self,
        slide_idx: int,
        image_id: str,
        existing_notes: str,
        previous_slide_summary: str,
        presentation_theme: str,
        global_context: str,
        entry: Optional[Dict[str, Any]],
        supervisor_runner: InMemoryRunner,
        user_id: str,
        session_id: str,
    ) -> tuple[str, str]:
        """
        Process notes for a single slide.

        Returns:
            Tuple of (final_response, status)
        """
        # TRANSLATION MODE: If non-English and English notes exist
        # translate directly (BEFORE checking if already done)
        if (
            self.config.language != "en"
            and self.translator_agent
            and hasattr(self, 'english_notes')
            and self.english_notes
            and slide_idx in self.english_notes
        ):
            # Check if already translated
            if (
                entry
                and entry.get("status") == "success"
                and not self.retry_errors
            ):
                existing_note = entry.get("note", "")
                # Verify it's actually translated (not English)
                # Simple check: if it matches English note, retranslate
                if existing_note != self.english_notes[slide_idx]:
                    logger.info(
                        f"Skipping translation for slide {slide_idx} "
                        "(already translated)"
                    )
                    return existing_note, "success"

            logger.info(
                f"Translation mode: Translating slide {slide_idx} "
                f"from English to {self.config.language}"
            )
            english_note = self.english_notes[slide_idx]
            translated_note = await self._translate_notes(
                english_note, slide_idx
            )
            if translated_note:
                return translated_note, "success"
            else:
                logger.warning(
                    f"Translation failed for slide {slide_idx}, "
                    "falling back to generation mode"
                )

        # Check if already done (for non-translation mode)
        if (
            entry
            and entry.get("status") == "success"
            and not self.retry_errors
        ):
            logger.info(f"Skipping generation for slide {slide_idx}")
            return entry.get("note", ""), "success"

        # Build supervisor prompt
        supervisor_prompt = self._build_supervisor_prompt(
            slide_idx, image_id, existing_notes,
            previous_slide_summary, presentation_theme,
            global_context
        )

        content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=supervisor_prompt)]
        )

        # Run supervisor with retry logic
        final_response = ""
        status = "pending"
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                final_response = ""
                for event in supervisor_runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content,
                ):
                    if getattr(event, "content", None) and event.content.parts:
                        for part in event.content.parts:
                            fn_call = getattr(part, "function_call", None)
                            if fn_call:
                                print(
                                    f"\n[Supervisor] 📞 calling tool: "
                                    f"{fn_call.name}"
                                )
                            text = getattr(part, "text", "") or ""
                            final_response += text

                # Check if we got a response
                final_response = final_response.strip()
                if final_response:
                    status = "success"
                    self.tool_factory.reset_writer_output()
                    break

                # Try fallback to last writer output
                last_output = self.tool_factory.last_writer_output
                if last_output:
                    logger.info(
                        f"Supervisor returned empty text, "
                        f"using fallback content ({len(last_output)} chars)."
                    )
                    final_response = last_output
                    status = "success"
                    self.tool_factory.reset_writer_output()
                    break

                # No response and no fallback - retry if attempts remain
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Empty response for Slide {slide_idx}, "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/"
                        f"{max_retries})..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to get response for Slide {slide_idx} "
                        f"after {max_retries} attempts."
                    )
                    status = "error"

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.error(
                        f"Error in supervisor loop (attempt {attempt + 1}/"
                        f"{max_retries}): {e}, retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Error in supervisor loop after {max_retries} "
                        f"attempts: {e}"
                    )
                    status = "error"
                    break

        return final_response, status

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

    def _update_slide_notes(self, slide, notes: str) -> None:
        """Update the notes on a slide as plain text without bullets."""
        try:
            if not slide.has_notes_slide:
                slide.notes_slide
            
            text_frame = slide.notes_slide.notes_text_frame
            text_frame.clear()
            
            # Add notes as single paragraph without bullet formatting
            p = text_frame.paragraphs[0]
            p.text = notes
            p.level = 0
            
            # Explicitly remove bullet formatting
            from pptx.enum.text import PP_ALIGN
            p.alignment = PP_ALIGN.LEFT
            
        except Exception as e:
            logger.error(f"Failed to update slide notes: {e}")

    async def _translate_notes(
        self, english_note: str, slide_idx: int
    ) -> Optional[str]:
        """
        Translate English speaker notes to target language.

        Args:
            english_note: The English speaker note to translate
            slide_idx: The slide index for context

        Returns:
            Translated notes or None if translation fails
        """
        if not self.translator_agent:
            return None

        # Map locale to language name
        locale_map = {
            "en": "English",
            "zh-CN": "Simplified Chinese (简体中文)",
            "zh-TW": "Traditional Chinese (繁體中文)",
            "yue-HK": "Cantonese (廣東話)",
            "es": "Spanish (Español)",
            "fr": "French (Français)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "de": "German (Deutsch)",
            "it": "Italian (Italiano)",
            "pt": "Portuguese (Português)",
            "ru": "Russian (Русский)",
            "ar": "Arabic (العربية)",
            "hi": "Hindi (हिन्दी)",
            "th": "Thai (ไทย)",
            "vi": "Vietnamese (Tiếng Việt)",
        }

        lang_name = locale_map.get(
            self.config.language, self.config.language
        )

        prompt = (
            f"Translate the following English speaker notes to {lang_name}. "
            f"Maintain technical accuracy, educational tone, and clarity. "
            f"Preserve formatting and structure.\n\n"
            f"English notes:\n{english_note}\n\n"
            f"IMPORTANT: Provide ONLY the translated speaker notes "
            f"in {lang_name}. Do not include explanations or metadata."
        )

        try:
            result = await run_stateless_agent(
                self.translator_agent, prompt
            )
            if result and result.strip():
                logger.info(
                    f"Successfully translated slide {slide_idx} "
                    f"to {self.config.language}"
                )
                return result.strip()
        except Exception as e:
            logger.error(
                f"Translation error for slide {slide_idx}: {e}",
                exc_info=True
            )

        return None

    async def _translate_visual(
        self,
        english_visual: Image.Image,
        english_note: str,
        translated_note: str,
        slide_idx: int,
    ) -> Optional[bytes]:
        """
        Translate visual from English to target language.

        Uses Image Translator Agent to analyze English visual and
        Designer Agent to regenerate with translated text.

        Args:
            english_visual: The English slide visual image
            english_note: The English speaker notes for context
            translated_note: The translated speaker notes
            slide_idx: The slide index

        Returns:
            Image bytes of translated visual or None if translation fails
        """
        if not self.image_translator_agent:
            return None

        # Map locale to language name
        locale_map = {
            "en": "English",
            "zh-CN": "Simplified Chinese (简体中文)",
            "zh-TW": "Traditional Chinese (繁體中文)",
            "yue-HK": "Cantonese (廣東話)",
            "es": "Spanish (Español)",
            "fr": "French (Français)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "de": "German (Deutsch)",
            "it": "Italian (Italiano)",
            "pt": "Portuguese (Português)",
            "ru": "Russian (Русский)",
            "ar": "Arabic (العربية)",
            "hi": "Hindi (हिन्दी)",
            "th": "Thai (ไทย)",
            "vi": "Vietnamese (Tiếng Việt)",
        }

        lang_name = locale_map.get(
            self.config.language, self.config.language
        )

        # Step 1: Analyze English visual and get translation specs
        analysis_prompt = (
            f"You are a visual translator. Analyze this slide image and "
            f"provide ONLY the following information:\n\n"
            f"TEXT TRANSLATIONS (list all text in the image):\n"
            f"English: [text] -> {lang_name}: [translation]\n\n"
            f"VISUAL DESCRIPTION:\n"
            f"Describe the slide layout, colors, and design elements.\n\n"
            f"Context:\n"
            f"English notes: {english_note}\n"
            f"Translated notes: {translated_note}\n\n"
            f"IMPORTANT: Be concise. List only the text translations and "
            f"visual description. No explanations or planning."
        )

        try:
            # Get translation specs from image translator
            translation_spec = await run_stateless_agent(
                self.image_translator_agent,
                analysis_prompt,
                [english_visual]  # Pass as list
            )

            if not translation_spec or not translation_spec.strip():
                logger.warning(
                    f"Image translator returned empty result for "
                    f"slide {slide_idx}"
                )
                return None

            # Step 2: Use designer agent to regenerate visual
            # with translated content
            design_prompt = (
                f"Generate a slide visual in {lang_name} based on these "
                f"specifications:\n\n"
                f"{translation_spec}\n\n"
                f"Translated speaker notes:\n{translated_note}\n\n"
                f"IMPORTANT:\n"
                f"- Use the translated text from the specifications\n"
                f"- Maintain the same layout and design style\n"
                f"- Ensure all text is in {lang_name}\n"
                f"- Keep colors and branding consistent\n"
                f"- Make it professional and high-quality"
            )

            from utils.agent_utils import run_visual_agent
            img_bytes = await run_visual_agent(
                self.designer_agent,
                design_prompt,
                images=[english_visual]
            )

            if img_bytes:
                logger.info(
                    f"Successfully translated visual for slide {slide_idx} "
                    f"to {self.config.language}"
                )
                return img_bytes
            else:
                logger.warning(
                    f"Designer failed to generate translated visual for "
                    f"slide {slide_idx}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Visual translation error for slide {slide_idx}: {e}",
                exc_info=True
            )
            return None

