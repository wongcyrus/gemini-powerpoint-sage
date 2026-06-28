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
from pptx.util import Inches

from google.adk.agents import LlmAgent
from google import genai
from google.genai import types
from utils.project_rotation import rotate_project

from config.constants import EnvironmentVars, FilePatterns
from utils.agent_utils import run_visual_agent
from services.visual_generator_helpers import (
    cleanup_reduced_image_file,
    apply_slide_notes,
    build_designer_prompt,
    build_fallback_prompt,
    compute_image_placement_inches,
    get_logo_instruction,
    optimize_image_file,
)

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

        img_filename = FilePatterns.REIMAGINED_SLIDE.format(idx=slide_idx)
        img_path = os.path.join(self.output_dir, img_filename)
        img_bytes = self._load_existing_visual_bytes(img_path, slide_idx, img_filename, retry_errors)
        if img_bytes is None:
            img_bytes = await self._generate_visual_candidate(
                slide_idx,
                slide_image,
                speaker_notes,
                language,
            )

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

    def _load_existing_visual_bytes(
        self,
        img_path: str,
        slide_idx: int,
        img_filename: str,
        retry_errors: bool,
    ) -> Optional[bytes]:
        """Load an existing generated image when reuse is allowed."""
        if not os.path.exists(img_path) or retry_errors:
            return None

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
            return None

    async def _generate_visual_candidate(
        self,
        slide_idx: int,
        slide_image: Image.Image,
        speaker_notes: str,
        language: str,
    ) -> Optional[bytes]:
        """Generate a new visual using the primary, secondary, and Imagen tiers."""
        force_fallback = os.getenv(EnvironmentVars.FORCE_FALLBACK_IMAGE_GEN) == "1"

        current_project = rotate_project()
        if current_project:
            logger.info(
                "--- Generating Visual for Slide %d (Project: %s, force_fallback=%s) ---"
                % (slide_idx, current_project, force_fallback)
            )
        else:
            logger.info(
                "--- Generating Visual for Slide %d (force_fallback=%s) ---"
                % (slide_idx, force_fallback)
            )

        logo_instruction = self._get_logo_instruction(slide_idx)
        designer_prompt = self._build_designer_prompt(
            speaker_notes,
            logo_instruction,
            language,
        )
        if designer_prompt is None:
            logger.warning("_build_designer_prompt returned None; using minimal fallback prompt.")
            designer_prompt = (
                "Speaker Notes: " + speaker_notes[:400] + "\nTASK: Generate a high-fidelity slide image."
            )

        designer_images = [slide_image]
        if self.previous_image:
            designer_images.append(self.previous_image)

        img_bytes = None
        if not force_fallback:
            img_bytes = await run_visual_agent(
                self.designer_agent,
                designer_prompt,
                images=designer_images,
            )
        else:
            logger.info("Force fallback enabled; skipping primary designer model.")

        if not img_bytes and not force_fallback:
            logger.info(
                "FALLBACK TIER 2: Trying secondary model (%s) for Slide %d",
                self.secondary_model,
                slide_idx,
            )
            from google.adk.agents import LlmAgent

            secondary_agent = LlmAgent(
                name="slide_designer_secondary",
                model=self.secondary_model,
                description="Secondary slide designer",
                instruction=self.designer_agent.instruction,
            )
            try:
                img_bytes = await run_visual_agent(
                    secondary_agent,
                    designer_prompt,
                    images=designer_images,
                )
            except Exception as e:
                logger.error("Secondary model failed for Slide %d: %s" % (slide_idx, e))

        if not img_bytes:
            logger.info(
                "FALLBACK TIER 3: Calling Imagen model for Slide %d", slide_idx
            )
            fallback_prompt = self._build_fallback_prompt(speaker_notes, language)
            try:
                img_bytes = await self._generate_imagen_directly(fallback_prompt)
            except Exception as e:
                logger.error(
                    "Fallback Imagen generation failed for Slide %d: %s" % (slide_idx, e)
                )

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
            reduced_img_path = optimize_image_file(img_path)

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
            try:
                cleanup_reduced_image_file(img_path, reduced_img_path)
                if reduced_img_path != img_path:
                    logger.debug(f"Cleaned up reduced image: {reduced_img_path}")
            except Exception as e:
                logger.debug(f"Could not clean up reduced image: {e}")

            # Add speaker notes to the notes section as plain text
            apply_slide_notes(slide, speaker_notes)

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
            reduced_img_path = optimize_image_file(img_path)

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
            try:
                cleanup_reduced_image_file(img_path, reduced_img_path)
                if reduced_img_path != img_path:
                    logger.debug(f"Cleaned up reduced image: {reduced_img_path}")
            except Exception as e:
                logger.debug(f"Could not clean up reduced image: {e}")

            # Add speaker notes to the notes section instead of as text on slide
            apply_slide_notes(
                new_slide,
                f"Generated Notes for Slide {slide_idx}:\n{speaker_notes}",
            )

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
        return get_logo_instruction(slide_idx)

    def _build_designer_prompt(
        self,
        speaker_notes: str,
        logo_instruction: str,
        language: str = "en"
    ) -> str:
        """Build the prompt for the primary (Gemini) designer agent."""
        return build_designer_prompt(
            speaker_notes,
            logo_instruction,
            language,
            previous_image_present=self.previous_image is not None,
        )

    def _build_fallback_prompt(
        self,
        speaker_notes: str,
        language: str = "en"
    ) -> str:
        """Prompt for Imagen fallback rendering."""
        return build_fallback_prompt(speaker_notes, language)

    async def _generate_imagen_directly(self, prompt: str) -> Optional[bytes]:
        """Generate image using Imagen API directly (not via ADK agent).
        
        Args:
            prompt: Text prompt for image generation
            
        Returns:
            Image bytes or None if generation failed
        """
        try:
            # Rotate project before Imagen API call
            current_project = rotate_project()
            if current_project:
                logger.debug(f"Using Imagen API with project: {current_project}")
            
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

        left_in, top_in, width_in, height_in = compute_image_placement_inches(
            img_width_px,
            img_height_px,
            slide_width.inches,
            slide_height.inches,
            dpi=dpi,
            mode=mode,
        )
        left = Inches(left_in)
        top = Inches(top_in)
        width = Inches(width_in)
        height = Inches(height_in)
        logger.debug(
            f"Image placement ({mode}): {left.inches:.2f}\", {top.inches:.2f}\", {width.inches:.2f}\", {height.inches:.2f}\""
        )
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
