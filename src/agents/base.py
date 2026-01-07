# src/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the shared state and return updates.
        """
        pass