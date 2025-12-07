"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, AsyncMock
from PIL import Image


@pytest.fixture
def mock_agent():
    """Create a mock LLM agent."""
    agent = Mock()
    agent.name = "test_agent"
    agent.model = "test-model"
    return agent


@pytest.fixture
def mock_async_agent():
    """Create a mock async LLM agent."""
    agent = AsyncMock()
    agent.name = "test_agent"
    agent.model = "test-model"
    return agent


@pytest.fixture
def sample_image():
    """Create a sample PIL image."""
    return Image.new("RGB", (800, 600), color="white")


@pytest.fixture
def sample_slide_data():
    """Create sample slide data."""
    return {
        "slide_idx": 1,
        "speaker_notes": "This is a test slide about security.",
        "status": "success",
    }


@pytest.fixture
def sample_progress_data():
    """Create sample progress data."""
    return {
        "slides": {
            "slide_1_abc123": {
                "slide_index": 1,
                "existing_notes_hash": "abc123",
                "original_notes": "Original notes",
                "note": "Generated notes",
                "status": "success",
            }
        },
        "global_context": "This presentation covers security topics.",
    }


@pytest.fixture
def sample_english_notes():
    """Create sample English notes."""
    return {
        1: "Welcome to this presentation on security.",
        2: "Today we will discuss authentication methods.",
        3: "Let's explore encryption techniques.",
    }


@pytest.fixture
def mock_supervisor_runner():
    """Create a mock supervisor runner."""
    runner = Mock()
    runner.run = Mock(return_value=iter([]))
    return runner


@pytest.fixture
def mock_tool_factory():
    """Create a mock tool factory."""
    factory = Mock()
    factory.last_writer_output = ""
    factory.reset_writer_output = Mock()
    factory.create_analyst_tool = Mock(return_value=AsyncMock())
    factory.create_writer_tool = Mock(return_value=AsyncMock())
    factory.create_auditor_tool = Mock(return_value=AsyncMock())
    factory.create_translator_tool = Mock(return_value=AsyncMock())
    return factory
