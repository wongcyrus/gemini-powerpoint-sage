"""Tests for agent prompts."""

import pytest
from agents.prompts import (
    SUPERVISOR_PROMPT,
    ANALYST_PROMPT,
    WRITER_PROMPT,
    AUDITOR_PROMPT,
    OVERVIEWER_PROMPT,
    DESIGNER_PROMPT,
    TRANSLATOR_PROMPT,
    IMAGE_TRANSLATOR_PROMPT,
    VIDEO_GENERATOR_PROMPT,
    TITLE_GENERATOR_PROMPT,
    REFINER_PROMPT,
)


class TestPrompts:
    """Test that all prompts are properly defined."""
    
    def test_all_prompts_exist(self):
        """Test that all prompts are defined and non-empty."""
        prompts = [
            ("SUPERVISOR_PROMPT", SUPERVISOR_PROMPT),
            ("ANALYST_PROMPT", ANALYST_PROMPT),
            ("WRITER_PROMPT", WRITER_PROMPT),
            ("AUDITOR_PROMPT", AUDITOR_PROMPT),
            ("OVERVIEWER_PROMPT", OVERVIEWER_PROMPT),
            ("DESIGNER_PROMPT", DESIGNER_PROMPT),
            ("TRANSLATOR_PROMPT", TRANSLATOR_PROMPT),
            ("IMAGE_TRANSLATOR_PROMPT", IMAGE_TRANSLATOR_PROMPT),
            ("VIDEO_GENERATOR_PROMPT", VIDEO_GENERATOR_PROMPT),
            ("TITLE_GENERATOR_PROMPT", TITLE_GENERATOR_PROMPT),
            ("REFINER_PROMPT", REFINER_PROMPT),
        ]
        
        for name, prompt in prompts:
            assert prompt is not None, f"{name} is None"
            assert isinstance(prompt, str), f"{name} is not a string"
            assert len(prompt) > 0, f"{name} is empty"
            assert len(prompt) > 50, f"{name} is too short (< 50 chars)"
    
    def test_prompts_have_instructions(self):
        """Test that prompts contain key instruction keywords."""
        # Supervisor should mention tools and workflow
        assert "tool" in SUPERVISOR_PROMPT.lower()
        assert "workflow" in SUPERVISOR_PROMPT.lower() or "sequence" in SUPERVISOR_PROMPT.lower()
        
        # Analyst should mention analysis
        assert "analyz" in ANALYST_PROMPT.lower()
        
        # Writer should mention writing or script
        assert "write" in WRITER_PROMPT.lower() or "script" in WRITER_PROMPT.lower()
        
        # Designer should mention image or visual
        assert "image" in DESIGNER_PROMPT.lower() or "visual" in DESIGNER_PROMPT.lower()
    
    def test_backward_compatibility(self):
        """Test that old import path still works."""
        from agents import prompt
        
        # Old module should have all prompts
        assert hasattr(prompt, "SUPERVISOR_PROMPT")
        assert hasattr(prompt, "ANALYST_PROMPT")
        assert hasattr(prompt, "WRITER_PROMPT")
        assert hasattr(prompt, "DESIGNER_PROMPT")
        
        # Backward-compatible module should still expose non-empty prompt text
        assert isinstance(prompt.SUPERVISOR_PROMPT, str) and len(prompt.SUPERVISOR_PROMPT) > 50
        assert isinstance(prompt.ANALYST_PROMPT, str) and len(prompt.ANALYST_PROMPT) > 50
        assert isinstance(prompt.WRITER_PROMPT, str) and len(prompt.WRITER_PROMPT) > 50
        assert isinstance(prompt.DESIGNER_PROMPT, str) and len(prompt.DESIGNER_PROMPT) > 50
    
    def test_prompts_are_strings(self):
        """Test that all prompts are strings, not bytes or other types."""
        prompts = [
            SUPERVISOR_PROMPT,
            ANALYST_PROMPT,
            WRITER_PROMPT,
            AUDITOR_PROMPT,
            OVERVIEWER_PROMPT,
            DESIGNER_PROMPT,
            TRANSLATOR_PROMPT,
            IMAGE_TRANSLATOR_PROMPT,
            VIDEO_GENERATOR_PROMPT,
            TITLE_GENERATOR_PROMPT,
            REFINER_PROMPT,
        ]
        
        for prompt in prompts:
            assert isinstance(prompt, str)
            assert not isinstance(prompt, bytes)
