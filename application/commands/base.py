"""Base command class for CLI operations."""

from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    """Base class for all CLI commands."""
    
    @abstractmethod
    async def execute(self) -> Any:
        """
        Execute the command.
        
        Returns:
            Command execution result
        """
        pass
    
    def validate(self) -> None:
        """
        Validate command parameters before execution.
        
        Raises:
            ValueError: If parameters are invalid
        """
        pass
