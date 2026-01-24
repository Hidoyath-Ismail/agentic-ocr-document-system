from typing import Dict, Any
from src.agents.base import BaseAgent
from datetime import datetime


class IntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="intake")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["audit_log"].append({
            "step": "intake",
            "ts": datetime.utcnow().isoformat(),
            "details": {
                "file_name": state.get("file_name"),
                "file_type": state.get("file_type"),
            }
        })
        return state
