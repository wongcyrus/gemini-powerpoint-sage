"""Prompt rewriter service for integrating styles into agent prompts."""

import logging
import uuid
import time
import asyncio
from typing import Dict, Any
from google.adk.runners import InMemoryRunner
from .prompt_cache import PromptCache

logger = logging.getLogger(__name__)


class PromptRewriter:
    """
    Rewrites agent prompts to deeply integrate visual and speaker styles.
    
    Uses an LLM agent to intelligently combine base prompts with style guidelines,
    weaving styles throughout the instructions for better adherence.
    """
    
    def __init__(self, visual_style: str = None, speaker_style: str = None):
        """
        Initialize the prompt rewriter.
        
        Args:
            visual_style: Visual style description for designer
            speaker_style: Speaking style description for writer/title generator
        """
        self.visual_style = visual_style or "Professional"
        self.speaker_style = speaker_style or "Professional"
        
        # Initialize cache system
        self.cache = PromptCache()
        
        # Import here to avoid circular imports
        from agents.prompt_rewriter import prompt_rewriter_agent
        self.rewriter_agent = prompt_rewriter_agent
        
        logger.info("=" * 80)
        logger.info("PROMPT REWRITER INITIALIZED (LLM-POWERED WITH CACHING)")
        logger.info("=" * 80)
        logger.info(f"Visual Style: {self.visual_style[:100]}...")
        logger.info(f"Speaker Style: {self.speaker_style[:100]}...")
        logger.info(f"Cache Status: {self.cache.get_cache_stats()}")
        logger.info("=" * 80)
    
    async def _run_rewriter_with_retry(self, rewrite_request: str, session_prefix: str) -> str:
        """
        Run the rewriter agent with retry logic and fallback to simple concatenation.
        
        Args:
            rewrite_request: The rewrite request to send to the LLM
            session_prefix: Prefix for session ID generation
            
        Returns:
            Rewritten prompt text
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                from google.genai import types
                
                # Create a fresh runner for each attempt to avoid session conflicts
                runner = InMemoryRunner(agent=self.rewriter_agent, app_name="agents")
                
                # Create proper Content object
                content = types.Content(
                    role='user', 
                    parts=[types.Part.from_text(text=rewrite_request)]
                )
                
                # Create unique session for each attempt
                user_id = f"rewriter_user_{uuid.uuid4().hex[:6]}"
                session_id = f"{session_prefix}_{attempt}_{uuid.uuid4().hex[:8]}"
                
                logger.debug(f"Attempt {attempt + 1}/{max_retries}: Using session {session_id}")
                
                # Explicitly create session to avoid "Session not found" error
                await runner.session_service.create_session(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Run the agent and collect response
                response_text = ""
                try:
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=content,
                    ):
                        if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    response_text += part.text
                except Exception as run_error:
                    logger.warning(f"Runner execution failed on attempt {attempt + 1}: {run_error}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        raise run_error
                
                rewritten = response_text.strip()
                
                # Check if rewriting actually produced content
                if rewritten and len(rewritten) > 50:  # Ensure we got substantial content
                    logger.info(f"✓ LLM rewriting successful on attempt {attempt + 1}")
                    return rewritten
                else:
                    logger.warning(f"LLM returned insufficient content on attempt {attempt + 1}: {len(rewritten)} chars")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Longer delay for empty responses
                        continue
                    else:
                        raise Exception(f"LLM returned insufficient content after {max_retries} attempts")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Delay before retry
                    continue
                else:
                    logger.warning(f"All {max_retries} attempts failed, falling back to simple concatenation")
                    return self._fallback_to_simple_concatenation(rewrite_request, session_prefix)
        
        # This should never be reached, but just in case
        return self._fallback_to_simple_concatenation(rewrite_request, session_prefix)
    
    def _fallback_to_simple_concatenation(self, rewrite_request: str, session_prefix: str) -> str:
        """
        Fallback method that does simple prompt concatenation when LLM rewriting fails.
        
        Args:
            rewrite_request: The original rewrite request
            session_prefix: Session prefix to determine prompt type
            
        Returns:
            Concatenated prompt with style integrated
        """
        logger.info(f"Using simple concatenation fallback for {session_prefix}")
        
        # Extract base prompt and style from the rewrite request
        lines = rewrite_request.split('\n')
        base_prompt = ""
        style_guidelines = ""
        style_type = ""
        
        current_section = None
        for line in lines:
            if line.startswith("BASE_PROMPT:"):
                current_section = "base"
                continue
            elif line.startswith("STYLE_GUIDELINES:"):
                current_section = "style"
                continue
            elif line.startswith("STYLE_TYPE:"):
                style_type = line.split(":", 1)[1].strip()
                current_section = None
                continue
            elif line.startswith("CRITICAL REQUIREMENT:") or line.startswith("Please rewrite"):
                current_section = None
                continue
            
            if current_section == "base":
                base_prompt += line + "\n"
            elif current_section == "style":
                style_guidelines += line + "\n"
        
        base_prompt = base_prompt.strip()
        style_guidelines = style_guidelines.strip()
        
        # Create enhanced prompt with style integration
        if "writer" in session_prefix or "translator" in session_prefix:
            # For speaker-related prompts, add strong language enforcement
            enhanced_prompt = f"""{base_prompt}

