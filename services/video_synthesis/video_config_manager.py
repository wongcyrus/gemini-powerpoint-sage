"""Video configuration management for video synthesis."""

import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from core.domain.video_synthesis import VideoConfig, VideoConfigurationError

logger = logging.getLogger(__name__)


class VideoConfigManager:
    """Manager for video synthesis configuration."""
    
    def __init__(self):
        """Initialize video configuration manager."""
        self.default_config = self.create_default_config()
    
    @staticmethod
    def create_default_config() -> VideoConfig:
        """Create default video configuration."""
        return VideoConfig(
            resolution=(1920, 1080),
            fps=30,
            video_codec="libx264",
            audio_codec="aac",
            video_bitrate="1M",
            audio_bitrate="96k",
            output_format="mp4",
            fade_duration=0.5
        )
    
    @staticmethod
    def create_hd_config() -> VideoConfig:
        """Create HD (720p) video configuration."""
        return VideoConfig(
            resolution=(1280, 720),
            fps=30,
            video_codec="libx264",
            audio_codec="aac",
            video_bitrate="1.5M",
            audio_bitrate="128k",
            output_format="mp4",
            fade_duration=0.5
        )
    
    @staticmethod
    def create_4k_config() -> VideoConfig:
        """Create 4K video configuration."""
        return VideoConfig(
            resolution=(3840, 2160),
            fps=30,
            video_codec="libx264",
            audio_codec="aac",
            video_bitrate="8M",
            audio_bitrate="192k",
            output_format="mp4",
            fade_duration=0.5
        )
    
    @staticmethod
    def create_web_optimized_config() -> VideoConfig:
        """Create web-optimized video configuration."""
        return VideoConfig(
            resolution=(1280, 720),
            fps=30,
            video_codec="libx264",
            audio_codec="aac",
            video_bitrate="1M",
            audio_bitrate="96k",
            output_format="mp4",
            fade_duration=0.3
        )
    
    def validate_config(self, config: VideoConfig) -> None:
        """
        Validate video configuration parameters.
        
        Args:
            config: Video configuration to validate
            
        Raises:
            VideoConfigurationError: If configuration is invalid
        """
        try:
            logger.debug("Validating video configuration")
            
            # Validate resolution
            width, height = config.resolution
            if width <= 0 or height <= 0:
                raise VideoConfigurationError(f"Invalid resolution: {width}x{height}. Both dimensions must be positive.")
            
            # Check for common aspect ratios and warn if unusual
            aspect_ratio = width / height
            common_ratios = {
                16/9: "16:9",
                4/3: "4:3", 
                1/1: "1:1",
                21/9: "21:9"
            }
            
            closest_ratio = min(common_ratios.keys(), key=lambda x: abs(x - aspect_ratio))
            if abs(aspect_ratio - closest_ratio) > 0.1:
                logger.warning(f"Unusual aspect ratio {aspect_ratio:.2f} for resolution {width}x{height}")
            
            # Validate FPS
            if config.fps <= 0:
                raise VideoConfigurationError(f"Invalid FPS: {config.fps}. Must be positive.")
            
            if config.fps > 120:
                logger.warning(f"Very high FPS: {config.fps}. This may result in large file sizes.")
            
            # Validate video codec
            supported_video_codecs = {
                "libx264": "H.264 (widely compatible)",
                "libx265": "H.265/HEVC (better compression)",
                "libvpx": "VP8 (WebM)",
                "libvpx-vp9": "VP9 (WebM)"
            }
            
            if config.video_codec not in supported_video_codecs:
                raise VideoConfigurationError(
                    f"Unsupported video codec: {config.video_codec}. "
                    f"Supported codecs: {list(supported_video_codecs.keys())}"
                )
            
            # Validate audio codec
            supported_audio_codecs = {
                "aac": "AAC (widely compatible)",
                "mp3": "MP3 (legacy)",
                "libvorbis": "Vorbis (OGG)",
                "libopus": "Opus (high quality)"
            }
            
            if config.audio_codec not in supported_audio_codecs:
                raise VideoConfigurationError(
                    f"Unsupported audio codec: {config.audio_codec}. "
                    f"Supported codecs: {list(supported_audio_codecs.keys())}"
                )
            
            # Validate bitrates
            self._validate_bitrate(config.video_bitrate, "video")
            self._validate_bitrate(config.audio_bitrate, "audio")
            
            # Validate output format
            supported_formats = {
                "mp4": "MP4 (widely compatible)",
                "avi": "AVI (legacy)",
                "mkv": "Matroska (flexible)",
                "webm": "WebM (web optimized)"
            }
            
            if config.output_format not in supported_formats:
                raise VideoConfigurationError(
                    f"Unsupported output format: {config.output_format}. "
                    f"Supported formats: {list(supported_formats.keys())}"
                )
            
            # Validate fade duration
            if config.fade_duration < 0:
                raise VideoConfigurationError(f"Invalid fade duration: {config.fade_duration}. Cannot be negative.")
            
            if config.fade_duration > 5.0:
                logger.warning(f"Long fade duration: {config.fade_duration}s. This may be noticeable in short slides.")
            
            # Validate codec/format compatibility
            self._validate_codec_format_compatibility(config)
            
            logger.debug("Video configuration validation successful")
            
        except VideoConfigurationError:
            # Re-raise configuration errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error validating video configuration: {e}"
            logger.error(error_msg)
            raise VideoConfigurationError(error_msg) from e
    
    def _validate_bitrate(self, bitrate: str, bitrate_type: str) -> None:
        """
        Validate bitrate string format and value.
        
        Args:
            bitrate: Bitrate string (e.g., "2M", "128k")
            bitrate_type: Type of bitrate ("video" or "audio")
            
        Raises:
            VideoConfigurationError: If bitrate is invalid
        """
        try:
            # Parse bitrate string
            if bitrate.endswith('k') or bitrate.endswith('K'):
                value = float(bitrate[:-1])
                unit = 'k'
            elif bitrate.endswith('M') or bitrate.endswith('m'):
                value = float(bitrate[:-1])
                unit = 'M'
            else:
                # Assume bits per second
                value = float(bitrate)
                unit = 'bps'
            
            if value <= 0:
                raise VideoConfigurationError(f"Invalid {bitrate_type} bitrate: {bitrate}. Must be positive.")
            
            # Convert to kbps for validation
            if unit == 'M':
                kbps = value * 1000
            elif unit == 'k':
                kbps = value
            else:  # bps
                kbps = value / 1000
            
            # Validate reasonable ranges
            if bitrate_type == "video":
                if kbps < 100:
                    logger.warning(f"Very low video bitrate: {bitrate}. Quality may be poor.")
                elif kbps > 50000:  # 50 Mbps
                    logger.warning(f"Very high video bitrate: {bitrate}. File size will be large.")
            else:  # audio
                if kbps < 32:
                    logger.warning(f"Very low audio bitrate: {bitrate}. Quality may be poor.")
                elif kbps > 320:
                    logger.warning(f"Very high audio bitrate: {bitrate}. May be unnecessary.")
            
        except ValueError as e:
            raise VideoConfigurationError(f"Invalid {bitrate_type} bitrate format: {bitrate}. Use format like '2M' or '128k'.") from e
    
    def _validate_codec_format_compatibility(self, config: VideoConfig) -> None:
        """
        Validate that codec and format combinations are compatible.
        
        Args:
            config: Video configuration to validate
            
        Raises:
            VideoConfigurationError: If codec/format combination is incompatible
        """
        # Define compatibility matrix
        format_codec_compatibility = {
            "mp4": {
                "video": ["libx264", "libx265"],
                "audio": ["aac", "mp3"]
            },
            "avi": {
                "video": ["libx264", "libx265"],
                "audio": ["aac", "mp3"]
            },
            "mkv": {
                "video": ["libx264", "libx265", "libvpx", "libvpx-vp9"],
                "audio": ["aac", "mp3", "libvorbis", "libopus"]
            },
            "webm": {
                "video": ["libvpx", "libvpx-vp9"],
                "audio": ["libvorbis", "libopus"]
            }
        }
        
        format_compat = format_codec_compatibility.get(config.output_format)
        if not format_compat:
            return  # Already validated in main validation
        
        # Check video codec compatibility
        if config.video_codec not in format_compat["video"]:
            raise VideoConfigurationError(
                f"Video codec '{config.video_codec}' is not compatible with format '{config.output_format}'. "
                f"Compatible video codecs: {format_compat['video']}"
            )
        
        # Check audio codec compatibility
        if config.audio_codec not in format_compat["audio"]:
            raise VideoConfigurationError(
                f"Audio codec '{config.audio_codec}' is not compatible with format '{config.output_format}'. "
                f"Compatible audio codecs: {format_compat['audio']}"
            )
    
    def create_config_from_dict(self, config_dict: Dict[str, Any]) -> VideoConfig:
        """
        Create VideoConfig from dictionary with validation.
        
        Args:
            config_dict: Dictionary containing configuration parameters
            
        Returns:
            Validated VideoConfig instance
            
        Raises:
            VideoConfigurationError: If configuration is invalid
        """
        try:
            # Start with default config
            config_data = asdict(self.default_config)
            
            # Update with provided values
            config_data.update(config_dict)
            
            # Handle resolution tuple
            if 'resolution' in config_dict:
                resolution = config_dict['resolution']
                if isinstance(resolution, (list, tuple)) and len(resolution) == 2:
                    config_data['resolution'] = tuple(resolution)
                else:
                    raise VideoConfigurationError(f"Invalid resolution format: {resolution}. Must be [width, height].")
            
            # Create and validate config
            config = VideoConfig(**config_data)
            self.validate_config(config)
            
            return config
            
        except TypeError as e:
            raise VideoConfigurationError(f"Invalid configuration parameters: {e}") from e
        except Exception as e:
            error_msg = f"Failed to create configuration from dictionary: {e}"
            logger.error(error_msg)
            raise VideoConfigurationError(error_msg) from e
    
    def get_config_summary(self, config: VideoConfig) -> Dict[str, Any]:
        """
        Get a human-readable summary of the configuration.
        
        Args:
            config: Video configuration
            
        Returns:
            Dictionary containing configuration summary
        """
        width, height = config.resolution
        aspect_ratio = width / height
        
        # Determine quality level
        pixel_count = width * height
        if pixel_count >= 3840 * 2160 * 0.8:  # ~4K
            quality_level = "4K/Ultra HD"
        elif pixel_count >= 1920 * 1080 * 0.8:  # ~Full HD
            quality_level = "Full HD"
        elif pixel_count >= 1280 * 720 * 0.8:  # ~HD
            quality_level = "HD"
        else:
            quality_level = "Standard Definition"
        
        return {
            "resolution": f"{width}x{height}",
            "quality_level": quality_level,
            "aspect_ratio": f"{aspect_ratio:.2f}:1",
            "frame_rate": f"{config.fps} fps",
            "video_codec": config.video_codec,
            "audio_codec": config.audio_codec,
            "video_bitrate": config.video_bitrate,
            "audio_bitrate": config.audio_bitrate,
            "output_format": config.output_format.upper(),
            "fade_duration": f"{config.fade_duration}s"
        }
    
    def optimize_config_for_content(self, config: VideoConfig, total_duration: float, slide_count: int) -> VideoConfig:
        """
        Optimize configuration based on content characteristics.
        
        Args:
            config: Base configuration
            total_duration: Total video duration in seconds
            slide_count: Number of slides
            
        Returns:
            Optimized configuration
        """
        optimized_config = VideoConfig(
            resolution=config.resolution,
            fps=config.fps,
            video_codec=config.video_codec,
            audio_codec=config.audio_codec,
            video_bitrate=config.video_bitrate,
            audio_bitrate=config.audio_bitrate,
            output_format=config.output_format,
            fade_duration=config.fade_duration
        )
        
        # Adjust fade duration based on average slide duration
        if slide_count > 0:
            avg_slide_duration = total_duration / slide_count
            
            # For very short slides, reduce fade duration
            if avg_slide_duration < 5.0:
                optimized_config.fade_duration = min(config.fade_duration, avg_slide_duration * 0.1)
                logger.info(f"Reduced fade duration to {optimized_config.fade_duration:.2f}s for short slides")
            
            # For very long presentations, consider reducing quality slightly
            if total_duration > 3600:  # 1 hour
                logger.info("Long presentation detected. Consider using web-optimized settings for smaller file size.")
        
        return optimized_config