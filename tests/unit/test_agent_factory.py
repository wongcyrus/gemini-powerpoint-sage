"""Tests for agent factory."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.agent_factory import (
    create_designer_agent,
    create_writer_agent,
    create_title_generator_agent,
    create_all_agents,
)


class TestAgentFactory:
    """Tests for agent factory functions."""
    
    @pytest.mark.asyncio
    @patch('agents.agent_factory.LlmAgent')
    @patch('agents.agent_factory.PromptRewriter')
    async def test_create_designer_agent(self, mock_rewriter_class, mock_llm_agent):
        """Test designer agent creation with style."""
        # Setup mocks
        mock_rewriter = Mock()
        
        # Mock async method
        async def mock_rewrite(prompt):
            return "rewritten prompt"
        mock_rewriter.rewrite_designer_prompt = mock_rewrite
        
        mock_rewriter_class.return_value = mock_rewriter
        
        mock_agent = Mock()
        mock_llm_agent.return_value = mock_agent
        
        # Create agent
        visual_style = "Cyberpunk"
        agent = await create_designer_agent(visual_style)
        
        # Verify rewriter was created with style
        mock_rewriter_class.assert_called_once_with(visual_style=visual_style)
        
        # Verify agent was created with rewritten prompt
        mock_llm_agent.assert_called_once()
        call_kwargs = mock_llm_agent.call_args[1]
        assert call_kwargs['instruction'] == "rewritten prompt"
        assert call_kwargs['name'] == "slide_designer"
        
        assert agent == mock_agent
    
    @pytest.mark.asyncio
    @patch('agents.agent_factory.LlmAgent')
    @patch('agents.agent_factory.PromptRewriter')
    async def test_create_writer_agent(self, mock_rewriter_class, mock_llm_agent):
        """Test writer agent creation with style."""
        # Setup mocks
        mock_rewriter = Mock()
        
        # Mock async method
        async def mock_rewrite(prompt):
            return "rewritten prompt"
        mock_rewriter.rewrite_writer_prompt = mock_rewrite
        
        mock_rewriter_class.return_value = mock_rewriter
        
        mock_agent = Mock()
        mock_llm_agent.return_value = mock_agent
        
        # Create agent
        speaker_style = "Gundam Commander"
        agent = await create_writer_agent(speaker_style)
        
        # Verify rewriter was created with style
        mock_rewriter_class.assert_called_once_with(speaker_style=speaker_style)
        
        # Verify agent was created with rewritten prompt
        mock_llm_agent.assert_called_once()
        call_kwargs = mock_llm_agent.call_args[1]
        assert call_kwargs['instruction'] == "rewritten prompt"
        assert call_kwargs['name'] == "speech_writer"
        assert 'tools' in call_kwargs  # Should have google_search
        
        assert agent == mock_agent
    
    @pytest.mark.asyncio
    @patch('agents.agent_factory.LlmAgent')
    @patch('agents.agent_factory.PromptRewriter')
    async def test_create_title_generator_agent(self, mock_rewriter_class, mock_llm_agent):
        """Test title generator agent creation with style."""
        # Setup mocks
        mock_rewriter = Mock()
        
        # Mock async method
        async def mock_rewrite(prompt):
            return "rewritten prompt"
        mock_rewriter.rewrite_title_generator_prompt = mock_rewrite
        
        mock_rewriter_class.return_value = mock_rewriter
        
        mock_agent = Mock()
        mock_llm_agent.return_value = mock_agent
        
        # Create agent
        speaker_style = "Star Wars"
        agent = await create_title_generator_agent(speaker_style)
        
        # Verify rewriter was created with style
        mock_rewriter_class.assert_called_once_with(speaker_style=speaker_style)
        
        # Verify agent was created with rewritten prompt
        mock_llm_agent.assert_called_once()
        call_kwargs = mock_llm_agent.call_args[1]
        assert call_kwargs['instruction'] == "rewritten prompt"
        assert call_kwargs['name'] == "title_generator"
        
        assert agent == mock_agent
    
    @pytest.mark.asyncio
    @patch('agents.agent_factory.create_designer_agent')
    @patch('agents.agent_factory.create_writer_agent')
    @patch('agents.agent_factory.create_title_generator_agent')
    @patch('agents.agent_factory.LlmAgent')
    async def test_create_all_agents(
        self,
        mock_llm_agent,
        mock_create_title,
        mock_create_writer,
        mock_create_designer
    ):
        """Test creating all agents at once."""
        # Setup mocks for styled agents
        mock_designer = Mock(name="designer")
        mock_writer = Mock(name="writer")
        mock_title = Mock(name="title_generator")
        
        # Mock async factory methods
        async def mock_designer_fn(style): return mock_designer
        async def mock_writer_fn(style): return mock_writer
        async def mock_title_fn(style): return mock_title
        
        mock_create_designer.side_effect = mock_designer_fn
        mock_create_writer.side_effect = mock_writer_fn
        mock_create_title.side_effect = mock_title_fn
        
        # Mock other agents
        mock_llm_agent.return_value = Mock()
        
        # Create all agents
        visual_style = "Cyberpunk"
        speaker_style = "Gundam"
        agents = await create_all_agents(visual_style, speaker_style)
        
        # Verify styled agents were created with correct styles
        mock_create_designer.assert_called_once_with(visual_style)
        mock_create_writer.assert_called_once_with(speaker_style)
        mock_create_title.assert_called_once_with(speaker_style)
        
        # Verify all expected agents are in the dict
        expected_agents = [
            "supervisor",
            "analyst",
            "writer",
            "auditor",
            "overviewer",
            "designer",
            "translator",
            "image_translator",
            "video_generator",
            "refiner",
            "title_generator",
            "prompt_rewriter",
        ]
        
        for agent_name in expected_agents:
            assert agent_name in agents, f"Missing agent: {agent_name}"
        
        # Verify styled agents are in the dict
        assert agents["designer"] == mock_designer
        assert agents["writer"] == mock_writer
        assert agents["title_generator"] == mock_title
    
    @pytest.mark.asyncio
    @patch('agents.agent_factory.LlmAgent')
    @patch('agents.agent_factory.PromptRewriter')
    async def test_default_styles(self, mock_rewriter_class, mock_llm_agent):
        """Test that default style is 'Professional' when not specified."""
        mock_rewriter = Mock()
        
        async def mock_rewrite(prompt): return "rewritten"
        mock_rewriter.rewrite_designer_prompt = mock_rewrite
        
        mock_rewriter_class.return_value = mock_rewriter
        
        mock_llm_agent.return_value = Mock()
        
        # Create without specifying style
        await create_designer_agent()
        
        # Should use default "Professional"
        mock_rewriter_class.assert_called_once_with(visual_style="Professional")
