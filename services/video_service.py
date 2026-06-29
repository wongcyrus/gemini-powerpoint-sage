"""Video generation service."""

import asyncio
import io
import json
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import pymupdf
from PIL import Image
from google.adk.agents import LlmAgent
from google import genai
from google.genai import types

from config.constants import FilePatterns, ModelConfig
from utils.agent_utils import run_stateless_agent
from utils.error_handling import VideoGenerationError
from services.video_service_helpers import (
    build_fallback_video_plan,
    build_video_agent_prompt,
    build_video_prompt,
    build_video_planner_prompt,
    build_veo_video_prompt,
    extract_artifact_id,
    format_video_prompt_file,
    parse_video_plan_response,
)

logger = logging.getLogger(__name__)


class VideoService:
    """Service for generating video prompts, plans, and Veo clips."""
    
    def __init__(
        self,
        video_generator_agent: Optional[LlmAgent] = None,
        videos_dir: Optional[str] = None,
    ):
        """
        Initialize video service.
        
        Args:
            video_generator_agent: Agent for generating videos
            videos_dir: Directory to save video outputs
        """
        self.video_generator_agent = video_generator_agent
        self.videos_dir = videos_dir
        
        if videos_dir:
            os.makedirs(videos_dir, exist_ok=True)
    
    async def generate_video_prompt(
        self,
        slide_idx: int,
        speaker_notes: str,
        slide_image: Optional[Image.Image] = None,
    ) -> str:
        """
        Generate a video prompt for a slide.
        
        Args:
            slide_idx: Slide index
            speaker_notes: Speaker notes for the slide
            slide_image: Optional slide image for context
            
        Returns:
            Video prompt text
        """
        return build_video_prompt(speaker_notes)
    
    async def generate_video(
        self,
        slide_idx: int,
        speaker_notes: str,
        slide_image: Optional[Image.Image] = None,
    ) -> Optional[str]:
        """
        Generate a video for a slide using the video agent.
        
        Args:
            slide_idx: Slide index
            speaker_notes: Speaker notes
            slide_image: Optional slide image
            
        Returns:
            Video artifact ID or None if generation failed
        """
        if not self.video_generator_agent:
            logger.warning("Video generator agent not available")
            return None

        try:
            # Generate video prompt
            video_prompt = await self.generate_video_prompt(
                slide_idx, speaker_notes, slide_image
            )
            
            # Call video agent
            agent_prompt = build_video_agent_prompt(video_prompt, speaker_notes)
            
            images = [slide_image] if slide_image else None
            response = await run_stateless_agent(
                self.video_generator_agent,
                agent_prompt,
                images=images
            )
            
            # Extract artifact ID from response
            artifact_id = self._extract_artifact_id(response)
            
            if artifact_id:
                logger.info(
                    f"Generated video artifact for Slide {slide_idx}: "
                    f"{artifact_id}"
                )
                return artifact_id
            else:
                logger.warning(
                    f"No video artifact in response for Slide {slide_idx}"
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Video generation failed for Slide {slide_idx}: {e}",
                exc_info=True
            )
            return None

    async def plan_video_moments(
        self,
        slide_data: List[Dict[str, Any]],
        presentation_theme: str,
        global_context: str,
        language: str,
        max_clips: int = 3,
    ) -> Dict[str, Any]:
        """Plan the small number of deck moments that deserve video treatment."""
        if not slide_data:
            return build_fallback_video_plan(slide_data, presentation_theme, global_context, language, max_clips)

        if not self.video_generator_agent:
            logger.warning("Video planner agent not available; using fallback plan")
            return build_fallback_video_plan(slide_data, presentation_theme, global_context, language, max_clips)

        try:
            planner_prompt = build_video_planner_prompt(
                slide_data=slide_data,
                presentation_theme=presentation_theme,
                global_context=global_context,
                language=language,
                max_clips=max_clips,
            )
            response = await run_stateless_agent(self.video_generator_agent, planner_prompt)
            plan = parse_video_plan_response(response, max_clips=max_clips)
            if not plan["moments"]:
                logger.warning("Video planner returned no usable moments; using fallback plan")
                return build_fallback_video_plan(slide_data, presentation_theme, global_context, language, max_clips)

            plan.update(
                {
                    "presentation_theme": presentation_theme,
                    "global_context": global_context,
                    "language": language,
                    "max_clips": max_clips,
                    "raw_response": response,
                }
            )
            return plan
        except Exception as e:
            logger.error("Video planning failed: %s", e, exc_info=True)
            return build_fallback_video_plan(slide_data, presentation_theme, global_context, language, max_clips)
    
    async def save_video_prompt(
        self,
        slide_idx: int,
        video_prompt: str,
        speaker_notes: str,
        video_artifact: Optional[str] = None,
    ) -> str:
        """
        Save video prompt to file.
        
        Args:
            slide_idx: Slide index
            video_prompt: Video prompt text
            speaker_notes: Speaker notes
            video_artifact: Optional video artifact ID
            
        Returns:
            Path to saved prompt file
        """
        if not self.videos_dir:
            raise VideoGenerationError("Videos directory not configured")
        
        filename = FilePatterns.VIDEO_PROMPT_FILE.format(idx=slide_idx)
        filepath = os.path.join(self.videos_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(
                format_video_prompt_file(
                    slide_idx,
                    video_prompt,
                    speaker_notes,
                    video_artifact,
                )
            )
        
        logger.info(f"Saved video prompt to {filepath}")
        return filepath

    async def save_video_plan(
        self,
        plan: Dict[str, Any],
    ) -> str:
        """Save the selected video moments as a sidecar JSON plan."""
        if not self.videos_dir:
            raise VideoGenerationError("Videos directory not configured")

        filepath = os.path.join(self.videos_dir, FilePatterns.VIDEO_PLAN_FILE)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
            f.write("\n")

        logger.info("Saved video plan to %s", filepath)
        return filepath

    def _build_veo_client(self) -> genai.Client:
        """Create a Veo client for the current environment."""
        return genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )

    def _build_veo_config(
        self,
        *,
        duration_seconds: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "1080p",
        negative_prompt: Optional[str] = None,
    ) -> types.GenerateVideosConfig:
        """Create the Veo generation config."""
        config = types.GenerateVideosConfig(
            duration_seconds=duration_seconds,
            number_of_videos=1,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )
        if negative_prompt:
            config.negative_prompt = negative_prompt
        return config

    async def generate_veo_video(
        self,
        *,
        slide_idx: int,
        role: str,
        video_prompt: str,
        speaker_notes: str,
        slide_image: Optional[Image.Image],
        output_path: str,
        presentation_theme: str,
        global_context: str,
        language: str,
        model: Optional[str] = None,
        duration_seconds: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "1080p",
        negative_prompt: Optional[str] = None,
        retry_errors: bool = False,
    ) -> Optional[str]:
        """Generate a Veo video clip and save it to disk."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_file.exists() and not retry_errors:
            logger.info("Veo clip already exists for slide %s: %s", slide_idx, output_file)
            return str(output_file)

        client = self._build_veo_client()
        prompt = build_veo_video_prompt(
            slide_idx=slide_idx,
            role=role,
            video_prompt=video_prompt,
            speaker_notes=speaker_notes,
            presentation_theme=presentation_theme,
            global_context=global_context,
            language=language,
        )

        image = None
        if slide_image is not None:
            buffer = io.BytesIO()
            slide_image.save(buffer, format="PNG")
            image = types.Image(image_bytes=buffer.getvalue(), mime_type="image/png")

        veo_model = model or os.getenv("MODEL_VEO", ModelConfig.VEO)
        config = self._build_veo_config(
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            negative_prompt=negative_prompt,
        )

        logger.info(
            "Generating Veo clip for slide %s with model %s -> %s",
            slide_idx,
            veo_model,
            output_file,
        )
        request_kwargs = {
            "model": veo_model,
            "prompt": prompt,
            "config": config,
        }
        if image is not None:
            request_kwargs["image"] = image

        operation = client.models.generate_videos(**request_kwargs)

        poll_count = 0
        while not operation.done:
            poll_count += 1
            logger.info(
                "Waiting for Veo video generation... (slide %s, poll %s)",
                slide_idx,
                poll_count,
            )
            await asyncio.sleep(10)
            operation = client.operations.get(operation)

        generated = getattr(getattr(operation, "response", None), "generated_videos", None)
        if not generated:
            raise VideoGenerationError(f"No Veo video returned for slide {slide_idx}")

        video_ref = generated[0].video
        try:
            client.files.download(file=video_ref)
        except Exception:
            # Some SDK builds already hydrate the bytes in-place.
            pass

        if hasattr(video_ref, "save"):
            video_ref.save(str(output_file))
        else:
            video_bytes = getattr(video_ref, "video_bytes", None)
            if not video_bytes:
                raise VideoGenerationError(f"Veo response missing video bytes for slide {slide_idx}")
            output_file.write_bytes(video_bytes)

        logger.info("Saved Veo clip to %s", output_file)
        return str(output_file)

    async def generate_planned_videos(
        self,
        *,
        plan: Dict[str, Any],
        slide_data: List[Dict[str, Any]],
        presentation_theme: str,
        global_context: str,
        language: str,
        retry_errors: bool = False,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate Veo clips for the selected plan moments."""
        if not self.videos_dir:
            raise VideoGenerationError("Videos directory not configured")

        slide_lookup = {
            item.get("slide_idx"): item for item in slide_data if item.get("slide_idx") is not None
        }
        moments = plan.get("moments", [])
        generated_count = 0
        failed_count = 0

        for moment in moments:
            slide_idx = moment.get("slide_idx")
            slide = slide_lookup.get(slide_idx)
            if not slide:
                moment["status"] = "skipped"
                moment["error"] = "Slide data not found"
                failed_count += 1
                continue

            slide_image = slide.get("slide_image")
            speaker_notes = slide.get("speaker_notes", "")
            role = moment.get("role", "section")
            video_prompt = moment.get("prompt") or build_video_prompt(speaker_notes)
            output_name = f"slide_{slide_idx}_{role}_veo.mp4"
            output_path = str(Path(self.videos_dir) / output_name)

            try:
                saved_path = await self.generate_veo_video(
                    slide_idx=slide_idx,
                    role=role,
                    video_prompt=video_prompt,
                    speaker_notes=speaker_notes,
                    slide_image=slide_image,
                    output_path=output_path,
                    presentation_theme=presentation_theme,
                    global_context=global_context,
                    language=language,
                    model=model,
                    retry_errors=retry_errors,
                )
                if saved_path:
                    moment["status"] = "success"
                    moment["video_path"] = saved_path
                    generated_count += 1
                else:
                    moment["status"] = "skipped"
                    moment["error"] = "No output returned"
                    failed_count += 1
            except Exception as e:
                moment["status"] = "error"
                moment["error"] = str(e)
                failed_count += 1
                logger.error("Veo generation failed for slide %s: %s", slide_idx, e, exc_info=True)

        plan["generated_count"] = generated_count
        plan["failed_count"] = failed_count
        return plan
    
    def _extract_artifact_id(self, agent_response: str) -> str:
        """
        Extract artifact ID from agent response.
        
        Args:
            agent_response: Full text response from agent
            
        Returns:
            Artifact ID if found, empty string otherwise
        """
        return extract_artifact_id(agent_response)
    
    def is_available(self) -> bool:
        """Check if video generation is available."""
        return self.video_generator_agent is not None
