"""Tests for AgentManager (DEPRECATED - Legacy Code).

AgentManager is deprecated in favor of agent_factory.
These tests are kept for backward compatibility only.
"""

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
    def test_initialize_agents(self, mock_llm_agent):
        """Test agent initialization."""
        manager = AgentManager()
        
        manager.initialize_agents()
        
        assert manager._initialized is True
        assert len(manager._agents) == 10
        assert "supervisor" in manager._agents
        assert "analyst" in manager._agents
        assert "writer" in manager._agents
    
    @patch('services.agent_manager.LlmAgent')
    def test_get_agent(self, mock_llm_agent):
        """Test getting an agent."""
        manager = AgentManager()
        
        manager.initialize_agents()
        
        agent = manager.get_agent("supervisor")
        assert agent is not None
    
    @patch('services.agent_manager.LlmAgent')
    def test_get_agent_not_found(self, mock_llm_agent):
        """Test getting non-existent agent."""
        manager = AgentManager()
        
        manager.initialize_agents()
        
        agent = manager.get_agent("nonexistent")
        assert agent is None
    
    @patch('services.agent_manager.LlmAgent')
    def test_lazy_initialization(self, mock_llm_agent):
        """Test lazy initialization on first get_agent call."""
        manager = AgentManager()
        
        assert manager._initialized is False
        
        manager.get_agent("supervisor")
        
        assert manager._initialized is True
    
    @patch('services.agent_manager.LlmAgent')
    def test_getter_methods(self, mock_llm_agent):
        """Test specific getter methods."""
        manager = AgentManager()
        
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
    def test_is_initialized_property(self, mock_llm_agent):
        """Test is_initialized property."""
        manager = AgentManager()
        
        assert manager.is_initialized is False
        
        manager.initialize_agents()
        
        assert manager.is_initialized is True
    
    @patch('services.agent_manager.LlmAgent')
    def test_double_initialization(self, mock_llm_agent):
        """Test that double initialization is handled gracefully."""
        manager = AgentManager()
        
        manager.initialize_agents()
        first_count = len(manager._agents)
        
        # Try to initialize again
        manager.initialize_agents()
        second_count = len(manager._agents)
        
        # Should not create duplicate agents
        assert first_count == second_count
