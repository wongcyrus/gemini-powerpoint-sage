"""TTS Style Adapter for contextual speech generation."""

import logging
from typing import Optional, Dict, List, Any
from core.domain.tts import StyleContext, PresentationType
from services.prompt_rewriter import PromptRewriter

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
        return f"""You are a professional speaker delivering presentation content in {language_code}. 
Your goal is to communicate clearly and effectively to your audience. 
Speak the following content with appropriate tone and delivery."""
    
    def _analyze_speaker_notes_to_style(
        self, 
        speaker_notes: str, 
        slide_content: str
    ) -> str:
        """
        Convert speaker notes into style guidelines format.
        This creates the style input for the PromptRewriter system.
        """
        if not speaker_notes or not speaker_notes.strip():
            return self._get_default_professional_style()
        
        # Analyze the speaker notes to extract style information
        style_analysis = self._extract_style_indicators(speaker_notes, slide_content)
        
        # Convert analysis to style guidelines format
        style_guidelines = f"""SPEAKING STYLE ANALYSIS:

Detected Tone: {style_analysis['tone']}
Pace Indicators: {style_analysis['pace']}
Emphasis Points: {', '.join(style_analysis['emphasis_words']) if style_analysis['emphasis_words'] else 'None'}
Emotional Context: {', '.join(style_analysis['emotions']) if style_analysis['emotions'] else 'Neutral'}
Presentation Type: {style_analysis['presentation_type'].value}

STYLE GUIDELINES:
{style_analysis['style_description']}

DELIVERY INSTRUCTIONS:
{style_analysis['delivery_instructions']}"""
        
        return style_guidelines
    
    def _extract_style_indicators(self, speaker_notes: str, slide_content: str) -> Dict:
        """Extract style indicators from speaker notes using pattern matching."""
        normalized_notes = speaker_notes.lower().strip()
        normalized_content = slide_content.lower().strip()
        
        # Style patterns for tone detection
        style_patterns = {
            "formal": ["formal", "professional", "academic", "official", "structured"],
            "casual": ["casual", "informal", "conversational", "friendly", "relaxed"],
            "enthusiastic": ["exciting", "energetic", "passionate", "dynamic", "enthusiastic"],
            "technical": ["technical", "detailed", "precise", "step-by-step", "systematic"],
            "narrative": ["story", "narrative", "journey", "experience", "example"]
        }
        
        # Detect dominant tone
        tone_scores = {}
        for tone, patterns in style_patterns.items():
            score = sum(1 for pattern in patterns 
                       if pattern in normalized_notes or pattern in normalized_content)
            if score > 0:
                tone_scores[tone] = score
        
        dominant_tone = max(tone_scores, key=tone_scores.get) if tone_scores else "professional"
        
        # Calculate confidence based on pattern matches
        total_patterns = sum(len(patterns) for patterns in style_patterns.values())
        total_matches = sum(tone_scores.values())
        confidence_score = min(0.9, max(0.3, total_matches / 10))  # Scale to 0.3-0.9 range
        
        # Detect pace
        pace = "normal"
        if any(word in normalized_notes for word in ["slowly", "carefully", "pause", "deliberate"]):
            pace = "slow"
        elif any(word in normalized_notes for word in ["quickly", "rapidly", "brief", "fast"]):
            pace = "fast"
        
        # Extract emphasis words
        emphasis_words = []
        emphasis_triggers = ["important", "key", "critical", "emphasize", "highlight", "focus"]
        for trigger in emphasis_triggers:
            if trigger in normalized_notes:
                # Simple extraction of nearby words
                words = normalized_notes.split()
                for i, word in enumerate(words):
                    if trigger in word:
                        # Look for words after the trigger
                        for j in range(i + 1, min(i + 4, len(words))):
                            next_word = words[j].strip('.,!?:;')
                            if len(next_word) > 2 and next_word not in ['the', 'and', 'or', 'but', 'is', 'are']:
                                emphasis_words.append(next_word)
                                break
        
        # Remove duplicates and limit to top 3
        emphasis_words = list(dict.fromkeys(emphasis_words))[:3]
        
        # Detect emotions
        emotions = []
        emotion_patterns = {
            "confident": ["confident", "certain", "sure", "definite"],
            "enthusiastic": ["excited", "thrilled", "amazing", "fantastic"],
            "cautious": ["careful", "consider", "might", "perhaps"],
            "urgent": ["urgent", "critical", "immediately", "must"]
        }
        
        for emotion, patterns in emotion_patterns.items():
            if any(pattern in normalized_notes for pattern in patterns):
                emotions.append(emotion)
        
        # Detect presentation type
        presentation_type = self._detect_presentation_type(normalized_notes, normalized_content)
        
        # Create style description
        style_descriptions = {
            "formal": "Professional, authoritative, and structured delivery appropriate for business or academic settings.",
            "casual": "Friendly, conversational tone as if speaking to colleagues or friends.",
            "enthusiastic": "Energetic, passionate delivery that conveys excitement and engagement.",
            "technical": "Precise, methodical explanation with emphasis on accuracy and clarity.",
            "narrative": "Storytelling approach with natural flow and engaging rhythm.",
            "professional": "Clear, professional delivery suitable for general presentation contexts."
        }
        
        # Create delivery instructions
        delivery_instructions = []
        if pace == "slow":
            delivery_instructions.append("Speak slowly and deliberately, allowing time for comprehension.")
        elif pace == "fast":
            delivery_instructions.append("Maintain a brisk but clear pace.")
        
        if emphasis_words:
            delivery_instructions.append(f"Give special emphasis to: {', '.join(emphasis_words)}")
        
        if emotions:
            delivery_instructions.append(f"Convey {emotions[0]} emotion in your delivery.")
        
        return {
            "tone": dominant_tone,
            "pace": pace,
            "emphasis_words": emphasis_words,
            "emotions": emotions,
            "presentation_type": presentation_type,
            "confidence_score": confidence_score,
            "style_description": style_descriptions.get(dominant_tone, style_descriptions["professional"]),
            "delivery_instructions": " ".join(delivery_instructions) if delivery_instructions else "Use clear, natural delivery."
        }
    
    def _detect_presentation_type(self, notes: str, content: str) -> PresentationType:
        """Detect presentation type from content."""
        type_indicators = {
            PresentationType.ACADEMIC: ["research", "study", "analysis", "theory", "methodology"],
            PresentationType.BUSINESS: ["strategy", "revenue", "market", "growth", "profit"],
            PresentationType.TRAINING: ["learn", "practice", "skill", "procedure", "exercise"],
            PresentationType.TECHNICAL: ["system", "implementation", "configuration", "architecture"],
            PresentationType.NARRATIVE: ["story", "journey", "experience", "example", "case"]
        }
        
        combined = f"{notes} {content}"
        type_scores = {}
        
        for ptype, indicators in type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in combined)
            if score > 0:
                type_scores[ptype] = score
        
        return max(type_scores, key=type_scores.get) if type_scores else PresentationType.BUSINESS
    
    def _get_default_professional_style(self) -> str:
        """Return default professional style guidelines."""
        return """SPEAKING STYLE ANALYSIS:

Detected Tone: professional
Pace Indicators: normal
Emphasis Points: None
Emotional Context: Neutral
Presentation Type: business

STYLE GUIDELINES:
Professional, clear, and authoritative delivery appropriate for business presentations. 
Maintain engagement while conveying information accurately and efficiently.

DELIVERY INSTRUCTIONS:
Use clear, natural delivery with appropriate pacing for comprehension."""
    
    def _create_fallback_prompt(self, style_guidelines: str, language_code: str) -> str:
        """Create fallback prompt when LLM rewriting fails."""
        logger.info("Using fallback TTS prompt generation")
        
        # Extract key style elements from guidelines
        lines = style_guidelines.split('\n')
        tone = "professional"
        pace = "normal"
        
        for line in lines:
            if "Detected Tone:" in line:
                tone = line.split(":", 1)[1].strip()
            elif "Pace Indicators:" in line:
                pace = line.split(":", 1)[1].strip()
        
        # Create simple fallback prompt
        pace_instruction = ""
        if pace == "slow":
            pace_instruction = "Speak slowly and clearly. "
        elif pace == "fast":
            pace_instruction = "Speak at a brisk but clear pace. "
        
        tone_instruction = ""
        if tone == "enthusiastic":
            tone_instruction = "Use an energetic and passionate tone. "
        elif tone == "casual":
            tone_instruction = "Use a friendly, conversational tone. "
        elif tone == "technical":
            tone_instruction = "Use a precise, methodical delivery. "
        elif tone == "formal":
            tone_instruction = "Use a professional, authoritative tone. "
        
        return f"""Speak in a {tone} manner appropriate for a presentation in {language_code}. 
        
{tone_instruction}{pace_instruction}Deliver the content with appropriate emphasis and natural flow for your audience."""
    
    def _create_concise_prompt(self, style_guidelines: str, language_code: str) -> str:
        """Create concise TTS prompt that stays under Gemini TTS length limits."""
        logger.info("Creating concise TTS prompt to stay under length limits")
        
        # Extract only the most essential style elements
        lines = style_guidelines.split('\n')
        tone = "professional"
        pace = "normal"
        emphasis_words = []
        emotions = []
        
        for line in lines:
            if "Detected Tone:" in line:
                tone = line.split(":", 1)[1].strip()
            elif "Pace Indicators:" in line:
                pace = line.split(":", 1)[1].strip()
            elif "Emphasis Points:" in line and "None" not in line:
                # Extract emphasis words if present
                emphasis_part = line.split(":", 1)[1].strip()
                if emphasis_part and emphasis_part != "None":
                    emphasis_words = [w.strip() for w in emphasis_part.split(",")][:2]  # Limit to 2
            elif "Emotional Context:" in line and "Neutral" not in line:
                emotion_part = line.split(":", 1)[1].strip()
                if emotion_part and emotion_part != "Neutral":
                    emotions = [emotion_part.lower()]
        
        # Build concise prompt components
        components = []
        
        # Base tone instruction (always include)
        tone_map = {
            "professional": "professional and clear",
            "enthusiastic": "energetic and passionate", 
            "casual": "friendly and conversational",
            "technical": "precise and methodical",
            "formal": "authoritative and structured",
            "narrative": "engaging storytelling"
        }
        base_tone = tone_map.get(tone, "clear and professional")
        components.append(f"Speak in a {base_tone} manner")
        
        # Add pace if not normal
        if pace == "slow":
            components.append("at a slow, deliberate pace")
        elif pace == "fast":
            components.append("at a brisk pace")
        
        # Add emotion if present
        if emotions:
            components.append(f"with {emotions[0]} emotion")
        
        # Add emphasis if present (limit to 1-2 words)
        if emphasis_words:
            components.append(f"emphasizing {emphasis_words[0]}")
        
        # Create final concise prompt
        prompt = ". ".join(components) + "."
        
        # Ensure it's under the limit (aim for under 200 chars for safety)
        if len(prompt) > 200:
            # Ultra-concise fallback
            prompt = f"Speak in a {base_tone} manner."
        
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