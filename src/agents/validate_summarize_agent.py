from typing import Dict, Any
from src.agents.base import BaseAgent
from datetime import datetime


class ValidateSummarizeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="validate_summarize")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        extracted = state.get("extracted") or {}
        missing = []

        # MVP required fields for invoice
        for f in ["invoice_number", "total_amount"]:
            if not extracted.get(f):
                missing.append(f)

        validation = {
            "is_valid": len(missing) == 0,
            "missing_fields": missing
        }
        state["validation"] = validation

        if validation["is_valid"]:
            state["summary"] = f"Invoice detected. Invoice #{extracted.get('invoice_number')} with total {extracted.get('total_amount')}."
        else:
            state["summary"] = f"Invoice detected but missing fields: {', '.join(missing)}."

        state["audit_log"].append({
            "step": "validate_summarize",
            "ts": datetime.utcnow().isoformat(),
            "details": validation
        })
        return state
