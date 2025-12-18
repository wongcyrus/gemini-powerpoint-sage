"""Visual generation service for Gemini Powerpoint Sage.

Primary attempt: Gemini model (designer_agent).
Fallback (if no image bytes OR forced): Imagen API via genai.Client for direct image generation.
Set env var FORCE_FALLBACK_IMAGE_GEN=1 to bypass primary and test fallback directly.
"""

import io
import logging
import os
from typing import Optional

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt

from google.adk.agents import LlmAgent
from google import genai
from google.genai import types

from config.constants import EnvironmentVars, FilePatterns, LanguageConfig
from utils.agent_utils import run_visual_agent

logger = logging.getLogger(__name__)


class VisualGenerator:
    """Service for generating enhanced slide visuals."""

    def __init__(
        self,
        designer_agent: LlmAgent,
        output_dir: str,
        skip_generation: bool = False,
        fallback_imagen_model: str = "imagen-4.0-generate-001",
        style: str = "Professional",
    ):
        """
        Initialize the visual generator.

        Args:
            designer_agent: Agent for generating slide designs
            output_dir: Directory to save generated visuals
            skip_generation: Whether to skip visual generation
            fallback_imagen_model: Imagen model name for fallback generation
            style: Style/theme for visual generation
        """
        self.designer_agent = designer_agent
        self.fallback_imagen_model = fallback_imagen_model
        self.secondary_model = os.getenv("MODEL_DESIGNER_SECONDARY", "gemini-2.5-flash-image")
        self.output_dir = output_dir
        self.skip_generation = skip_generation
        self.visual_style = style  # This is visual_style from config
        self.previous_image: Optional[Image.Image] = None

        # Ensure output directory exists
        if not skip_generation:
            os.makedirs(output_dir, exist_ok=True)

    async def generate_visual(
        self,
        slide_idx: int,
        slide_image: Image.Image,
        speaker_notes: str,
        retry_errors: bool = False,
        language: str = "en",
    ) -> Optional[bytes]:
        """
        Generate an enhanced visual for a slide.

        Args:
            slide_idx: Slide index (1-based)
            slide_image: Original slide image
            speaker_notes: Generated speaker notes
            retry_errors: Whether to regenerate existing images
            language: Target language locale code (e.g., en, zh-CN, yue-HK)

        Returns:
            Image bytes if generated, None otherwise
        """
        if self.skip_generation:
            logger.info(
                f"Skipping visual generation for Slide {slide_idx} "
                "(skip-visuals active)."
            )
            return None

        # Check if visual already exists
        img_filename = FilePatterns.REIMAGINED_SLIDE.format(idx=slide_idx)
        img_path = os.path.join(self.output_dir, img_filename)

        if os.path.exists(img_path) and not retry_errors:
            logger.info(
                f"Visual already exists for Slide {slide_idx} "
                f"({img_filename}). Skipping generation."
            )
            try:
                with open(img_path, "rb") as f:
                    img_bytes = f.read()
                self._update_previous_image(img_bytes)
                return img_bytes
            except Exception as e:
                logger.error(f"Failed to load existing image {img_path}: {e}")
                # Fall through to regenerate

        # Generate new visual with multi-tier fallback
        force_fallback = os.getenv(EnvironmentVars.FORCE_FALLBACK_IMAGE_GEN) == "1"
        logger.info("--- Generating Visual for Slide %d (force_fallback=%s) ---" % (slide_idx, force_fallback))

        img_bytes = None
        logo_instruction = self._get_logo_instruction(slide_idx)
        designer_prompt = self._build_designer_prompt(
            speaker_notes,
            logo_instruction,
            language
        )
        if designer_prompt is None:
            logger.warning("_build_designer_prompt returned None; using minimal fallback prompt.")
            designer_prompt = (
                "Speaker Notes: " + speaker_notes[:400] + "\nTASK: Generate a high-fidelity slide image."
            )

        designer_images = [slide_image]
        if self.previous_image:
            designer_images.append(self.previous_image)

        # Tier 1: Primary designer model (gemini-3-pro-image-preview)
        if not force_fallback:
            img_bytes = await run_visual_agent(
                self.designer_agent,
                designer_prompt,
                images=designer_images
            )
        else:
            logger.info("Force fallback enabled; skipping primary designer model.")

        # Tier 2: Secondary Gemini model (gemini-2.5-flash-image)
        if not img_bytes and not force_fallback:
            logger.info(
                "FALLBACK TIER 2: Trying secondary model (%s) for Slide %d",
                self.secondary_model, slide_idx
            )
            from google.adk.agents import LlmAgent
            secondary_agent = LlmAgent(
                name="slide_designer_secondary",
                model=self.secondary_model,
                description="Secondary slide designer",
                instruction=self.designer_agent.instruction
            )
            try:
                img_bytes = await run_visual_agent(
                    secondary_agent,
                    designer_prompt,
                    images=designer_images
                )
            except Exception as e:
                logger.error("Secondary model failed for Slide %d: %s" % (slide_idx, e))

        # Tier 3: Imagen API directly
        if not img_bytes:
            logger.info(
                "FALLBACK TIER 3: Calling Imagen model for Slide %d", slide_idx
            )
            fallback_prompt = self._build_fallback_prompt(
                speaker_notes, language
            )
            try:
                img_bytes = await self._generate_imagen_directly(fallback_prompt)
            except Exception as e:
                logger.error("Fallback Imagen generation failed for Slide %d: %s" % (slide_idx, e))

        if img_bytes:
            try:
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                logger.info("Saved reimagined slide to: %s" % img_path)
                self._update_previous_image(img_bytes)
            except Exception as e:
                logger.error("Failed to save generated image: %s" % e)
        else:
            logger.warning("No image generated for Slide %d" % slide_idx)
            self.previous_image = None

        return img_bytes

    def replace_slide_with_visual(
        self,
        prs,
        slide,
        img_path: str,
        speaker_notes: str,
        mode: str = "cover",  # "contain" or "cover"
        target_dpi: int = 150   # controls file size if you downscale
    ) -> bool:
        """
        Replace slide content with generated visual and add notes to the notes section.

        Args:
            prs: PowerPoint Presentation object
            slide: Slide object to modify
            img_path: Path to the generated image
            speaker_notes: Notes to add to the notes section
            mode: "contain" (preserve aspect, may letterbox) or "cover" (fill, crop overflow)
            target_dpi: DPI to use when re-saving image to reduce file size

        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove all shapes on the slide
            for shape in list(slide.shapes):
                sp = shape.element
                sp.getparent().remove(sp)

            slide_width = prs.slide_width
            slide_height = prs.slide_height
            
            logger.debug(f"Slide dimensions: {slide_width.inches}\" x {slide_height.inches}\"")

            # Optionally reduce image file size (not dimensions) by re-saving
            # This keeps pixel dimensions but lowers compression quality for smaller .pptx
            reduced_img_path = img_path
            try:
                with Image.open(img_path) as im:
                    img_width_px, img_height_px = im.size
                    
                    # Re-save to JPEG or PNG with optimized settings to reduce size
                    # If original has alpha, keep PNG; otherwise use JPEG for disk-size savings.
                    if im.mode in ("RGBA", "LA") or (im.format == "PNG" and "transparency" in im.info):
                        tmp_path = os.path.splitext(img_path)[0] + "_reduced.png"
                        im.save(tmp_path, format="PNG", optimize=True)
                    else:
                        tmp_path = os.path.splitext(img_path)[0] + "_reduced.jpg"
                        # quality ~85 is a good balance; adjust as needed
                        im = im.convert("RGB")
                        im.save(tmp_path, format="JPEG", quality=85, optimize=True)
                    
                    reduced_img_path = tmp_path
            except Exception as e:
                logger.debug(f"Image re-save optimization skipped: {e}")

            # Compute placement with aspect ratio rules
            try:
                with Image.open(reduced_img_path) as im:
                    img_width_px, img_height_px = im.size
                    left, top, width, height = self._compute_image_placement(
                        img_width_px, img_height_px, slide_width, slide_height, dpi=96, mode=mode
                    )
            except Exception as e:
                logger.debug(f"Placement fallback (full slide) due to error: {e}")
                left, top, width, height = 0, 0, slide_width, slide_height

            logger.info(f"Original image: {img_path}")
            logger.info(f"Reduced image: {reduced_img_path}")

            # Add the picture with final size AT INSERTION TIME to avoid oversized initial shape
            picture = slide.shapes.add_picture(
                reduced_img_path,
                left=left,
                top=top,
                width=width,
                height=height
            )

            logger.debug(f"Picture dimensions set to: {picture.width.inches}\" x {picture.height.inches}\"")
            logger.info(f"Optimized image added with {mode} mode")

            # Clean up the reduced image if it's different from original
            if reduced_img_path != img_path and os.path.exists(reduced_img_path):
                try:
                    os.unlink(reduced_img_path)
                    logger.debug(f"Cleaned up reduced image: {reduced_img_path}")
                except Exception as e:
                    logger.debug(f"Could not clean up reduced image: {e}")

            # Add speaker notes to the notes section as plain text
            if not slide.has_notes_slide:
                slide.notes_slide
            
            text_frame = slide.notes_slide.notes_text_frame
            text_frame.clear()
            
            # Add notes as single paragraph without bullet formatting
            p = text_frame.paragraphs[0]
            p.text = speaker_notes
            p.level = 0
            
            # Explicitly remove bullet formatting
            from pptx.enum.text import PP_ALIGN
            p.alignment = PP_ALIGN.LEFT

            logger.info(f"Replaced slide content with visual using {mode} mode.")
            return True

        except Exception as e:
            logger.error(f"Failed to replace slide with visual: {e}")
            return False





    def add_visual_to_presentation(
        self,
        prs: Presentation,
        slide_idx: int,
        img_path: str,
        speaker_notes: str,
        mode: str = "cover",
        target_dpi: int = 150
    ) -> bool:
        """
        Add a generated visual as a new slide in the presentation.

        Args:
            prs: PowerPoint presentation object
            slide_idx: Original slide index
            img_path: Path to the generated image
            speaker_notes: Speaker notes to add to the slide

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find a blank layout
            try:
                blank_layout = prs.slide_layouts[6]  # Usually blank
            except IndexError:
                logger.warning(
                    "Could not find blank slide layout (index 6), "
                    "using first available."
                )
                blank_layout = prs.slide_layouts[0]

            # Add new slide
            new_slide = prs.slides.add_slide(blank_layout)

            # Get slide dimensions for full coverage
            slide_width = prs.slide_width
            slide_height = prs.slide_height
            
            logger.debug(f"New slide dimensions: {slide_width.inches}\" x {slide_height.inches}\"")

            # Optimize image file size by re-saving with compression
            reduced_img_path = img_path
            try:
                with Image.open(img_path) as im:
                    img_width_px, img_height_px = im.size
                    
                    # Re-save with optimized settings
                    if im.mode in ("RGBA", "LA") or (im.format == "PNG" and "transparency" in im.info):
                        tmp_path = os.path.splitext(img_path)[0] + "_reduced.png"
                        im.save(tmp_path, format="PNG", optimize=True)
                    else:
                        tmp_path = os.path.splitext(img_path)[0] + "_reduced.jpg"
                        im = im.convert("RGB")
                        im.save(tmp_path, format="JPEG", quality=85, optimize=True)
                    
                    reduced_img_path = tmp_path
            except Exception as e:
                logger.debug(f"Image optimization skipped: {e}")

            # Compute placement with aspect ratio rules
            try:
                with Image.open(reduced_img_path) as im:
                    img_width_px, img_height_px = im.size
                    left, top, width, height = self._compute_image_placement(
                        img_width_px, img_height_px, slide_width, slide_height, dpi=96, mode=mode
                    )
            except Exception as e:
                logger.debug(f"Placement fallback (full slide) due to error: {e}")
                left, top, width, height = 0, 0, slide_width, slide_height

            # Add the optimized image with proper placement
            picture = new_slide.shapes.add_picture(
                reduced_img_path,
                left=left,
                top=top,
                width=width,
                height=height
            )
            
            logger.debug(f"Picture dimensions set to: {picture.width.inches}\" x {picture.height.inches}\"")
            logger.info(f"Optimized image added with {mode} mode")
            
            # Clean up the reduced image if it's different from original
            if reduced_img_path != img_path and os.path.exists(reduced_img_path):
                try:
                    os.unlink(reduced_img_path)
                    logger.debug(f"Cleaned up reduced image: {reduced_img_path}")
                except Exception as e:
                    logger.debug(f"Could not clean up reduced image: {e}")

            # Add speaker notes to the notes section instead of as text on slide
            if not new_slide.has_notes_slide:
                new_slide.notes_slide
            
            text_frame = new_slide.notes_slide.notes_text_frame
            text_frame.clear()
            
            # Add notes as single paragraph
            p = text_frame.paragraphs[0]
            p.text = f"Generated Notes for Slide {slide_idx}:\n{speaker_notes}"
            p.level = 0
            
            # Explicitly remove bullet formatting
            from pptx.enum.text import PP_ALIGN
            p.alignment = PP_ALIGN.LEFT

            logger.info(
                f"Added new slide with full-size reimagined image and notes "
                f"for Slide {slide_idx}."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add reimagined slide to PPTX: {e}")
            return False

    def _get_logo_instruction(self, slide_idx: int) -> str:
        """Get logo instruction based on slide position."""
        if slide_idx == 1:
            return (
                "You MUST prominently feature the logo/branding from "
                "IMAGE 1 (Original Draft Slide) in an appropriate corner."
            )
        else:
            return (
                "DO NOT include any logos or branding elements. "
                "Focus solely on content."
            )

    def _build_designer_prompt(
        self,
        speaker_notes: str,
        logo_instruction: str,
        language: str = "en"
    ) -> str:
        """Build the prompt for the primary (Gemini) designer agent."""
        style_ref = (
            "Style Reference (Previous Slide) provided."
            if self.previous_image
            else "N/A"
        )
        
        # Language-specific instructions
        lang_name = LanguageConfig.get_language_name(language)
        
        lang_instruction = ""
        if language != "en":
            lang_instruction = (
                f"\n\nLANGUAGE: ALL text in the generated image MUST be "
                f"in {lang_name}. Do NOT include any English text. "
                f"Translate all titles, labels, and content to "
                f"{lang_name}."
            )
        
        # Note: Visual style is now in the agent's system instruction, not here
        
        return (
            f"IMAGE 1: Original Slide Image provided.\n\n"
            f"IMAGE 2: {style_ref}\n\n"
            f"Speaker Notes: \"{speaker_notes}\"\n\n"
            f"TASK: Generate the high-fidelity slide image now.\n\n"
            f"CONTEXT: {logo_instruction}{lang_instruction}\n"
        )

    def _build_fallback_prompt(
        self,
        speaker_notes: str,
        language: str = "en"
    ) -> str:
        """Prompt for Imagen fallback rendering."""
        # Language-specific instructions
        lang_name = LanguageConfig.get_language_name(language)
        
        lang_instruction = ""
        if language != "en":
            lang_instruction = (
                f" ALL text MUST be in {lang_name}. "
                f"NO English text allowed."
            )
        
        return (
            "Create a professional 16:9 presentation slide. "
            + "Speaker Notes: " + speaker_notes.strip() + "\n"
            + "Instructions: Derive a clear title and bullet points. "
            + "Render a clean slide with whitespace, legible "
            + "typography, subtle modern background, high contrast "
            + "text." + lang_instruction
            + " NO logos, NO invented imagery."
        )

    async def _generate_imagen_directly(self, prompt: str) -> Optional[bytes]:
        """Generate image using Imagen API directly (not via ADK agent).
        
        Args:
            prompt: Text prompt for image generation
            
        Returns:
            Image bytes or None if generation failed
        """
        try:
            client = genai.Client()
            response = client.models.generate_images(
                model=self.fallback_imagen_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    include_rai_reason=True,
                    output_mime_type='image/png',
                    aspect_ratio='16:9',  # Match PowerPoint slide dimensions
                )
            )
            
            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
                logger.info("Imagen generated image: %d bytes" % len(image_bytes))
                return image_bytes
            else:
                logger.warning("Imagen returned no images")
                return None
                
        except Exception as e:
            logger.error("Imagen API call failed: %s" % e)
            return None

    def _update_previous_image(self, img_bytes: bytes) -> None:
        """Update the previous image for style consistency."""
        try:
            self.previous_image = Image.open(io.BytesIO(img_bytes))
        except Exception as e:
            logger.warning(
                f"Could not load generated image for next iteration: {e}"
            )
            self.previous_image = None

    def reset_style_context(self) -> None:
        """Reset the style context (previous image)."""
        self.previous_image = None

    def _compute_image_placement(
        self, 
        img_width_px: int, 
        img_height_px: int, 
        slide_width, 
        slide_height, 
        dpi: int = 96, 
        mode: str = "cover"
    ):
        """
        Compute image placement on slide with proper aspect ratio handling.
        
        Args:
            img_width_px: Image width in pixels
            img_height_px: Image height in pixels
            slide_width: Slide width (Length object)
            slide_height: Slide height (Length object)
            dpi: DPI for pixel to inch conversion
            mode: "contain" (fit within, may letterbox) or "cover" (fill, may crop)
            
        Returns:
            Tuple of (left, top, width, height) as Length objects
        """
        from pptx.util import Inches
        
        # Convert slide dimensions to pixels
        slide_width_px = slide_width.inches * dpi
        slide_height_px = slide_height.inches * dpi
        
        # Calculate aspect ratios
        img_ratio = img_width_px / img_height_px
        slide_ratio = slide_width_px / slide_height_px
        
        if mode == "contain":
            # Fit image within slide bounds (letterbox/pillarbox)
            if img_ratio > slide_ratio:
                # Image is wider - fit to width
                new_width_px = slide_width_px
                new_height_px = slide_width_px / img_ratio
                left_px = 0
                top_px = (slide_height_px - new_height_px) / 2
            else:
                # Image is taller - fit to height
                new_height_px = slide_height_px
                new_width_px = slide_height_px * img_ratio
                left_px = (slide_width_px - new_width_px) / 2
                top_px = 0
        else:  # mode == "cover"
            # Fill slide completely (may crop image)
            if img_ratio > slide_ratio:
                # Image is wider - fit to height, crop width
                new_height_px = slide_height_px
                new_width_px = slide_height_px * img_ratio
                left_px = -(new_width_px - slide_width_px) / 2
                top_px = 0
            else:
                # Image is taller - fit to width, crop height
                new_width_px = slide_width_px
                new_height_px = slide_width_px / img_ratio
                left_px = 0
                top_px = -(new_height_px - slide_height_px) / 2
        
        # Convert back to inches
        left = Inches(left_px / dpi)
        top = Inches(top_px / dpi)
        width = Inches(new_width_px / dpi)
        height = Inches(new_height_px / dpi)
        
        logger.debug(f"Image placement ({mode}): {left.inches:.2f}\", {top.inches:.2f}\", {width.inches:.2f}\", {height.inches:.2f}\"")
        
        return left, top, width, height



    def cleanup_temp_files(self, prs) -> None:
        """Clean up temporary image files created during slide processing."""
        cleaned_count = 0
        for slide in prs.slides:
            if hasattr(slide, '_temp_image_paths'):
                for temp_path in slide._temp_image_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                            cleaned_count += 1
                            logger.debug(f"Cleaned up temporary file: {temp_path}")
                    except Exception as e:
                        logger.warning(f"Could not clean up {temp_path}: {e}")
                # Clear the list
                slide._temp_image_paths = []
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} temporary image files")
