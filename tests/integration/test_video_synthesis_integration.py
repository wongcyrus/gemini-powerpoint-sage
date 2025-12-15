"""Integration tests for video synthesis functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from core.domain.video_synthesis import VideoConfig, VideoSynthesisRequest
from services.video_synthesis import VideoSynthesisService, VideoConfigManager


class TestVideoSynthesisIntegration:
    """Integration tests for video synthesis service."""
    
    def test_video_config_creation_and_validation(self):
        """Test video configuration creation and validation."""
        config_manager = VideoConfigManager()
        
        # Test default config
        default_config = config_manager.create_default_config()
        assert default_config.resolution == (1920, 1080)
        assert default_config.video_codec == "libx264"
        
        # Test validation
        config_manager.validate_config(default_config)
        
        # Test HD config
        hd_config = config_manager.create_hd_config()
        assert hd_config.resolution == (1280, 720)
        config_manager.validate_config(hd_config)
        
        # Test custom config from dict
        custom_dict = {
            "resolution": [800, 600],
            "fps": 24,
            "video_bitrate": "1M"
        }
        custom_config = config_manager.create_config_from_dict(custom_dict)
        assert custom_config.resolution == (800, 600)
        assert custom_config.fps == 24
        config_manager.validate_config(custom_config)
    
    def test_video_config_validation_errors(self):
        """Test video configuration validation with invalid values."""
        config_manager = VideoConfigManager()
        
        # Test invalid resolution
        invalid_config = VideoConfig(resolution=(0, 1080))
        with pytest.raises(Exception):
            config_manager.validate_config(invalid_config)
        
        # Test invalid FPS
        invalid_config = VideoConfig(fps=-1)
        with pytest.raises(Exception):
            config_manager.validate_config(invalid_config)
        
        # Test invalid codec
        invalid_config = VideoConfig(video_codec="invalid_codec")
        with pytest.raises(Exception):
            config_manager.validate_config(invalid_config)
    
    def test_video_synthesis_request_validation(self):
        """Test video synthesis request validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock files
            slide1 = temp_path / "slide1.png"
            slide2 = temp_path / "slide2.png"
            audio1 = temp_path / "audio1.mp3"
            audio2 = temp_path / "audio2.mp3"
            output = temp_path / "output.mp4"
            
            # Create empty files for testing
            slide1.touch()
            slide2.touch()
            audio1.touch()
            audio2.touch()
            
            config = VideoConfig()
            
            # Test valid request
            request = VideoSynthesisRequest(
                slide_images=[slide1, slide2],
                audio_files=[audio1, audio2],
                output_path=output,
                config=config,
                presentation_id="test"
            )
            
            # Should not raise exception
            request.validate()
            
            # Test mismatched counts
            with pytest.raises(ValueError, match="must match"):
                VideoSynthesisRequest(
                    slide_images=[slide1],
                    audio_files=[audio1, audio2],
                    output_path=output,
                    config=config,
                    presentation_id="test"
                )
            
            # Test missing files
            missing_slide = temp_path / "missing.png"
            with pytest.raises(ValueError, match="not found"):
                VideoSynthesisRequest(
                    slide_images=[missing_slide],
                    audio_files=[audio1],
                    output_path=output,
                    config=config,
                    presentation_id="test"
                )
    
    @patch('services.video_synthesis.audio_analyzer.ffmpeg')
    def test_audio_analyzer_integration(self, mock_ffmpeg):
        """Test audio analyzer integration."""
        from services.video_synthesis.audio_analyzer import AudioAnalyzer
        
        # Mock ffmpeg probe response
        mock_ffmpeg.probe.return_value = {
            'format': {
                'duration': '45.123',
                'size': '1024000',
                'bit_rate': '128000'
            },
            'streams': [{
                'codec_type': 'audio',
                'codec_name': 'mp3',
                'sample_rate': '44100',
                'channels': '2'
            }]
        }
        
        analyzer = AudioAnalyzer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file = Path(temp_dir) / "test.mp3"
            audio_file.touch()
            
            # Test duration extraction
            duration = analyzer.get_audio_duration(audio_file)
            assert duration == 45.123
            
            # Test metadata extraction
            metadata = analyzer.get_audio_metadata(audio_file)
            assert metadata['duration_seconds'] == 45.123
            assert metadata['codec_name'] == 'mp3'
            assert metadata['sample_rate'] == 44100
            
            # Test validation
            assert analyzer.validate_audio_file(audio_file) is True
    
    @patch('services.video_synthesis.file_validator.Image')
    @patch('services.video_synthesis.file_validator.ffmpeg')
    def test_file_validator_integration(self, mock_ffmpeg, mock_image):
        """Test file validator integration."""
        from services.video_synthesis.file_validator import FileValidator
        
        # Mock PIL Image
        mock_img = Mock()
        mock_img.size = (1920, 1080)
        mock_img.mode = 'RGB'
        mock_img.format = 'PNG'
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        # Mock ffmpeg probe
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'audio'}]
        }
        
        validator = FileValidator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            image_file = temp_path / "test.png"
            audio_file = temp_path / "test.mp3"
            image_file.touch()
            audio_file.touch()
            
            # Test image validation
            image_metadata = validator.validate_image_file(image_file)
            assert image_metadata['width'] == 1920
            assert image_metadata['height'] == 1080
            
            # Test audio validation
            audio_metadata = validator.validate_audio_file(audio_file)
            assert audio_metadata['duration_seconds'] == 30.0
            
            # Test slide-audio pairs validation
            pairs = validator.validate_slide_audio_pairs([image_file], [audio_file])
            assert len(pairs) == 1
    
    def test_video_synthesis_service_initialization(self):
        """Test video synthesis service initialization."""
        service = VideoSynthesisService()
        
        # Test service components are initialized
        assert service.audio_analyzer is not None
        assert service.file_validator is not None
        assert service.config_manager is not None
        
        # Test supported formats
        formats = service.get_supported_formats()
        assert 'image_formats' in formats
        assert 'audio_formats' in formats
        assert 'video_formats' in formats
        
        # Test default config creation
        default_config = service.create_default_config()
        assert isinstance(default_config, VideoConfig)
    
    def test_progress_tracker_functionality(self):
        """Test progress tracker functionality."""
        from services.video_synthesis.progress_tracker import VideoProgressTracker, ProcessingStage
        
        tracker = VideoProgressTracker("test_op", 3)
        
        # Test initial state
        status = tracker.get_current_status()
        assert status['operation_id'] == "test_op"
        assert status['total_slides'] == 3
        assert status['current_slide'] == 0
        
        # Test stage updates
        tracker.update_stage(ProcessingStage.VALIDATING, "Validating files")
        status = tracker.get_current_status()
        assert status['stage'] == 'validating'
        
        # Test slide progress
        tracker.update_slide_progress(0, ProcessingStage.CREATING_SEGMENTS, "Processing slide 1")
        status = tracker.get_current_status()
        assert status['current_slide'] == 1
        
        # Test error reporting
        test_error = Exception("Test error")
        tracker.report_error(test_error, slide_index=0)
        status = tracker.get_current_status()
        assert status['error_count'] == 1
        
        # Test completion
        output_path = Path("/tmp/test.mp4")
        tracker.mark_completed(output_path, 1024000, 60.0)
        status = tracker.get_current_status()
        assert status['stage'] == 'completed'
        assert status['is_completed'] is True
    
    def test_file_manager_functionality(self):
        """Test file manager functionality."""
        from services.video_synthesis.file_manager import VideoFileManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test file manager creation
            manager = VideoFileManager(temp_path, "test_op")
            assert manager.temp_dir.exists()
            assert "test_op" in str(manager.temp_dir)
            
            # Test temp file creation
            temp_file = manager.get_temp_file_path("test.txt")
            assert temp_file.parent == manager.temp_dir
            
            # Test directory creation
            segments_dir = manager.create_segment_temp_dir()
            assert segments_dir.exists()
            assert segments_dir.name == "segments"
            
            # Test disk usage
            usage = manager.get_disk_usage()
            assert 'temp_files_size_bytes' in usage
            assert 'available_space_bytes' in usage
            
            # Test cleanup
            cleanup_stats = manager.cleanup()
            assert 'files_removed' in cleanup_stats
            assert 'dirs_removed' in cleanup_stats


