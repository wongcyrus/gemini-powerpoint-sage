"""Prompt rewriter service for integrating styles into agent prompts."""

import logging
import uuid
import time
from typing import Dict, Any
from google.adk.runners import InMemoryRunner

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
        
        # Import here to avoid circular imports
        from agents.prompt_rewriter import prompt_rewriter_agent
        self.rewriter_agent = prompt_rewriter_agent
        
        logger.info("=" * 80)
        logger.info("PROMPT REWRITER INITIALIZED (LLM-POWERED)")
        logger.info("=" * 80)
        logger.info(f"Visual Style: {self.visual_style[:100]}...")
        logger.info(f"Speaker Style: {self.speaker_style[:100]}...")
        logger.info("=" * 80)
    
    def _run_rewriter_with_retry(self, rewrite_request: str, session_prefix: str) -> str:
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
                runner.session_service.create_session_sync(
                    app_name="agents",
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Run the agent and collect response
                response_text = ""
                try:
                    for event in runner.run(
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
                        time.sleep(1)  # Brief delay before retry
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
                        time.sleep(2)  # Longer delay for empty responses
                        continue
                    else:
                        raise Exception(f"LLM returned insufficient content after {max_retries} attempts")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Delay before retry
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

═══════════════════════════════════════════════════════════════════════════════
STYLE INTEGRATION ({style_type.upper()})
═══════════════════════════════════════════════════════════════════════════════

{style_guidelines}

═══════════════════════════════════════════════════════════════════════════════
CRITICAL LANGUAGE ENFORCEMENT
═══════════════════════════════════════════════════════════════════════════════

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

═══════════════════════════════════════════════════════════════════════════════
VISUAL STYLE INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

{style_guidelines}

Apply these visual style guidelines throughout all design decisions and outputs."""
        
        logger.info(f"Fallback concatenation: {len(base_prompt)} + {len(style_guidelines)} chars")
        return enhanced_prompt
    
    def rewrite_designer_prompt(self, base_prompt: str) -> str:
        """
        Rewrite designer prompt with visual style deeply integrated using LLM.
        
        Args:
            base_prompt: Original designer prompt
            
        Returns:
            Rewritten prompt with visual style woven throughout
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING DESIGNER PROMPT WITH LLM")
        logger.info("=" * 80)
        
        rewrite_request = f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{self.visual_style}

STYLE_TYPE: visual

Please rewrite the base prompt to deeply integrate the visual style guidelines throughout the instructions."""
        
        try:
            rewritten = self._run_rewriter_with_retry(rewrite_request, "designer_rewriter")
            
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
            
        except Exception as e:
            logger.error(f"Failed to rewrite designer prompt with LLM: {e}")
            raise Exception(f"Designer prompt rewriting failed: {e}")
    
    def rewrite_writer_prompt(self, base_prompt: str) -> str:
        """
        Rewrite writer prompt with speaker style deeply integrated using LLM.
        
        Args:
            base_prompt: Original writer prompt
            
        Returns:
            Rewritten prompt with speaker style woven throughout
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING WRITER PROMPT WITH LLM")
        logger.info("=" * 80)
        
        rewrite_request = f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{self.speaker_style}

STYLE_TYPE: speaker

CRITICAL REQUIREMENT: When rewriting this prompt, you MUST include explicit language enforcement instructions that ensure the agent will always write in the target language specified by the user, regardless of any language examples in the style guidelines. The target language parameter should always override any language tendencies from the style.

Please rewrite the base prompt to deeply integrate the speaker style guidelines throughout the instructions while ensuring language compliance is enforced."""
        
        try:
            rewritten = self._run_rewriter_with_retry(rewrite_request, "writer_rewriter")
            
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
            
        except Exception as e:
            logger.error(f"Failed to rewrite writer prompt with LLM: {e}")
            raise Exception(f"Writer prompt rewriting failed: {e}")
    
    def rewrite_title_generator_prompt(self, base_prompt: str) -> str:
        """
        Rewrite title generator prompt with speaker style integrated using LLM.
        
        Args:
            base_prompt: Original title generator prompt
            
        Returns:
            Rewritten prompt with speaker style for title consistency
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING TITLE GENERATOR PROMPT WITH LLM")
        logger.info("=" * 80)
        
        rewrite_request = f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{self.speaker_style}

STYLE_TYPE: speaker

Please rewrite the base prompt to deeply integrate the speaker style guidelines throughout the instructions. This is for a title generator, so focus on how the style affects title creation."""
        
        try:
            rewritten = self._run_rewriter_with_retry(rewrite_request, "title_rewriter")
            
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
            
        except Exception as e:
            logger.error(f"Failed to rewrite title generator prompt with LLM: {e}")
            raise Exception(f"Title generator prompt rewriting failed: {e}")
    
    def rewrite_translator_prompt(self, base_prompt: str) -> str:
        """
        Rewrite translator prompt with speaker style integrated using LLM.
        
        Args:
            base_prompt: Original translator prompt
            
        Returns:
            Rewritten prompt with speaker style for style-aware translation
        """
        logger.info("\n" + "=" * 80)
        logger.info("REWRITING TRANSLATOR PROMPT WITH LLM")
        logger.info("=" * 80)
        
        rewrite_request = f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{self.speaker_style}

STYLE_TYPE: speaker

CRITICAL REQUIREMENT: This translator must not only translate language but also apply the speaker style. When translating speaker notes, the translator should:
1. Translate the content to the target language
2. Rewrite the translated content to match the speaker style (tone, vocabulary, personality)
3. Ensure the result sounds natural in the target language with the speaker's voice
4. Maintain informational accuracy while adapting stylistic elements

Please rewrite the base prompt to deeply integrate these style-aware translation capabilities."""
        
        try:
            rewritten = self._run_rewriter_with_retry(rewrite_request, "translator_rewriter")
            
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
            
        except Exception as e:
            logger.error(f"Failed to rewrite translator prompt with LLM: {e}")
            raise Exception(f"Translator prompt rewriting failed: {e}")
    
    def get_rewrite_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the rewrite configuration.
        
        Returns:
            Dictionary with rewrite statistics
        """
        return {
            "visual_style_length": len(self.visual_style),
            "speaker_style_length": len(self.speaker_style),
            "visual_style_preview": self.visual_style[:100] + "...",
            "speaker_style_preview": self.speaker_style[:100] + "...",
        }
    
    def log_rewrite_summary(self):
        """Log a summary of the rewrite configuration."""
        summary = self.get_rewrite_summary()
        logger.info("\n" + "╔" + "═" * 78 + "╗")
        logger.info("║" + " " * 25 + "REWRITE SUMMARY" + " " * 38 + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info(f"Visual Style Length: {summary['visual_style_length']} chars")
        logger.info(f"Speaker Style Length: {summary['speaker_style_length']} chars")
        logger.info(f"Visual Preview: {summary['visual_style_preview']}")
        logger.info(f"Speaker Preview: {summary['speaker_style_preview']}")
        logger.info("═" * 80 + "\n")