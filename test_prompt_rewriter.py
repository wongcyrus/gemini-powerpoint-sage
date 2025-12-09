#!/usr/bin/env python3
"""Quick test for the prompt rewriter agent."""

import logging
from services.prompt_rewriter import PromptRewriter
from agents import prompt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_prompt_rewriter():
    """Test the prompt rewriter with sample styles."""
    
    # Sample styles
    visual_style = """
    Cyberpunk aesthetic with neon colors (electric blue, hot pink, purple).
    Dark backgrounds with glowing elements.
    Futuristic typography with sharp angles.
    Grid patterns and digital glitch effects.
    """
    
    speaker_style = """
    Energetic and enthusiastic tech evangelist.
    Uses phrases like "game-changer", "next-level", "revolutionary".
    Speaks in short, punchy sentences.
    Frequently uses rhetorical questions to engage audience.
    """
    
    print("\n" + "="*80)
    print("TESTING PROMPT REWRITER AGENT")
    print("="*80 + "\n")
    
    # Create rewriter
    rewriter = PromptRewriter(
        visual_style=visual_style,
        speaker_style=speaker_style
    )
    
    # Test designer prompt rewrite
    print("\n--- Testing Designer Prompt Rewrite ---\n")
    designer_rewritten = rewriter.rewrite_designer_prompt(prompt.DESIGNER_PROMPT[:500])
    print(f"Rewritten length: {len(designer_rewritten)} chars")
    print(f"Preview:\n{designer_rewritten[:300]}...\n")
    
    # Test writer prompt rewrite
    print("\n--- Testing Writer Prompt Rewrite ---\n")
    writer_rewritten = rewriter.rewrite_writer_prompt(prompt.WRITER_PROMPT[:500])
    print(f"Rewritten length: {len(writer_rewritten)} chars")
    print(f"Preview:\n{writer_rewritten[:300]}...\n")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_prompt_rewriter()
