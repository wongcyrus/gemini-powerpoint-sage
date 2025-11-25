"""Supervisor Agent."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from . import prompt
from .auditor import auditor_agent
from .writer import writer_agent

# Note: 'call_analyst' tool will be added dynamically in main.py 
# because it requires runtime access to image registry.

supervisor_agent = LlmAgent(
    name="supervisor",
    model="gemini-2.5-flash",
    description="The orchestrator that manages the slide generation workflow.",
    instruction=prompt.SUPERVISOR_PROMPT,
    tools=[
        AgentTool(agent=auditor_agent), 
        AgentTool(agent=writer_agent)
    ]
)
