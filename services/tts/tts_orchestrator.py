"""TTS orchestrator for workflow coordination."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from google.cloud import texttospeech

from core.domain.tts import (
    TTSResult, SlideData, TTSEngineType, StyleContext, VoiceConfig, TTSEngineError
)
from config.tts_config import TTSConfig
from services.tts.engine_selector import EngineSelector
from services.tts.cache_manager import CacheManager
from services.tts.storage_manager import StorageManager
from services.tts.tts_style_adapter import TTSStyleAdapter
from services.tts.engines import GeminiTTSEngine, TraditionalTTSEngine

logger = logging.getLogger(__name__)


class TTSOrchestrator:
    """Main TTS orchestrator for slide processing coordination."""
    
    def __init__(
        self,
        tts_config: TTSConfig,
        tts_style_adapter: TTSStyleAdapter,
        engine_selector: EngineSelector,
        cache_manager: CacheManager,
        storage_manager: StorageManager,
        gemini_engine: Optional[GeminiTTSEngine] = None,
        traditional_engine: Optional[TraditionalTTSEngine] = None
    ):
        """
        Initialize TTS orchestrator with all required components.
        
        Args:
            tts_config: TTS system configuration
            tts_style_adapter: Style adapter for prompt generation
            engine_selector: Engine selection logic
            cache_manager: Audio caching manager
            storage_manager: File storage manager
            gemini_engine: Optional Gemini TTS engine instance
            traditional_engine: Optional Traditional TTS engine instance
        """
        self.config = tts_config
        self.style_adapter = tts_style_adapter
        self.engine_selector = engine_selector
        self.cache_manager = cache_manager
        self.storage_manager = storage_manager
        
        # Initialize TTS engines
        self.gemini_engine = gemini_engine or self._create_gemini_engine()
        self.traditional_engine = traditional_engine or self._create_traditional_engine()
        
        # Engine-specific semaphores for controlling concurrent operations
        self.gemini_semaphore = asyncio.Semaphore(tts_config.get_max_concurrent_for_engine(TTSEngineType.GEMINI))
        self.traditional_semaphore = asyncio.Semaphore(tts_config.get_max_concurrent_for_engine(TTSEngineType.TRADITIONAL))
        
        logger.info("TTSOrchestrator initialized with dual-engine support")
    
    def _check_and_adjust_engine_for_size(
        self,
        text_content: str,
        speaker_notes: str,
        original_engine: TTSEngineType,
        slide_number: int
    ) -> TTSEngineType:
        """
        Check if content fits Gemini TTS size limits and adjust engine if needed.
        
        Args:
            text_content: Main slide text content
            speaker_notes: Speaker notes for style analysis
            original_engine: Originally selected engine
            slide_number: Slide number for logging
            
        Returns:
            Adjusted engine type
        """
        if original_engine != TTSEngineType.GEMINI:
            return original_engine
        
        # Import here to avoid circular imports
        from utils.text_processing import check_gemini_tts_size_limit
        
        # Generate a sample style prompt to check total size
        # Use a typical style prompt length for estimation
        sample_style_prompt = "Speak in a professional, clear manner with appropriate emphasis on key concepts and maintain good pacing for comprehension."
        
        # Check if content would fit within Gemini TTS limits
        if check_gemini_tts_size_limit(text_content, sample_style_prompt):
            return TTSEngineType.GEMINI
        else:
            logger.info(f"Slide {slide_number}: Content too large for Gemini TTS, using Traditional TTS instead")
            return TTSEngineType.TRADITIONAL
    
    def _create_gemini_engine(self) -> GeminiTTSEngine:
        """Create Gemini TTS engine instance."""
        try:
            client = texttospeech.TextToSpeechClient()
            return GeminiTTSEngine(client, self.config.gemini)
        except Exception as e:
            logger.error(f"Failed to create Gemini TTS engine: {e}")
            raise TTSEngineError(f"Gemini TTS engine initialization failed: {e}")
    
    def _create_traditional_engine(self) -> TraditionalTTSEngine:
        """Create Traditional TTS engine instance."""
        try:
            client = texttospeech.TextToSpeechClient()
            return TraditionalTTSEngine(client, self.config.traditional)
        except Exception as e:
            logger.error(f"Failed to create Traditional TTS engine: {e}")
            raise TTSEngineError(f"Traditional TTS engine initialization failed: {e}")
    
    async def generate_speech_for_slide(
        self,
        slide_number: int,
        text_content: str,
        speaker_notes: str,
        language_code: str,
        presentation_id: str,
        title: str = ""
    ) -> TTSResult:
        """
        Generate speech audio for a slide with contextual styling.
        
        Args:
            slide_number: Slide number
            text_content: Main slide text content
            speaker_notes: Speaker notes for style analysis
            language_code: Target language code
            presentation_id: Presentation identifier
            title: Optional slide title
            
        Returns:
            TTSResult with generated audio and metadata
        """
        try:
            logger.info(f"Generating speech for slide {slide_number} in {language_code}")
            
            # Normalize language code
            normalized_language = self.config.normalize_language_code(language_code)
            
            # Select appropriate TTS engine using normalized language
            engine_type = self.engine_selector.select_engine(normalized_language)
            
            # Check if content is too large for Gemini TTS and force Traditional TTS if needed
            if engine_type == TTSEngineType.GEMINI:
                engine_type = self._check_and_adjust_engine_for_size(
                    text_content, speaker_notes, engine_type, slide_number
                )
            
            # Use engine-specific semaphore for concurrency control
            semaphore = self.gemini_semaphore if engine_type == TTSEngineType.GEMINI else self.traditional_semaphore
            
            async with semaphore:
                # Create slide data with normalized language
                slide_data = SlideData(
                    slide_number=slide_number,
                    text_content=text_content,
                    speaker_notes=speaker_notes,
                    language_code=normalized_language,
                    presentation_id=presentation_id,
                    title=title
                )
                
                # Analyze speaker notes for style context
                style_context = self.style_adapter.analyze_speaker_notes(
                    speaker_notes, text_content
                )
                
                # Get voice configuration using normalized language
                voice_config = self.engine_selector.get_voice_config(
                    normalized_language, engine_type
                )
                
                # Generate cache key using normalized language
                cache_key = self.cache_manager.generate_cache_key(
                    text_content, style_context, voice_config, normalized_language
                )
                
                # Get expected file path (like visual content approach)
                expected_file_path = self.storage_manager.get_audio_file_path(
                    presentation_id, language_code, slide_number, cache_key
                )
                
                # Debug: Print cache key and expected path
                print(f"🔍 SLIDE {slide_number} CACHE DEBUG:")
                print(f"   Cache Key: {cache_key[:16]}...")
                print(f"   Expected:  {expected_file_path}")
                
                # Check cache first (file path based like visual content)
                cached_audio_data = await self.cache_manager.get_cached_audio(cache_key, expected_file_path)
                if cached_audio_data:
                    logger.info(f"✓ Cache hit for slide {slide_number}")
                    
                    # Create TTSResult from cached audio data
                    cached_result = TTSResult(
                        audio_data=cached_audio_data,
                        engine_used=TTSEngineType.GEMINI,  # Default assumption
                        file_path=expected_file_path,
                        cache_key=cache_key,
                        metadata={"cached": True}
                    )
                    
                    # Print cached file path information prominently
                    print(f"💾 SLIDE {slide_number} TTS (CACHED): {expected_file_path}")
                    return cached_result
                
                # Fallback: Check for any existing file for this slide (cache key mismatch tolerance)
                speech_dir = Path(expected_file_path).parent
                if speech_dir.exists():
                    existing_files = list(speech_dir.glob(f"slide_{slide_number}_*.mp3"))
                    if existing_files:
                        existing_file = existing_files[0]  # Use first match
                        logger.info(f"✓ Found existing audio file for slide {slide_number} (cache key mismatch)")
                        
                        try:
                            with open(existing_file, 'rb') as f:
                                cached_audio_data = f.read()
                            
                            # Create TTSResult from existing file
                            cached_result = TTSResult(
                                audio_data=cached_audio_data,
                                engine_used=TTSEngineType.GEMINI,
                                file_path=str(existing_file),
                                cache_key=cache_key,
                                metadata={"cached": True, "cache_key_mismatch": True}
                            )
                            
                            print(f"💾 SLIDE {slide_number} TTS (EXISTING): {existing_file}")
                            return cached_result
                            
                        except Exception as e:
                            logger.warning(f"Failed to read existing file {existing_file}: {e}")
                
                # Generate speech using appropriate engine
                if engine_type == TTSEngineType.GEMINI:
                    tts_result = await self._generate_with_gemini(
                        slide_data, style_context, voice_config, cache_key
                    )
                else:
                    tts_result = await self._generate_with_traditional(
                        slide_data, style_context, voice_config, cache_key
                    )
                
                # Save audio file locally using original language code (for consistency with visual output)
                file_path = self.storage_manager.get_audio_file_path(
                    presentation_id, language_code, slide_number, cache_key
                )
                
                saved_path = await self.storage_manager.save_audio_file(
                    tts_result.audio_data, file_path
                )
                
                # Update result with file path
                tts_result.file_path = saved_path
                tts_result.cache_key = cache_key
                
                # Store in cache (file path based - no metadata needed)
                await self.cache_manager.store_audio(cache_key, saved_path)
                
                # Print file path information prominently
                print(f"📁 SLIDE {slide_number} TTS: {saved_path}")
                logger.info(f"✓ Generated speech for slide {slide_number} ({tts_result.duration_seconds:.1f}s) → {saved_path}")
                return tts_result
                
        except Exception as e:
            logger.error(f"Failed to generate speech for slide {slide_number}: {e}")
            # Return empty result to allow graceful degradation
            return TTSResult(
                audio_data=b"",
                engine_used=TTSEngineType.GEMINI,
                metadata={"error": str(e)}
            )
    
    async def _generate_with_gemini(
        self,
        slide_data: SlideData,
        style_context: StyleContext,
        voice_config: VoiceConfig,
        cache_key: str
    ) -> TTSResult:
        """Generate speech using Gemini TTS engine."""
        try:
            # Generate style prompt with presentation_id for caching
            style_prompt = self.style_adapter.generate_tts_style_prompt(
                slide_data.speaker_notes,
                slide_data.text_content,
                slide_data.language_code,
                slide_data.presentation_id
            )
            
            # Synthesize speech
            result = await self.gemini_engine.synthesize_speech(
                slide_data.text_content,
                style_prompt,
                voice_config,
                slide_data.language_code
            )
            
            logger.debug(f"Gemini TTS synthesis completed for slide {slide_data.slide_number}")
            return result
            
        except Exception as e:
            logger.warning(f"Gemini TTS failed, attempting fallback to Traditional TTS: {e}")
            # Fallback to traditional TTS
            return await self._generate_with_traditional(
                slide_data, style_context, voice_config, cache_key
            )
    
    async def _generate_with_traditional(
        self,
        slide_data: SlideData,
        style_context: StyleContext,
        voice_config: VoiceConfig,
        cache_key: str
    ) -> TTSResult:
        """Generate speech using Traditional TTS engine."""
        result = await self.traditional_engine.synthesize_speech(
            slide_data.text_content,
            voice_config,
            slide_data.language_code,
            style_context
        )
        
        logger.debug(f"Traditional TTS synthesis completed for slide {slide_data.slide_number}")
        return result
    
    async def process_presentation_batch(
        self,
        slides_data: List[SlideData],
        languages: List[str],
        presentation_id: str
    ) -> Dict[str, List[TTSResult]]:
        """
        Process multiple slides and languages in parallel.
        
        Args:
            slides_data: List of slide data to process
            languages: List of language codes to generate
            presentation_id: Presentation identifier
            
        Returns:
            Dictionary mapping language codes to lists of TTS results
        """
        if not self.config.enabled:
            logger.info("TTS system is disabled, skipping batch processing")
            return {}
        
        logger.info(f"Processing batch: {len(slides_data)} slides x {len(languages)} languages")
        
        # Pre-analyze presentation style for each language to avoid per-slide LLM calls
        logger.info("Pre-analyzing presentation style to optimize TTS generation...")
        for language in languages:
            slides_for_analysis = [
                {
                    "speaker_notes": slide.speaker_notes,
                    "text_content": slide.text_content
                }
                for slide in slides_data[:5]  # Use first 5 slides for analysis
            ]
            self.style_adapter.analyze_presentation_style(
                slides_for_analysis, language, presentation_id
            )
        
        # Create directory structure for all languages
        self.storage_manager.create_local_directory_structure(
            presentation_id, languages
        )
        
        # Create tasks for all slide/language combinations
        tasks = []
        for language in languages:
            for slide_data in slides_data:
                # Update slide data with current language
                slide_data.language_code = language
                
                task = self.generate_speech_for_slide(
                    slide_data.slide_number,
                    slide_data.text_content,
                    slide_data.speaker_notes,
                    language,
                    presentation_id,
                    slide_data.title
                )
                tasks.append((language, slide_data.slide_number, task))
        
        # Execute tasks with controlled concurrency
        results = {}
        for language in languages:
            results[language] = []
        
        # Execute all tasks with engine-specific concurrency control
        # (concurrency is now controlled by engine-specific semaphores in generate_speech_for_slide)
        all_task_coroutines = [task for _, _, task in tasks]
        batch_results = await asyncio.gather(
            *all_task_coroutines,
            return_exceptions=True
        )
        
        # Organize results by language
        for (language, slide_number, _), result in zip(tasks, batch_results):
            if isinstance(result, Exception):
                logger.error(f"Task failed for slide {slide_number} in {language}: {result}")
                # Create empty result for failed tasks
                result = TTSResult(
                    audio_data=b"",
                    engine_used=TTSEngineType.GEMINI,
                    metadata={"error": str(result)}
                )
            
            results[language].append(result)
        
        # Log summary
        total_successful = sum(
            1 for lang_results in results.values()
            for result in lang_results
            if result.is_valid()
        )
        total_tasks = len(slides_data) * len(languages)
        
        # Print batch completion summary with file paths
        print(f"\n🎵 TTS BATCH COMPLETED: {total_successful}/{total_tasks} successful")
        for language, lang_results in results.items():
            valid_results = [r for r in lang_results if r.is_valid()]
            if valid_results:
                print(f"📁 {language.upper()}: {len(valid_results)} files generated")
                # Show directory where files are saved
                if valid_results[0].file_path:
                    directory = str(Path(valid_results[0].file_path).parent)
                    print(f"   Directory: {directory}")
        
        logger.info(f"Batch processing completed: {total_successful}/{total_tasks} successful")
        
        return results
    
    async def process_single_language_batch(
        self,
        slides_data: List[SlideData],
        language_code: str,
        presentation_id: str
    ) -> List[TTSResult]:
        """
        Process multiple slides for a single language.
        
        Args:
            slides_data: List of slide data to process
            language_code: Language code to generate
            presentation_id: Presentation identifier
            
        Returns:
            List of TTS results
        """
        results = await self.process_presentation_batch(
            slides_data, [language_code], presentation_id
        )
        
        return results.get(language_code, [])
    
    async def regenerate_slide_audio(
        self,
        slide_number: int,
        text_content: str,
        speaker_notes: str,
        language_code: str,
        presentation_id: str,
        force_regenerate: bool = False
    ) -> TTSResult:
        """
        Regenerate audio for a specific slide, optionally bypassing cache.
        
        Args:
            slide_number: Slide number
            text_content: Slide text content
            speaker_notes: Speaker notes
            language_code: Language code
            presentation_id: Presentation identifier
            force_regenerate: If True, bypass cache
            
        Returns:
            TTSResult with regenerated audio
        """
        if force_regenerate:
            # Temporarily disable cache for this operation
            original_cache_enabled = self.cache_manager.config.enabled
            self.cache_manager.config.enabled = False
            
            try:
                result = await self.generate_speech_for_slide(
                    slide_number, text_content, speaker_notes,
                    language_code, presentation_id
                )
            finally:
                # Restore cache setting
                self.cache_manager.config.enabled = original_cache_enabled
            
            return result
        else:
            return await self.generate_speech_for_slide(
                slide_number, text_content, speaker_notes,
                language_code, presentation_id
            )
    
    def get_orchestrator_stats(self) -> Dict[str, any]:
        """Get orchestrator statistics."""
        # Get common output directories for cache stats
        output_directories = [
            "output/professional/generate",
            "output/comic/generate", 
            "output/gundam/generate",
            "cache/tts_audio"  # fallback directory
        ]
        
        cache_stats = self.cache_manager.get_cache_stats(output_directories)
        storage_stats = self.storage_manager.get_storage_stats()
        
        return {
            "config": {
                "enabled": self.config.enabled,
                "parallel_processing": self.config.parallel_processing,
                "max_concurrent_slides": self.config.max_concurrent_slides,
                "gemini_max_concurrent": self.config.gemini_max_concurrent,
                "traditional_max_concurrent": self.config.traditional_max_concurrent
            },
            "engines": {
                "gemini_supported_languages": len(self.config.gemini.supported_languages),
                "traditional_supported_languages": len(self.config.traditional.fallback_languages)
            },
            "cache": cache_stats,
            "storage": storage_stats
        }


def create_tts_orchestrator(
    tts_config: Optional[TTSConfig] = None,
    tts_style_adapter: Optional[TTSStyleAdapter] = None,
    main_config=None
) -> TTSOrchestrator:
    """
    Factory function to create TTS orchestrator with default components.
    
    Args:
        tts_config: Optional TTS configuration
        tts_style_adapter: Optional style adapter
        main_config: Optional main config for directory integration
        
    Returns:
        Configured TTSOrchestrator instance
    """
    from config.tts_config import get_tts_config
    from services.prompt_rewriter import PromptRewriter
    
    # Use default config if not provided
    if tts_config is None:
        tts_config = get_tts_config()
    
    # Create style adapter if not provided
    if tts_style_adapter is None:
        prompt_rewriter = PromptRewriter()
        tts_style_adapter = TTSStyleAdapter(prompt_rewriter)
    
    # Create other components
    engine_selector = EngineSelector(tts_config)
    cache_manager = CacheManager(tts_config.cache)
    storage_manager = StorageManager(tts_config.storage, main_config)
    
    return TTSOrchestrator(
        tts_config=tts_config,
        tts_style_adapter=tts_style_adapter,
        engine_selector=engine_selector,
        cache_manager=cache_manager,
        storage_manager=storage_manager
    )