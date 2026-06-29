"""Tests for VideoService."""

import json
import pytest
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from PIL import Image

from services.video_service import VideoService
from utils.error_handling import VideoGenerationError


class TestVideoService:
    """Tests for VideoService class."""
    
    def test_initialization(self, mock_agent):
        """Test service initialization."""
        service = VideoService(
            video_generator_agent=mock_agent,
            videos_dir="/tmp/videos"
        )
        
        assert service.video_generator_agent == mock_agent
        assert service.videos_dir == "/tmp/videos"
    
    @pytest.mark.asyncio
    async def test_generate_video_prompt_with_notes(self):
        """Test video prompt generation with speaker notes."""
        service = VideoService()
        
        prompt = await service.generate_video_prompt(
            slide_idx=1,
            speaker_notes="This is a test slide about security concepts."
        )
        
        assert "professional" in prompt.lower()
        assert "video" in prompt.lower()
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_generate_video_prompt_uses_empty_fallback(self):
        """Empty notes should use the shared fallback prompt."""
        service = VideoService()

        from services.video_service_helpers import build_video_prompt

        assert await service.generate_video_prompt(1, "") == build_video_prompt("")
    
    @pytest.mark.asyncio
    async def test_generate_video_prompt_empty_notes(self):
        """Test video prompt generation with empty notes."""
        service = VideoService()
        
        prompt = await service.generate_video_prompt(
            slide_idx=1,
            speaker_notes=""
        )
        
        assert "engaging" in prompt.lower()
        assert len(prompt) > 0
    
    @pytest.mark.asyncio
    async def test_generate_video_prompt_long_notes(self):
        """Test video prompt generation truncates long notes."""
        service = VideoService()
        
        long_notes = "A" * 200  # Very long notes
        
        prompt = await service.generate_video_prompt(
            slide_idx=1,
            speaker_notes=long_notes
        )
        
        assert "A" * 151 not in prompt
        assert prompt.endswith("Focus on clarity and visual appeal.")
    
    @pytest.mark.asyncio
    async def test_generate_video_success(self, mock_agent, sample_image):
        """Test successful video generation."""
        with patch('services.video_service.run_stateless_agent') as mock_run:
            mock_run.return_value = "artifact_id: video_123"
            
            service = VideoService(video_generator_agent=mock_agent)
            
            result = await service.generate_video(
                slide_idx=1,
                speaker_notes="Test notes",
                slide_image=sample_image
            )
            
            assert result == "video_123"
    
    @pytest.mark.asyncio
    async def test_generate_video_no_agent(self):
        """Test video generation without agent returns None."""
        service = VideoService(video_generator_agent=None)
        
        result = await service.generate_video(
            slide_idx=1,
            speaker_notes="Test notes"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_video_no_artifact(self, mock_agent):
        """Test video generation with no artifact in response."""
        with patch('services.video_service.run_stateless_agent') as mock_run:
            mock_run.return_value = "No artifact here"
            
            service = VideoService(video_generator_agent=mock_agent)
            
            result = await service.generate_video(
                slide_idx=1,
                speaker_notes="Test notes"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_veo_video_saves_mp4(self, tmp_path):
        """Veo generation should save a real mp4 file to disk."""
        service = VideoService(videos_dir=str(tmp_path))
        slide_image = Image.new("RGB", (64, 64), color="white")

        class _VideoRef:
            video_bytes = b"video-bytes"

            def save(self, path):
                Path(path).write_bytes(self.video_bytes)

        class _Client:
            def __init__(self):
                self.models = SimpleNamespace(generate_videos=self.generate_videos)
                self.operations = SimpleNamespace(get=lambda operation: operation)
                self.files = SimpleNamespace(download=lambda file: None)

            def generate_videos(self, **kwargs):
                return SimpleNamespace(
                    done=True,
                    response=SimpleNamespace(
                        generated_videos=[SimpleNamespace(video=_VideoRef())]
                    ),
                )

        with patch("services.video_service.genai.Client", return_value=_Client()):
            output = await service.generate_veo_video(
                slide_idx=1,
                role="intro",
                video_prompt="Opening hook",
                speaker_notes="Welcome everyone.",
                slide_image=slide_image,
                output_path=str(tmp_path / "slide_1_intro_veo.mp4"),
                presentation_theme="Theme",
                global_context="Context",
                language="en",
            )

        assert output == str(tmp_path / "slide_1_intro_veo.mp4")
        assert Path(output).exists()
        assert Path(output).read_bytes() == b"video-bytes"

    @pytest.mark.asyncio
    async def test_plan_video_moments_uses_ai_response(self, mock_agent):
        """Planning should return normalized moments from the AI response."""
        service = VideoService(video_generator_agent=mock_agent)
        slide_data = [
            {"slide_idx": 1, "speaker_notes": "Opening", "status": "success"},
            {"slide_idx": 2, "speaker_notes": "Middle", "status": "success"},
        ]

        response = json.dumps(
            {
                "should_generate": True,
                "moments": [
                    {
                        "slide_idx": 1,
                        "role": "intro",
                        "reason": "Opening hook",
                        "prompt": "Use the opening slide as a hook",
                    },
                    {
                        "slide_idx": 2,
                        "role": "conclusion",
                        "reason": "Closing recap",
                        "prompt": "Use the closing slide",
                    },
                ],
            }
        )

        with patch('services.video_service.run_stateless_agent', new=AsyncMock(return_value=response)):
            plan = await service.plan_video_moments(
                slide_data,
                "Theme",
                "Global context",
                "en",
            )

        assert plan["should_generate"] is True
        assert len(plan["moments"]) == 2
        assert plan["moments"][0]["slide_idx"] == 1

    @pytest.mark.asyncio
    async def test_plan_video_moments_falls_back_without_agent(self):
        """Planning should fall back when no agent is configured."""
        service = VideoService(video_generator_agent=None)
        slide_data = [
            {"slide_idx": 1, "speaker_notes": "Opening", "status": "success"},
            {"slide_idx": 5, "speaker_notes": "Conclusion", "status": "success"},
        ]

        plan = await service.plan_video_moments(slide_data, "Theme", "Global", "en")

        assert plan["source"] == "fallback"
        assert plan["moments"][0]["role"] == "intro"

    @pytest.mark.asyncio
    async def test_generate_video_handles_agent_failure(self, mock_agent):
        """Test video generation failures return None instead of bubbling up."""
        with patch('services.video_service.run_stateless_agent', side_effect=RuntimeError("boom")):
            service = VideoService(video_generator_agent=mock_agent)

            result = await service.generate_video(
                slide_idx=1,
                speaker_notes="Test notes"
            )

            assert result is None
    
    @pytest.mark.asyncio
    async def test_save_video_prompt(self):
        """Test saving video prompt to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VideoService(videos_dir=tmpdir)
            
            filepath = await service.save_video_prompt(
                slide_idx=1,
                video_prompt="Test prompt",
                speaker_notes="Test notes",
                video_artifact="video_123"
            )
            
            assert os.path.exists(filepath)
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "Test prompt" in content
                assert "Test notes" in content
                assert "video_123" in content
    
    @pytest.mark.asyncio
    async def test_save_video_prompt_no_artifact(self):
        """Test saving video prompt without artifact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VideoService(videos_dir=tmpdir)
            
            filepath = await service.save_video_prompt(
                slide_idx=1,
                video_prompt="Test prompt",
                speaker_notes="Test notes"
            )
            
            assert os.path.exists(filepath)
            
            with open(filepath, 'r') as f:
                content = f.read()
                assert "Test prompt" in content
                assert "video_123" not in content

    @pytest.mark.asyncio
    async def test_save_video_prompt_requires_videos_dir(self):
        """Test saving a prompt without a configured videos dir raises an error."""
        service = VideoService(videos_dir=None)

        with pytest.raises(VideoGenerationError, match="Videos directory not configured"):
            await service.save_video_prompt(
                slide_idx=1,
                video_prompt="Test prompt",
                speaker_notes="Test notes",
            )

    @pytest.mark.asyncio
    async def test_save_video_plan(self):
        """Test saving the sidecar video plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VideoService(videos_dir=tmpdir)
            plan = {"should_generate": True, "moments": [{"slide_idx": 1, "role": "intro"}]}

            filepath = await service.save_video_plan(plan)

            assert os.path.exists(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["moments"][0]["slide_idx"] == 1
    
    def test_extract_artifact_id_explicit(self):
        """Test extracting explicit artifact_id."""
        service = VideoService()
        
        response = 'artifact_id: "video_abc123"'
        artifact_id = service._extract_artifact_id(response)
        
        assert artifact_id == "video_abc123"
    
    def test_extract_artifact_id_file_reference(self):
        """Test extracting video file reference."""
        service = VideoService()
        
        response = "Generated video_output.mp4 successfully"
        artifact_id = service._extract_artifact_id(response)
        
        assert artifact_id == "video_output.mp4"
    
    def test_extract_artifact_id_none(self):
        """Test extracting artifact_id when none present."""
        service = VideoService()
        
        response = "No artifact here"
        artifact_id = service._extract_artifact_id(response)
        
        assert artifact_id == ""
    
    def test_extract_artifact_id_empty_response(self):
        """Test extracting artifact_id from empty response."""
        service = VideoService()
        
        artifact_id = service._extract_artifact_id("")
        
        assert artifact_id == ""

    def test_extract_artifact_id_generic_video_reference(self):
        """Test extracting generic generated video references."""
        service = VideoService()

        artifact_id = service._extract_artifact_id("Generated asset named video_alpha_beta")

        assert artifact_id == "video_alpha_beta"

    def test_save_video_prompt_formats_expected_content(self):
        """Prompt files should render the shared content format."""
        from services.video_service_helpers import format_video_prompt_file

        content = format_video_prompt_file(1, "Prompt", "Notes", "video_123")
        assert "Slide 1 Video Prompt" in content
        assert "video_123" in content
    
    def test_is_available(self, mock_agent):
        """Test availability check."""
        service_with = VideoService(video_generator_agent=mock_agent)
        service_without = VideoService(video_generator_agent=None)
        
        assert service_with.is_available() is True
        assert service_without.is_available() is False
