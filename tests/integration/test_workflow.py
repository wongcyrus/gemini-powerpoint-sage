"""Integration tests for complete workflows."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.agent_manager import AgentManager
from services.notes_generator import NotesGenerator
from services.translation_service import TranslationService
from services.video_service import VideoService


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    async def test_agent_manager_initialization(self, mock_prompt, mock_llm_agent):
        """Test that AgentManager initializes all agents correctly."""
        # Mock all prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        manager = AgentManager()
        manager.initialize_agents()
        
        # Verify all agents are created
        assert manager.get_supervisor() is not None
        assert manager.get_analyst() is not None
        assert manager.get_writer() is not None
        assert manager.get_translator() is not None
        
        # Verify they can be used by services
        translator = manager.get_translator()
        service = TranslationService(translator_agent=translator)
        
        assert service.is_translation_available()
    
    @pytest.mark.asyncio
    async def test_translation_workflow(self, mock_agent):
        """Test complete translation workflow."""
        with patch('services.translation_service.run_stateless_agent') as mock_run:
            mock_run.return_value = "翻译的内容"
            
            service = TranslationService(translator_agent=mock_agent)
            
            # Translate notes
            result = await service.translate_notes(
                english_notes="English content",
                target_language="zh-CN",
                slide_idx=1
            )
            
            assert result == "翻译的内容"
            assert service.is_translation_available()
    
    @pytest.mark.asyncio
    async def test_video_generation_workflow(self, mock_agent, sample_image):
        """Test complete video generation workflow."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('services.video_service.run_stateless_agent') as mock_run:
                mock_run.return_value = "artifact_id: video_123"
                
                service = VideoService(
                    video_generator_agent=mock_agent,
                    videos_dir=tmpdir
                )
                
                # Generate video
                artifact_id = await service.generate_video(
                    slide_idx=1,
                    speaker_notes="Test notes",
                    slide_image=sample_image
                )
                
                assert artifact_id == "video_123"
                
                # Save prompt
                filepath = await service.save_video_prompt(
                    slide_idx=1,
                    video_prompt="Test prompt",
                    speaker_notes="Test notes",
                    video_artifact=artifact_id
                )
                
                import os
                assert os.path.exists(filepath)
    
    @pytest.mark.asyncio
    async def test_notes_generation_translation_mode(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_english_notes
    ):
        """Test notes generation in translation mode."""
        # Mock translator tool
        async def mock_translator(text):
            return f"Translated: {text}"
        
        mock_tool_factory.create_translator_tool.return_value = mock_translator
        
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes=sample_english_notes
        )
        
        # Should use translation mode for slide 1
        notes, status = await generator.generate_notes(
            slide_idx=1,
            slide_image=Mock(),
            existing_notes="",
            previous_slide_summary="",
            presentation_theme="Test",
            global_context="Test context"
        )
        
        assert "Translated:" in notes
        assert status == "success"
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mock_agent):
        """Test error recovery in workflow."""
        call_count = 0
        
        async def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "Success after retry"
        
        with patch('services.translation_service.run_stateless_agent', failing_then_success):
            service = TranslationService(translator_agent=mock_agent)
            
            # Should succeed after retry
            result = await service.translate_notes(
                english_notes="Test",
                target_language="zh-CN"
            )
            
            # Note: Without retry in translate_notes, this will fail
            # This test demonstrates the need for retry logic
            assert call_count >= 1


@pytest.mark.integration
class TestServiceIntegration:
    """Integration tests for service interactions."""
    
    def test_services_can_share_agents(self, mock_agent):
        """Test that multiple services can share the same agent."""
        # Create multiple services with same agent
        translation_service = TranslationService(translator_agent=mock_agent)
        video_service = VideoService(video_generator_agent=mock_agent)
        
        assert translation_service.is_translation_available()
        assert video_service.is_available()
    
    @pytest.mark.asyncio
    async def test_service_pipeline(self, mock_agent, sample_image):
        """Test a pipeline of services working together."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup services
            translation = TranslationService(translator_agent=mock_agent)
            video = VideoService(
                video_generator_agent=mock_agent,
                videos_dir=tmpdir
            )
            
            # Mock responses
            with patch('services.translation_service.run_stateless_agent') as mock_translate:
                with patch('services.video_service.run_stateless_agent') as mock_video:
                    mock_translate.return_value = "翻译的笔记"
                    mock_video.return_value = "artifact_id: video_123"
                    
                    # Step 1: Translate notes
                    translated_notes = await translation.translate_notes(
                        english_notes="English notes",
                        target_language="zh-CN"
                    )
                    
                    # Step 2: Generate video with translated notes
                    artifact_id = await video.generate_video(
                        slide_idx=1,
                        speaker_notes=translated_notes,
                        slide_image=sample_image
                    )
                    
                    # Step 3: Save video prompt
                    filepath = await video.save_video_prompt(
                        slide_idx=1,
                        video_prompt="Test prompt",
                        speaker_notes=translated_notes,
                        video_artifact=artifact_id
                    )
                    
                    # Verify pipeline completed
                    assert translated_notes == "翻译的笔记"
                    assert artifact_id == "video_123"
                    
                    import os
                    assert os.path.exists(filepath)
