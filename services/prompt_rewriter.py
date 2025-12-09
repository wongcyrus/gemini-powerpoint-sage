"""Prompt rewriter service for integrating styles into agent prompts."""

import logging
from typing import Dict, Any
from google.adk.runners import Runner

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
            runner = Runner(agent=self.rewriter_agent)
            result = runner.run(rewrite_request)
            rewritten = result.text.strip()
            
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
            logger.warning("Falling back to simple concatenation")
            return self._fallback_designer_rewrite(base_prompt)
    
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

Please rewrite the base prompt to deeply integrate the speaker style guidelines throughout the instructions."""
        
        try:
            runner = Runner(agent=self.rewriter_agent)
            result = runner.run(rewrite_request)
            rewritten = result.text.strip()
            
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
            logger.warning("Falling back to simple concatenation")
            return self._fallback_writer_rewrite(base_prompt)
    
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
            runner = Runner(agent=self.rewriter_agent)
            result = runner.run(rewrite_request)
            rewritten = result.text.strip()
            
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
            logger.warning("Falling back to simple concatenation")
            return self._fallback_title_generator_rewrite(base_prompt)
    
    def _fallback_designer_rewrite(self, base_prompt: str) -> str:
        """Fallback method for designer prompt rewriting."""
        return f"""{base_prompt}

╔══════════════════════════════════════════════════════════════════════════════╗
║                          MANDATORY VISUAL STYLE                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

{self.visual_style}

🎨 STYLE APPLICATION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. EVERY slide MUST embody this visual style completely
2. Color schemes, typography, and layouts MUST match the style description
3. Visual elements (icons, shapes, backgrounds) MUST align with the style
4. If the style specifies particular aesthetics, they are MANDATORY
5. Consistency across all slides is CRITICAL - maintain the style throughout

⚠️  CRITICAL: This is not a suggestion - this is the REQUIRED visual language.
    Deviation from this style is considered a failure to follow instructions.
"""
    
    def _fallback_writer_rewrite(self, base_prompt: str) -> str:
        """Fallback method for writer prompt rewriting."""
        return f"""{base_prompt}

╔══════════════════════════════════════════════════════════════════════════════╗
║                          MANDATORY SPEAKER STYLE                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

{self.speaker_style}

🎤 STYLE APPLICATION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. EVERY speaker note MUST be written in this exact speaking style
2. Vocabulary, tone, and phrasing MUST match the style description precisely
3. Sentence structure and rhythm MUST reflect the speaker's personality
4. If the style includes specific terminology or expressions, USE THEM
5. The speaker's voice should be unmistakable in every sentence

⚠️  CRITICAL: You are not writing generic notes - you are channeling THIS speaker.
    Every word should sound like it comes from their mouth, not yours.
"""
    
    def _fallback_title_generator_rewrite(self, base_prompt: str) -> str:
        """Fallback method for title generator prompt rewriting."""
        return f"""{base_prompt}

╔══════════════════════════════════════════════════════════════════════════════╗
║                    MANDATORY SPEAKER STYLE FOR TITLES                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

{self.speaker_style}

🏷️  TITLE STYLE RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Titles MUST reflect the speaker's vocabulary and terminology
2. Tone and energy level MUST match the speaker style
3. If the style uses specific jargon or expressions, incorporate them
4. Title phrasing should feel natural coming from this speaker
5. Maintain consistency with the speaker notes' voice

⚠️  CRITICAL: Titles are the first thing audiences see - they must immediately
    establish the speaker's unique voice and perspective.
"""
    
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
