# src/workflow/state.py
from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    """
    Shared state passed across LangGraph nodes.
    """
    messages: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    artifacts: Dict[str, Any]