===============================================================================
STYLE INTEGRATION ({style_type.upper()})
===============================================================================

{style_guidelines}

===============================================================================
CRITICAL LANGUAGE ENFORCEMENT
===============================================================================

**MANDATORY LANGUAGE COMPLIANCE:**
- ALWAYS write in the target language specified by the user
- The target language parameter OVERRIDES any language examples in the style
- If English is requested, write 100% in English regardless of style examples
- If Chinese is requested, write 100% in Chinese regardless of style examples
- Style examples are for tone/voice reference only, NOT language selection

**STYLE APPLICATION:**
- Apply the speaking style, tone, and personality from the guidelines above
- Use the vocabulary patterns and phrasing style shown in the examples
- Maintain the character persona and voice described in the style
- Ensure the output sounds natural in the TARGET LANGUAGE with the style applied

Remember: Language compliance is MANDATORY. Style is applied WITHIN the target language."""
        else:
            # For visual prompts, simpler integration
            enhanced_prompt = f"""{base_prompt}

===============================================================================
VISUAL STYLE INTEGRATION
===============================================================================

{style_guidelines}

Apply these visual style guidelines throughout all design decisions and outputs."""
        
        logger.info(f"Fallback concatenation: {len(base_prompt)} + {len(style_guidelines)} chars")
        return enhanced_prompt
    
    async def _rewrite_with_cache(self, base_prompt: str, style_guidelines: str, prompt_type: str) -> str:
        """
        Rewrite a prompt with caching support and comprehensive error handling.
        
        Args:
            base_prompt: The original prompt text
            style_guidelines: Style guidelines to integrate
            prompt_type: Type of prompt (designer, writer, title, translator)
            
        Returns:
            Rewritten prompt text
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self.cache.generate_cache_key(base_prompt, style_guidelines, prompt_type)
            
            # Try to get cached result
            cached_result = self.cache.get_cached_prompt(cache_key)
            if cached_result:
                elapsed = time.time() - start_time
                logger.info(f"✓ Cache hit for {prompt_type}: {elapsed:.3f}s")
                return cached_result
            
            # Cache miss - perform LLM rewriting
            logger.info(f"Cache miss for {prompt_type} - performing LLM rewriting")
            
            # Create appropriate rewrite request based on prompt type
            if prompt_type == "tts":
                rewrite_request = f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{style_guidelines}

STYLE_TYPE: tts_speech

CRITICAL REQUIREMENT: This is for text-to-speech generation using Gemini TTS. The output should be a natural language instruction that tells the TTS engine how to speak the content.

IMPORTANT TONE CONSTRAINT: The tone MUST be exactly one of these values: 'professional', 'casual', 'enthusiastic', 'technical', or 'narrative'. Do not use any other tone words.

IMPORTANT LENGTH CONSTRAINT: The final output MUST be under 500 characters total. Be extremely concise.

Focus on:
1. Choose the most appropriate tone from: professional, casual, enthusiastic, technical, narrative
2. Pace and rhythm instructions (slow, normal, fast)
3. Emphasis and emotional expression
4. Language-appropriate cultural considerations

