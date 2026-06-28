"""TTS Style Adapter for contextual speech generation."""

import logging
from typing import Optional, Dict, List, Any
from core.domain.tts import StyleContext, PresentationType
from services.prompt_rewriter import PromptRewriter
from services.tts.tts_style_adapter_helpers import (
    analyze_speaker_notes_to_style,
    build_base_tts_prompt,
    create_concise_prompt,
    create_fallback_prompt,
    extract_style_indicators,
    get_default_professional_style,
)

logger = logging.getLogger(__name__)


class TTSStyleAdapter:
    """
    Adapts the existing PromptRewriter system for TTS style prompt generation.
    Uses the LLM-powered rewriting capabilities to create contextual TTS prompts.
    """
    
    def __init__(self, prompt_rewriter: PromptRewriter):
        """Initialize with existing PromptRewriter instance."""
        self.prompt_rewriter = prompt_rewriter
        self._style_cache = {}  # Cache style prompts per presentation
        logger.info("TTSStyleAdapter initialized with PromptRewriter integration")
    
    def generate_tts_style_prompt(
        self,
        speaker_notes: str,
        slide_content: str,
        language_code: str,
        presentation_id: str = "",
        base_tts_prompt: Optional[str] = None
    ) -> str:
        """
        Generate TTS style prompt using the existing PromptRewriter system.
        Uses caching to avoid regenerating the same style for each slide.
        
        Args:
            speaker_notes: Speaker notes containing style indicators
            slide_content: Slide text content for context
            language_code: Target language for TTS
            presentation_id: Presentation identifier for caching
            base_tts_prompt: Base TTS instruction template
            
        Returns:
            Generated style prompt for Gemini TTS
        """
        # Create cache key for this presentation and language
        cache_key = f"{presentation_id}_{language_code}"
        
        # Check if we already have a style prompt for this presentation
        if cache_key in self._style_cache:
            logger.info(f"Using cached TTS style prompt for {cache_key}")
            return self._style_cache[cache_key]
        
        logger.info(f"Generating TTS style prompt for language: {language_code}")
        
        # Create base TTS prompt if not provided
        if not base_tts_prompt:
            base_tts_prompt = self._create_base_tts_prompt(language_code)
        
        # Create style guidelines from speaker notes analysis
        # For the first slide of a presentation, do a comprehensive analysis
        # For subsequent slides, this will be cached
        style_guidelines = self._analyze_speaker_notes_to_style(
            speaker_notes, slide_content
        )
        
        try:
            # Use the new rewrite_tts_prompt method
            tts_prompt = self.prompt_rewriter.rewrite_tts_prompt(
                base_tts_prompt, style_guidelines
            )
            
            # Check if prompt is too long for Gemini TTS (4000 byte limit)
            if len(tts_prompt.encode('utf-8')) > 3500:  # Leave some buffer
                logger.warning(f"TTS prompt too long ({len(tts_prompt)} chars), using concise fallback")
                tts_prompt = self._create_concise_prompt(style_guidelines, language_code)
            
            # Cache the generated prompt for this presentation
            self._style_cache[cache_key] = tts_prompt
            logger.info(f"✓ TTS style prompt generated and cached ({len(tts_prompt)} chars)")
            return tts_prompt
            
        except Exception as e:
            logger.warning(f"TTS style prompt generation failed, using fallback: {e}")
            fallback_prompt = self._create_concise_prompt(style_guidelines, language_code)
            # Cache the fallback too
            self._style_cache[cache_key] = fallback_prompt
            return fallback_prompt
    
    def analyze_speaker_notes(
        self,
        speaker_notes: str,
        slide_content: str
    ) -> StyleContext:
        """
        Analyze speaker notes to extract style context.
        
        Args:
            speaker_notes: Speaker notes text
            slide_content: Slide content for additional context
            
        Returns:
            StyleContext with extracted style information
        """
        logger.debug("Analyzing speaker notes for style context")
        
        if not speaker_notes or not speaker_notes.strip():
            logger.info("No speaker notes provided, using default professional style")
            return StyleContext()
        
        # Extract style indicators from speaker notes
        style_analysis = self._extract_style_indicators(speaker_notes, slide_content)
        
        # Create StyleContext from analysis
        return StyleContext(
            tone=style_analysis['tone'],
            pace=style_analysis['pace'],
            emphasis_words=style_analysis['emphasis_words'],
            emotional_indicators=style_analysis['emotions'],
            presentation_type=style_analysis['presentation_type'],
            confidence_score=style_analysis['confidence_score']
        )
    
    def _create_base_tts_prompt(self, language_code: str) -> str:
        """Create base TTS prompt template."""
        return build_base_tts_prompt(language_code)
    
    def _analyze_speaker_notes_to_style(
        self, 
        speaker_notes: str, 
        slide_content: str
    ) -> str:
        """
        Convert speaker notes into style guidelines format.
        This creates the style input for the PromptRewriter system.
        """
        return analyze_speaker_notes_to_style(speaker_notes, slide_content)
    
    def _extract_style_indicators(self, speaker_notes: str, slide_content: str) -> Dict:
        """Extract style indicators from speaker notes using pattern matching."""
        return extract_style_indicators(speaker_notes, slide_content)
    
    def _detect_presentation_type(self, notes: str, content: str) -> PresentationType:
        """Detect presentation type from content."""
        from services.tts.tts_style_adapter_helpers import detect_presentation_type

        return detect_presentation_type(notes, content)
    
    def _get_default_professional_style(self) -> str:
        """Return default professional style guidelines."""
        return get_default_professional_style()
    
    def _create_fallback_prompt(self, style_guidelines: str, language_code: str) -> str:
        """Create fallback prompt when LLM rewriting fails."""
        logger.info("Using fallback TTS prompt generation")
        return create_fallback_prompt(style_guidelines, language_code)
    
    def _create_concise_prompt(self, style_guidelines: str, language_code: str) -> str:
        """Create concise TTS prompt that stays under Gemini TTS length limits."""
        logger.info("Creating concise TTS prompt to stay under length limits")
        prompt = create_concise_prompt(style_guidelines, language_code)
        logger.info(f"Created concise TTS prompt: {len(prompt)} chars")
        return prompt
    
    def clear_style_cache(self, presentation_id: str = None):
        """
        Clear the style prompt cache.
        
        Args:
            presentation_id: If provided, clear only this presentation's cache.
                           If None, clear all cached styles.
        """
        if presentation_id:
            # Clear cache entries for specific presentation
            keys_to_remove = [key for key in self._style_cache.keys() if key.startswith(f"{presentation_id}_")]
            for key in keys_to_remove:
                del self._style_cache[key]
            logger.info(f"Cleared TTS style cache for presentation: {presentation_id}")
        else:
            # Clear all cache
            self._style_cache.clear()
            logger.info("Cleared all TTS style cache")
    
    def analyze_presentation_style(
        self,
        slides_data: List[Dict[str, str]],
        language_code: str,
        presentation_id: str
    ) -> str:
        """
        Analyze the overall presentation style from multiple slides.
        This is more efficient than analyzing each slide individually.
        
        Args:
            slides_data: List of slide data with speaker_notes and text_content
            language_code: Target language
            presentation_id: Presentation identifier
            
        Returns:
            Generated style prompt for the entire presentation
        """
        cache_key = f"{presentation_id}_{language_code}"
        
        # Check cache first
        if cache_key in self._style_cache:
            logger.info(f"Using cached presentation style for {cache_key}")
            return self._style_cache[cache_key]
        
        logger.info(f"Analyzing presentation style from {len(slides_data)} slides")
        
        # Combine speaker notes from first few slides for better style analysis
        combined_notes = ""
        combined_content = ""
        
        # Use first 3-5 slides for style analysis (or all if fewer)
        sample_size = min(5, len(slides_data))
        for i in range(sample_size):
            slide = slides_data[i]
            if slide.get("speaker_notes"):
                combined_notes += f" {slide['speaker_notes']}"
            if slide.get("text_content"):
                combined_content += f" {slide['text_content']}"
        
        # Generate style prompt using combined analysis
        base_tts_prompt = self._create_base_tts_prompt(language_code)
        style_guidelines = self._analyze_speaker_notes_to_style(
            combined_notes.strip(), combined_content.strip()
        )
        
        try:
            tts_prompt = self.prompt_rewriter.rewrite_tts_prompt(
                base_tts_prompt, style_guidelines
            )
            
            if len(tts_prompt.encode('utf-8')) > 3500:
                logger.warning(f"Presentation style prompt too long, using concise version")
                tts_prompt = self._create_concise_prompt(style_guidelines, language_code)
            
            # Cache for entire presentation
            self._style_cache[cache_key] = tts_prompt
            logger.info(f"✓ Presentation style analyzed and cached ({len(tts_prompt)} chars)")
            return tts_prompt
            
        except Exception as e:
            logger.warning(f"Presentation style analysis failed, using fallback: {e}")
            fallback_prompt = self._create_concise_prompt(style_guidelines, language_code)
            self._style_cache[cache_key] = fallback_prompt
            return fallback_prompt
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_presentations": len(self._style_cache),
            "cache_keys": list(self._style_cache.keys())
        }