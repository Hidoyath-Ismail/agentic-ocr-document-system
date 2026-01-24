from typing import Dict, Any
from src.agents.base import BaseAgent
from datetime import datetime
from pypdf import PdfReader


class OcrAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ocr")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        path = state.get("file_path")
        text = ""

        if path and path.lower().endswith(".pdf"):
            reader = PdfReader(path)
            pages = []
            for p in reader.pages:
                pages.append(p.extract_text() or "")
            text = "\n".join(pages).strip()

        state["ocr_text"] = text if text else None
        state["audit_log"].append({
            "step": "ocr",
            "ts": datetime.utcnow().isoformat(),
            "details": {"text_len": len(text)}
        })
        return state