@pytest.mark.asyncio
class TestVideoSynthesisAsyncIntegration:
    """Async integration tests for video synthesis."""
    
    @patch('services.video_synthesis.ffmpeg_processor.ffmpeg')
    async def test_video_synthesis_service_mock_workflow(self, mock_ffmpeg):
        """Test complete video synthesis workflow with mocked FFmpeg."""
        # Mock ffmpeg operations
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '10.0'},
            'streams': [{'codec_type': 'audio'}]
        }
        mock_ffmpeg.run.return_value = None
        
        service = VideoSynthesisService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock files
            slide1 = temp_path / "slide1.png"
            audio1 = temp_path / "audio1.mp3"
            output = temp_path / "output.mp4"
            
            slide1.touch()
            audio1.touch()
            
            # Create request
            config = VideoConfig()
            request = VideoSynthesisRequest(
                slide_images=[slide1],
                audio_files=[audio1],
                output_path=output,
                config=config,
                presentation_id="test"
            )
            
            # Mock the actual video processing to avoid FFmpeg dependency
            with patch.object(service, '_create_video_segments') as mock_create, \
                 patch.object(service, '_concatenate_segments') as mock_concat, \
                 patch.object(service, '_finalize_output') as mock_finalize:
                
                # Setup mocks
                mock_create.return_value = request.create_segments()
                mock_concat.return_value = temp_path / "temp_video.mp4"
                mock_finalize.return_value = output
                
                # Create mock output file
                output.touch()
                
                # Run synthesis
                result = service.synthesize_video(request)
                
                # Verify result
                assert result.success is True
                assert result.output_path == output
                assert result.slides_processed == 1