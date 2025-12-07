"""Tests for AgentManager."""

import pytest
from unittest.mock import Mock, patch

from services.agent_manager import AgentManager


class TestAgentManager:
    """Tests for AgentManager class."""
    
    def test_initialization(self):
        """Test AgentManager initialization."""
        manager = AgentManager()
        
        assert manager._agents == {}
        assert manager._initialized is False
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_initialize_agents(self, mock_prompt, mock_llm_agent):
        """Test agent initialization."""
        manager = AgentManager()
        
        # Mock prompt attributes
        mock_prompt.AUDITOR_PROMPT = "auditor prompt"
        mock_prompt.ANALYST_PROMPT = "analyst prompt"
        mock_prompt.WRITER_PROMPT = "writer prompt"
        mock_prompt.SUPERVISOR_PROMPT = "supervisor prompt"
        mock_prompt.OVERVIEWER_PROMPT = "overviewer prompt"
        mock_prompt.DESIGNER_PROMPT = "designer prompt"
        mock_prompt.TRANSLATOR_PROMPT = "translator prompt"
        mock_prompt.IMAGE_TRANSLATOR_PROMPT = "image translator prompt"
        mock_prompt.VIDEO_GENERATOR_PROMPT = "video generator prompt"
        mock_prompt.REFINER_PROMPT = "refiner prompt"
        
        manager.initialize_agents()
        
        assert manager._initialized is True
        assert len(manager._agents) == 10
        assert "supervisor" in manager._agents
        assert "analyst" in manager._agents
        assert "writer" in manager._agents
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_get_agent(self, mock_prompt, mock_llm_agent):
        """Test getting an agent."""
        manager = AgentManager()
        
        # Mock prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        manager.initialize_agents()
        
        agent = manager.get_agent("supervisor")
        assert agent is not None
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_get_agent_not_found(self, mock_prompt, mock_llm_agent):
        """Test getting non-existent agent."""
        manager = AgentManager()
        
        # Mock prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        manager.initialize_agents()
        
        agent = manager.get_agent("nonexistent")
        assert agent is None
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_lazy_initialization(self, mock_prompt, mock_llm_agent):
        """Test lazy initialization on first get_agent call."""
        manager = AgentManager()
        
        # Mock prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        assert manager._initialized is False
        
        manager.get_agent("supervisor")
        
        assert manager._initialized is True
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_getter_methods(self, mock_prompt, mock_llm_agent):
        """Test specific getter methods."""
        manager = AgentManager()
        
        # Mock prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        manager.initialize_agents()
        
        assert manager.get_supervisor() is not None
        assert manager.get_analyst() is not None
        assert manager.get_writer() is not None
        assert manager.get_auditor() is not None
        assert manager.get_overviewer() is not None
        assert manager.get_designer() is not None
        assert manager.get_translator() is not None
        assert manager.get_image_translator() is not None
        assert manager.get_video_generator() is not None
        assert manager.get_refiner() is not None
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_is_initialized_property(self, mock_prompt, mock_llm_agent):
        """Test is_initialized property."""
        manager = AgentManager()
        
        assert manager.is_initialized is False
        
        # Mock prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        manager.initialize_agents()
        
        assert manager.is_initialized is True
    
    @patch('services.agent_manager.LlmAgent')
    @patch('services.agent_manager.prompt')
    def test_double_initialization(self, mock_prompt, mock_llm_agent):
        """Test that double initialization is handled gracefully."""
        manager = AgentManager()
        
        # Mock prompts
        for attr in ['AUDITOR_PROMPT', 'ANALYST_PROMPT', 'WRITER_PROMPT',
                     'SUPERVISOR_PROMPT', 'OVERVIEWER_PROMPT', 'DESIGNER_PROMPT',
                     'TRANSLATOR_PROMPT', 'IMAGE_TRANSLATOR_PROMPT',
                     'VIDEO_GENERATOR_PROMPT', 'REFINER_PROMPT']:
            setattr(mock_prompt, attr, f"{attr.lower()}")
        
        manager.initialize_agents()
        first_count = len(manager._agents)
        
        # Try to initialize again
        manager.initialize_agents()
        second_count = len(manager._agents)
        
        # Should not create duplicate agents
        assert first_count == second_count