Please rewrite the base prompt to create a SHORT, natural language TTS instruction that incorporates the speaking style from the guidelines. Keep it under 500 characters and use only the allowed tone values."""
            else:
                rewrite_request = f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{style_guidelines}

STYLE_TYPE: {"visual" if prompt_type == "designer" else "speaker"}

Please rewrite the base prompt to deeply integrate the style guidelines throughout the instructions."""
            
            try:
                # Perform LLM rewriting
                rewritten = await self._run_rewriter_with_retry(rewrite_request, f"{prompt_type}_rewriter")
                
                # Store in cache (ignore cache failures)
                try:
                    self.cache.store_prompt(cache_key, rewritten, prompt_type, base_prompt, style_guidelines)
                except Exception as cache_error:
                    logger.warning(f"Failed to cache result for {prompt_type}: {cache_error}")
                
                elapsed = time.time() - start_time
                logger.info(f"✓ LLM rewriting completed for {prompt_type}: {elapsed:.3f}s")
                return rewritten
                
            except Exception as llm_error:
                logger.warning(f"LLM rewriting failed for {prompt_type}: {llm_error}")
                # Fall back to simple concatenation
                fallback_result = self._fallback_to_simple_concatenation(rewrite_request, f"{prompt_type}_rewriter")
                
                # Try to cache the fallback result (ignore failures)
                try:
                    self.cache.store_prompt(cache_key, fallback_result, prompt_type, base_prompt, style_guidelines)
                except Exception as cache_error:
                    logger.debug(f"Failed to cache fallback result for {prompt_type}: {cache_error}")
                
                elapsed = time.time() - start_time
                logger.info(f"✓ Fallback rewriting completed for {prompt_type}: {elapsed:.3f}s")
                return fallback_result
                
        except Exception as critical_error:
            # Critical error - return basic concatenation without caching
            logger.error(f"Critical error in prompt rewriting for {prompt_type}: {critical_error}")
            logger.info(f"Using emergency fallback for {prompt_type}")
            
            # Emergency fallback - simple concatenation
            emergency_result = f"""{base_prompt}

===============================================================================
STYLE INTEGRATION ({prompt_type.upper()})
===============================================================================

{style_guidelines}

Apply these style guidelines throughout all operations."""
            
            elapsed = time.time() - start_time
            logger.warning(f"✓ Emergency fallback completed for {prompt_type}: {elapsed:.3f}s")
            return emergency_result
    
    async def rewrite_designer_prompt(self, base_prompt: str) -> str:
        """
        Rewrite designer prompt with visual style deeply integrated using LLM.
        
        Args:
            base_prompt: Original designer prompt
            
        Returns:
            Rewritten prompt with visual style woven throughout
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING DESIGNER PROMPT")
        logger.info("=" * 80)
        
        rewritten = await self._rewrite_with_cache(base_prompt, self.visual_style, "designer")
        
        logger.info(f"Original prompt length: {len(base_prompt)} chars")
        logger.info(f"Rewritten prompt length: {len(rewritten)} chars")
        logger.info(f"Style integration: {len(self.visual_style)} chars of style content")
        logger.info("✓ Designer prompt rewritten successfully")
        logger.info("=" * 80 + "\n")
        
        # Log full rewritten prompt for debugging
        logger.debug("FULL REWRITTEN DESIGNER PROMPT:")
        logger.debug("-" * 80)
        logger.debug(rewritten)
        logger.debug("-" * 80)
        
        return rewritten
    
    async def rewrite_writer_prompt(self, base_prompt: str) -> str:
        """
        Rewrite writer prompt with speaker style deeply integrated using LLM.
        
        Args:
            base_prompt: Original writer prompt
            
        Returns:
            Rewritten prompt with speaker style woven throughout
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING WRITER PROMPT")
        logger.info("=" * 80)
        
        rewritten = await self._rewrite_with_cache(base_prompt, self.speaker_style, "writer")
        
        logger.info(f"Original prompt length: {len(base_prompt)} chars")
        logger.info(f"Rewritten prompt length: {len(rewritten)} chars")
        logger.info(f"Style integration: {len(self.speaker_style)} chars of style content")
        logger.info("✓ Writer prompt rewritten successfully")
        logger.info("=" * 80 + "\n")
        
        logger.debug("FULL REWRITTEN WRITER PROMPT:")
        logger.debug("-" * 80)
        logger.debug(rewritten)
        logger.debug("-" * 80)
        
        return rewritten
    
    async def rewrite_title_generator_prompt(self, base_prompt: str) -> str:
        """
        Rewrite title generator prompt with speaker style integrated using LLM.
        
        Args:
            base_prompt: Original title generator prompt
            
        Returns:
            Rewritten prompt with speaker style for title consistency
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING TITLE GENERATOR PROMPT")
        logger.info("=" * 80)
        
        rewritten = await self._rewrite_with_cache(base_prompt, self.speaker_style, "title")
        
        logger.info(f"Original prompt length: {len(base_prompt)} chars")
        logger.info(f"Rewritten prompt length: {len(rewritten)} chars")
        logger.info(f"Style integration: {len(self.speaker_style)} chars of style content")
        logger.info("✓ Title generator prompt rewritten successfully")
        logger.info("=" * 80 + "\n")
        
        logger.debug("FULL REWRITTEN TITLE GENERATOR PROMPT:")
        logger.debug("-" * 80)
        logger.debug(rewritten)
        logger.debug("-" * 80)
        
        return rewritten
    
    async def rewrite_translator_prompt(self, base_prompt: str) -> str:
        """
        Rewrite translator prompt with speaker style integrated using LLM.
        
        Args:
            base_prompt: Original translator prompt
            
        Returns:
            Rewritten prompt with speaker style for style-aware translation
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING TRANSLATOR PROMPT")
        logger.info("=" * 80)
        
        rewritten = await self._rewrite_with_cache(base_prompt, self.speaker_style, "translator")
        
        logger.info(f"Original prompt length: {len(base_prompt)} chars")
        logger.info(f"Rewritten prompt length: {len(rewritten)} chars")
        logger.info(f"Style integration: {len(self.speaker_style)} chars of style content")
        logger.info("✓ Translator prompt rewritten successfully")
        logger.info("=" * 80 + "\n")
        
        logger.debug("FULL REWRITTEN TRANSLATOR PROMPT:")
        logger.debug("-" * 80)
        logger.debug(rewritten)
        logger.debug("-" * 80)
        
        return rewritten
    
    def get_rewrite_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the rewrite configuration.
        
        Returns:
            Dictionary with rewrite statistics
        """
        cache_stats = self.cache.get_cache_stats()
        return {
            "visual_style_length": len(self.visual_style),
            "speaker_style_length": len(self.speaker_style),
            "visual_style_preview": self.visual_style[:100] + "...",
            "speaker_style_preview": self.speaker_style[:100] + "...",
            "cache_stats": cache_stats,
        }
    
    async def rewrite_tts_prompt(self, base_prompt: str, style_guidelines: str) -> str:
        """
        Rewrite TTS prompt with style guidelines integrated using LLM with caching.
        
        Args:
            base_prompt: Original TTS prompt
            style_guidelines: TTS style guidelines from speaker notes analysis
            
        Returns:
            Rewritten prompt with TTS style integrated
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING TTS PROMPT WITH LLM")
        logger.info("=" * 80)
        
        # Use the centralized caching method with TTS-specific customization
        rewritten = await self._rewrite_with_cache(base_prompt, style_guidelines, "tts")
        
        # Apply TTS-specific post-processing
        rewritten = self._validate_and_fix_tts_tone(rewritten)
        
        # Check if rewritten prompt is too long for Gemini TTS
        if len(rewritten.encode('utf-8')) > 3500:  # 4000 byte limit with buffer
            logger.warning(f"Rewritten TTS prompt too long ({len(rewritten)} chars), using concise fallback")
            rewritten = self._create_concise_tts_prompt(style_guidelines)
        
        logger.info(f"Original TTS prompt length: {len(base_prompt)} chars")
        logger.info(f"Rewritten TTS prompt length: {len(rewritten)} chars")
        logger.info(f"Style integration: {len(style_guidelines)} chars of style content")
        logger.info("✓ TTS prompt rewritten successfully")
        logger.info("=" * 80 + "\n")
        
        # Log full rewritten prompt for debugging
        logger.debug("FULL REWRITTEN TTS PROMPT:")
        logger.debug("-" * 80)
        logger.debug(rewritten)
        logger.debug("-" * 80)
        
        return rewritten
    
    def _validate_and_fix_tts_tone(self, tts_prompt: str) -> str:
        """
        Validate and fix TTS tone to ensure it uses only allowed values.
        
        Args:
            tts_prompt: The TTS prompt to validate
            
        Returns:
            Fixed TTS prompt with valid tone
        """
        valid_tones = ["professional", "casual", "enthusiastic", "technical", "narrative"]
        
        # Check if prompt contains any valid tone
        found_tone = None
        for tone in valid_tones:
            if tone in tts_prompt.lower():
                found_tone = tone
                break
        
        if not found_tone:
            # Default to professional tone
            logger.warning("No valid tone found in TTS prompt, defaulting to professional")
            return f"Speak in a professional manner. {tts_prompt}"
        
        return tts_prompt
    
    def _create_tts_fallback_prompt(self, base_prompt: str, style_guidelines: str) -> str:
        """
        Create fallback TTS prompt when LLM rewriting fails.
        
        Args:
            base_prompt: Original TTS prompt
            style_guidelines: Style guidelines
            
        Returns:
            Simple fallback TTS prompt
        """
        logger.info("Creating TTS fallback prompt")
        
        # Extract key style elements from guidelines
        lines = style_guidelines.split('\n')
        tone = "professional"
        pace = "normal"
        
        for line in lines:
            if "Detected Tone:" in line:
                detected = line.split(":", 1)[1].strip().lower()
                if detected in ["professional", "casual", "enthusiastic", "technical", "narrative"]:
                    tone = detected
            elif "Pace Indicators:" in line:
                pace_part = line.split(":", 1)[1].strip().lower()
                if pace_part in ["slow", "fast"]:
                    pace = pace_part
        
        # Create simple fallback
        pace_instruction = ""
        if pace == "slow":
            pace_instruction = " Speak slowly and clearly."
        elif pace == "fast":
            pace_instruction = " Speak at a brisk but clear pace."
        
        fallback = f"Speak in a {tone} manner.{pace_instruction}"
        
        logger.info(f"Created TTS fallback prompt: {len(fallback)} chars")
        return fallback
    
    def _create_concise_tts_prompt(self, style_guidelines: str) -> str:
        """
        Create concise TTS prompt that stays under Gemini TTS length limits.
        
        Args:
            style_guidelines: Style guidelines to extract key elements from
            
        Returns:
            Concise TTS prompt under 500 characters
        """
        logger.info("Creating concise TTS prompt to stay under length limits")
        
        # Extract only the most essential style elements
        lines = style_guidelines.split('\n')
        tone = "professional"
        pace = "normal"
        emphasis_words = []
        emotions = []
        
        for line in lines:
            if "Detected Tone:" in line:
                tone = line.split(":", 1)[1].strip().lower()
            elif "Pace Indicators:" in line:
                pace = line.split(":", 1)[1].strip().lower()
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

    def log_rewrite_summary(self):
        """Log a summary of the rewrite configuration and performance."""
        summary = self.get_rewrite_summary()
        cache_stats = summary.get('cache_stats', {})
        
        logger.info("\n" + "+" + "=" * 78 + "+")
        logger.info("|" + " " * 25 + "REWRITE SUMMARY" + " " * 38 + "|")
        logger.info("+" + "=" * 78 + "+")
        logger.info(f"Visual Style Length: {summary['visual_style_length']} chars")
        logger.info(f"Speaker Style Length: {summary['speaker_style_length']} chars")
        logger.info(f"Visual Preview: {summary['visual_style_preview']}")
        logger.info(f"Speaker Preview: {summary['speaker_style_preview']}")
        
        if cache_stats.get('enabled'):
            logger.info("+" + "-" * 78 + "+")
            logger.info("|" + " " * 25 + "CACHE PERFORMANCE" + " " * 36 + "|")
            logger.info("+" + "-" * 78 + "+")
            logger.info(f"Cache Enabled: {cache_stats.get('enabled', False)}")
            logger.info(f"Total Entries: {cache_stats.get('total_entries', 0)}")
            logger.info(f"Cache Hits: {cache_stats.get('cache_hits', 0)}")
            logger.info(f"Cache Misses: {cache_stats.get('cache_misses', 0)}")
            logger.info(f"Hit Rate: {cache_stats.get('hit_rate', 0):.1%}")
            logger.info(f"Cache Size: {cache_stats.get('total_size_mb', 0):.2f}MB / {cache_stats.get('max_size_mb', 0):.0f}MB")
            logger.info(f"Cache Directory: {cache_stats.get('cache_dir', 'N/A')}")
        else:
            logger.info("Cache: DISABLED")
            
        logger.info("=" * 80 + "\n")
    
    def log_performance_metrics(self):
        """Log detailed performance metrics for monitoring."""
        cache_stats = self.cache.get_cache_stats()
        
        if cache_stats.get('enabled'):
            total_requests = cache_stats.get('cache_hits', 0) + cache_stats.get('cache_misses', 0)
            hit_rate = cache_stats.get('hit_rate', 0)
            
            logger.info("PERFORMANCE METRICS:")
            logger.info(f"  Total Requests: {total_requests}")
            logger.info(f"  Cache Hit Rate: {hit_rate:.1%}")
            logger.info(f"  Cache Efficiency: {'EXCELLENT' if hit_rate > 0.8 else 'GOOD' if hit_rate > 0.5 else 'POOR'}")
            logger.info(f"  Storage Used: {cache_stats.get('total_size_mb', 0):.2f}MB")
            
            if hit_rate > 0.5:
                estimated_time_saved = cache_stats.get('cache_hits', 0) * 15  # Assume 15s saved per hit
                logger.info(f"  Estimated Time Saved: {estimated_time_saved}s ({estimated_time_saved/60:.1f} minutes)")
        else:
            logger.info("PERFORMANCE METRICS: Cache disabled - no performance benefits")