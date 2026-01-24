from typing import Dict, Any
from src.agents.base import BaseAgent
from datetime import datetime
import re


class ExtractAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="extract")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = state.get("ocr_text") or ""
        extracted = {"document_type": "invoice"}

        # naive MVP patterns (replace with LLM later)
        m = re.search(r"Invoice\s*#?:?\s*([A-Z0-9\-]+)", text, re.IGNORECASE)
        if m:
            extracted["invoice_number"] = m.group(1)

        m = re.search(r"Total\s*[:$]\s*([0-9\.,]+)", text, re.IGNORECASE)
        if m:
            extracted["total_amount"] = m.group(1)

        state["extracted"] = extracted
        state["audit_log"].append({
            "step": "extract",
            "ts": datetime.utcnow().isoformat(),
            "details": {"fields": list(extracted.keys())}
        })
        return state
