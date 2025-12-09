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
    
    def __init__(self, visual_style: str = "Professional", speaker_style: str = "Professional"):
        """
        Initialize the agent manager.
        
        Args:
            visual_style: Visual style for designer agent
            speaker_style: Speaking style for writer agent
        """
        self._agents: dict[str, LlmAgent] = {}
        self._initialized = False
        self.visual_style = visual_style
        self.speaker_style = speaker_style
    
    def initialize_agents(self) -> None:
        """Initialize all agents with their configurations."""
        if self._initialized:
            logger.warning("Agents already initialized")
            return
        
        # Import prompts from new structure
        from agents.prompts import (
            AUDITOR_PROMPT,
            ANALYST_PROMPT,
            WRITER_PROMPT,
            SUPERVISOR_PROMPT,
            OVERVIEWER_PROMPT,
            DESIGNER_PROMPT,
            TRANSLATOR_PROMPT,
            IMAGE_TRANSLATOR_PROMPT,
            VIDEO_GENERATOR_PROMPT,
            REFINER_PROMPT,
        )
        
        # Initialize agents
        self._agents["auditor"] = LlmAgent(
            name="auditor",
            model=ModelConfig.AUDITOR,
            description="Evaluates existing speaker notes quality.",
            instruction=AUDITOR_PROMPT,
        )
        
        self._agents["analyst"] = LlmAgent(
            name="slide_analyst",
            model=ModelConfig.ANALYST,
            description="Extracts insights from slide images.",
            instruction=ANALYST_PROMPT,
        )
        
        # Writer agent with speaker style injected into instruction
        writer_instruction = f"{WRITER_PROMPT}\n\n**SPEAKER STYLE FOR THIS SESSION:**\n{self.speaker_style}"
        self._agents["writer"] = LlmAgent(
            name="speech_writer",
            model=ModelConfig.WRITER,
            description="Generates presentation scripts with context.",
            instruction=writer_instruction,
            tools=[google_search],
        )
        
        self._agents["supervisor"] = LlmAgent(
            name="supervisor",
            model=ModelConfig.SUPERVISOR,
            description="Orchestrates the slide generation workflow.",
            instruction=SUPERVISOR_PROMPT,
            tools=[
                AgentTool(agent=self._agents["auditor"]),
                AgentTool(agent=self._agents["writer"]),
            ],
        )
        
        self._agents["overviewer"] = LlmAgent(
            name="overviewer",
            model=ModelConfig.OVERVIEWER,
            description="Generates global presentation context.",
            instruction=OVERVIEWER_PROMPT,
        )
        
        # Designer agent with visual style injected into instruction
        designer_instruction = f"{DESIGNER_PROMPT}\n\n**VISUAL STYLE FOR THIS SESSION:**\n{self.visual_style}"
        self._agents["designer"] = LlmAgent(
            name="designer",
            model=ModelConfig.DESIGNER,
            description="Generates enhanced slide visuals.",
            instruction=designer_instruction,
        )
        
        self._agents["translator"] = LlmAgent(
            name="translator",
            model=ModelConfig.TRANSLATOR,
            description="Translates speaker notes to target languages.",
            instruction=TRANSLATOR_PROMPT,
        )
        
        self._agents["image_translator"] = LlmAgent(
            name="image_translator",
            model=ModelConfig.IMAGE_TRANSLATOR,
            description="Translates slide visuals to target languages.",
            instruction=IMAGE_TRANSLATOR_PROMPT,
        )
        
        self._agents["video_generator"] = LlmAgent(
            name="video_generator",
            model=ModelConfig.VIDEO_GENERATOR,
            description="Generates video prompts for slides.",
            instruction=VIDEO_GENERATOR_PROMPT,
        )
        
        self._agents["refiner"] = LlmAgent(
            name="refiner",
            model=ModelConfig.REFINER,
            description="Refines speaker notes for TTS.",
            instruction=REFINER_PROMPT,
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
