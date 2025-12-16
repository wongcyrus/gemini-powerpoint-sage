"""TTS storage management."""

import logging
import os
from pathlib import Path
from typing import Dict, List

from core.domain.tts import TTSStorageError
from config.tts_config import TTSStorageConfig

logger = logging.getLogger(__name__)


class StorageManager:
    """Handles TTS file organization and cloud storage integration."""
    
    def __init__(self, storage_config: TTSStorageConfig, main_config=None):
        """Initialize storage manager with configuration."""
        self.config = storage_config
        self.main_config = main_config  # Optional main config for directory integration
        self.local_cache_dir = Path(storage_config.local_cache_dir)
        
        # Ensure local cache directory exists (fallback only)
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_speech_directory_path(
        self,
        presentation_id: str,
        language_code: str
    ) -> str:
        """
        Generate organized directory path for speech files.
        
        Args:
            presentation_id: Base name of presentation
            language_code: Language code
            
        Returns:
            Directory path for speech files
        """
        # Use the main config's speech directory if available (this respects output_dir from YAML)
        if self.main_config:
            try:
                # The main config's speech_dir already handles output_dir from style YAML
                speech_dir = self.main_config.speech_dir
                logger.info(f"Using main config speech directory (respects YAML output_dir): {speech_dir}")
                return speech_dir
            except Exception as e:
                logger.warning(f"Failed to use main config speech directory: {e}")
        
        # Fallback: Try to create a config that matches the visual output structure
        try:
            from config.config import Config
            
            # Create a temporary config to get the proper output directory structure
            temp_config = Config(
                pptx_path=f"{presentation_id}.pptx",
                pdf_path=f"{presentation_id}.pdf",
                language=language_code,
                style=getattr(self.main_config, 'style', 'professional') if self.main_config else 'professional',
                output_dir=getattr(self.main_config, 'output_dir', None) if self.main_config else None
            )
            speech_dir = temp_config.speech_dir
            logger.info(f"Using temp config speech directory: {speech_dir}")
            return speech_dir
        except Exception as e:
            logger.warning(f"Failed to create temp config for speech directory: {e}")
            
            # Final fallback: Use default structure
            try:
                # Determine style and output_dir from main config
                style = getattr(self.main_config, 'style', 'professional') if self.main_config else 'professional'
                output_dir = getattr(self.main_config, 'output_dir', None) if self.main_config else None
                
                if output_dir:
                    # Use the output_dir from style configuration (e.g., "notes/hkcomic/generate")
                    base_output_dir = Path(output_dir)
                    logger.info(f"Using style-configured output directory: {base_output_dir}")
                else:
                    # Fallback to default output structure: output/[style]/generate/
                    if style and style.lower() != "professional":
                        style_folder = style.replace(" ", "_").lower()
                        base_output_dir = Path("output") / style_folder / "generate"
                    else:
                        base_output_dir = Path("output") / "professional" / "generate"
                    logger.info(f"Using default output structure: {base_output_dir}")
                
                # Create speech directory name using the same pattern as visuals
                speech_dir_name = f"{presentation_id}_{language_code}_speech"
                speech_dir_path = base_output_dir / speech_dir_name
                
                logger.info(f"Final fallback speech directory path: {speech_dir_path}")
                return str(speech_dir_path)
                
            except Exception as fallback_error:
                logger.warning(f"Enhanced fallback failed: {fallback_error}")
                
                # Final fallback to original cache behavior
                directory_name = self.config.directory_pattern.format(
                    base_name=presentation_id,
                    language_code=language_code
                )
                return str(self.local_cache_dir / directory_name)
    
    def generate_audio_filename(
        self,
        slide_number: int,
        content_hash: str
    ) -> str:
        """
        Generate filename for audio file.
        
        Args:
            slide_number: Slide number
            content_hash: Content hash for uniqueness
            
        Returns:
            Audio filename
        """
        return self.config.filename_pattern.format(
            slide_number=slide_number,
            content_hash=content_hash[:8]  # Use first 8 chars of hash
        )
    
    def get_audio_file_path(
        self,
        presentation_id: str,
        language_code: str,
        slide_number: int,
        content_hash: str
    ) -> str:
        """
        Get full path for audio file.
        
        Args:
            presentation_id: Presentation identifier
            language_code: Language code
            slide_number: Slide number
            content_hash: Content hash
            
        Returns:
            Full path to audio file
        """
        directory = self.generate_speech_directory_path(presentation_id, language_code)
        filename = self.generate_audio_filename(slide_number, content_hash)
        return os.path.join(directory, filename)
    
    async def save_audio_file(
        self,
        audio_data: bytes,
        file_path: str
    ) -> str:
        """
        Save audio data to local file.
        
        Args:
            audio_data: Audio data to save
            file_path: Path where to save the file
            
        Returns:
            Path to saved file
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write audio data
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            # Print file path prominently for user visibility
            print(f"🎵 TTS MP3 SAVED: {file_path}")
            logger.info(f"✓ Saved TTS audio file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving audio file {file_path}: {e}")
            raise TTSStorageError(f"Failed to save audio file: {e}")
    
    async def migrate_audio_file(
        self,
        old_file_path: str,
        new_file_path: str
    ) -> str:
        """
        Migrate audio file from old location to new location.
        
        Args:
            old_file_path: Path to existing audio file
            new_file_path: Path where to copy the file
            
        Returns:
            Path to migrated file
        """
        try:
            import shutil
            
            # Check if old file exists
            if not os.path.exists(old_file_path):
                raise TTSStorageError(f"Source file not found: {old_file_path}")
            
            # Ensure target directory exists
            Path(new_file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to new location
            shutil.copy2(old_file_path, new_file_path)
            
            # Print migration information prominently
            print(f"🔄 TTS MIGRATED: {old_file_path} → {new_file_path}")
            logger.info(f"✓ Migrated audio file from {old_file_path} to {new_file_path}")
            return new_file_path
            
        except Exception as e:
            logger.error(f"Error migrating audio file from {old_file_path} to {new_file_path}: {e}")
            raise TTSStorageError(f"Failed to migrate audio file: {e}")
    
    async def upload_audio_file(
        self,
        file_path: str,
        remote_path: str
    ) -> str:
        """
        Upload audio file to cloud storage and return public URL.
        
        Args:
            file_path: Local file path
            remote_path: Remote path in cloud storage
            
        Returns:
            Public URL for the uploaded file
        """
        # TODO: Implement cloud storage upload
        # This would integrate with Google Cloud Storage or similar
        
        # For now, return a placeholder URL
        # In a real implementation, this would:
        # 1. Upload file to cloud storage bucket
        # 2. Set appropriate permissions
        # 3. Return public URL
        
        logger.warning("Cloud storage upload not implemented, returning local path")
        return f"file://{file_path}"
    
    def create_local_directory_structure(
        self,
        base_name: str,
        languages: List[str]
    ) -> Dict[str, str]:
        """
        Create local directory structure for speech files.
        
        Args:
            base_name: Base presentation name
            languages: List of language codes
            
        Returns:
            Dictionary mapping language codes to directory paths
        """
        directories = {}
        
        for language in languages:
            directory_path = self.generate_speech_directory_path(base_name, language)
            
            try:
                os.makedirs(directory_path, exist_ok=True)
                directories[language] = directory_path
                logger.debug(f"Created directory for {language}: {directory_path}")
                
            except Exception as e:
                logger.error(f"Error creating directory for {language}: {e}")
                raise TTSStorageError(f"Failed to create directory for {language}: {e}")
        
        return directories
    
    def cleanup_old_files(self, max_age_days: int = 7) -> int:
        """
        Clean up old audio files.
        
        Args:
            max_age_days: Maximum age of files to keep
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        cleaned_count = 0
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        try:
            for root, dirs, files in os.walk(self.local_cache_dir):
                for file in files:
                    if file.endswith('.mp3'):
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.debug(f"Cleaned up old file: {file_path}")
            
            logger.info(f"Cleaned up {cleaned_count} old audio files")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return cleaned_count
    
    def get_storage_stats(self) -> Dict[str, any]:
        """Get storage statistics."""
        total_files = 0
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(self.local_cache_dir):
                for file in files:
                    if file.endswith('.mp3'):
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            total_files += 1
                            total_size += os.path.getsize(file_path)
        
        except Exception as e:
            logger.warning(f"Error calculating storage stats: {e}")
        
        return {
            "total_files": total_files,
            "total_size_mb": total_size / (1024 * 1024),
            "storage_directory": str(self.local_cache_dir),
            "bucket_name": self.config.bucket_name
        }