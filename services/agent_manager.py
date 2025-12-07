"""Agent management and registry."""

import logging
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

from config.constants import ModelConfig

logger = logging.getLogger(__name__)


class AgentManager:
    """Centralized agent management and initialization."""
    
    def __init__(self):
        """Initialize the agent manager."""
        self._agents: dict[str, LlmAgent] = {}
        self._initialized = False
    
    def initialize_agents(self) -> None:
        """Initialize all agents with their configurations."""
        if self._initialized:
            logger.warning("Agents already initialized")
            return
        
        # Import prompts
        from agents import prompt
        
        # Initialize agents
        self._agents["auditor"] = LlmAgent(
            name="auditor",
            model=ModelConfig.AUDITOR,
            description="Evaluates existing speaker notes quality.",
            instruction=prompt.AUDITOR_PROMPT,
        )
        
        self._agents["analyst"] = LlmAgent(
            name="slide_analyst",
            model=ModelConfig.ANALYST,
            description="Extracts insights from slide images.",
            instruction=prompt.ANALYST_PROMPT,
        )
        
        self._agents["writer"] = LlmAgent(
            name="speech_writer",
            model=ModelConfig.WRITER,
            description="Generates presentation scripts with context.",
            instruction=prompt.WRITER_PROMPT,
            tools=[google_search],
        )
        
        self._agents["supervisor"] = LlmAgent(
            name="supervisor",
            model=ModelConfig.SUPERVISOR,
            description="Orchestrates the slide generation workflow.",
            instruction=prompt.SUPERVISOR_PROMPT,
            tools=[
                AgentTool(agent=self._agents["auditor"]),
                AgentTool(agent=self._agents["writer"]),
            ],
        )
        
        self._agents["overviewer"] = LlmAgent(
            name="overviewer",
            model=ModelConfig.OVERVIEWER,
            description="Generates global presentation context.",
            instruction=prompt.OVERVIEWER_PROMPT,
        )
        
        self._agents["designer"] = LlmAgent(
            name="designer",
            model=ModelConfig.DESIGNER,
            description="Generates enhanced slide visuals.",
            instruction=prompt.DESIGNER_PROMPT,
        )
        
        self._agents["translator"] = LlmAgent(
            name="translator",
            model=ModelConfig.TRANSLATOR,
            description="Translates speaker notes to target languages.",
            instruction=prompt.TRANSLATOR_PROMPT,
        )
        
        self._agents["image_translator"] = LlmAgent(
            name="image_translator",
            model=ModelConfig.IMAGE_TRANSLATOR,
            description="Translates slide visuals to target languages.",
            instruction=prompt.IMAGE_TRANSLATOR_PROMPT,
        )
        
        self._agents["video_generator"] = LlmAgent(
            name="video_generator",
            model=ModelConfig.VIDEO_GENERATOR,
            description="Generates video prompts for slides.",
            instruction=prompt.VIDEO_GENERATOR_PROMPT,
        )
        
        self._agents["refiner"] = LlmAgent(
            name="refiner",
            model=ModelConfig.REFINER,
            description="Refines speaker notes for TTS.",
            instruction=prompt.REFINER_PROMPT,
        )
        
        self._initialized = True
        logger.info(f"Initialized {len(self._agents)} agents")
    
    def get_agent(self, role: str) -> Optional[LlmAgent]:
        """
        Get an agent by role.
        
        Args:
            role: Agent role name
            
        Returns:
            Agent instance or None if not found
        """
        if not self._initialized:
            self.initialize_agents()
        
        agent = self._agents.get(role)
        if not agent:
            logger.warning(f"Agent not found: {role}")
        return agent
    
    def get_supervisor(self) -> LlmAgent:
        """Get the supervisor agent."""
        return self.get_agent("supervisor")
    
    def get_analyst(self) -> LlmAgent:
        """Get the analyst agent."""
        return self.get_agent("analyst")
    
    def get_writer(self) -> LlmAgent:
        """Get the writer agent."""
        return self.get_agent("writer")
    
    def get_auditor(self) -> LlmAgent:
        """Get the auditor agent."""
        return self.get_agent("auditor")
    
    def get_overviewer(self) -> LlmAgent:
        """Get the overviewer agent."""
        return self.get_agent("overviewer")
    
    def get_designer(self) -> LlmAgent:
        """Get the designer agent."""
        return self.get_agent("designer")
    
    def get_translator(self) -> LlmAgent:
        """Get the translator agent."""
        return self.get_agent("translator")
    
    def get_image_translator(self) -> LlmAgent:
        """Get the image translator agent."""
        return self.get_agent("image_translator")
    
    def get_video_generator(self) -> LlmAgent:
        """Get the video generator agent."""
        return self.get_agent("video_generator")
    
    def get_refiner(self) -> LlmAgent:
        """Get the refiner agent."""
        return self.get_agent("refiner")
    
    @property
    def is_initialized(self) -> bool:
        """Check if agents are initialized."""
        return self._initialized
