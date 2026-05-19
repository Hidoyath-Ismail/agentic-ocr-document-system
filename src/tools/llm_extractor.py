from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from langchain_openai import ChatOpenAI

from src.schemas.extraction import ExtractedDocument

SYSTEM_PROMPT = """You are a careful document extraction assistant.
Extract fields from OCR/text of invoices/receipts/POs.

Rules:
- Return JSON that matches the provided schema exactly.
- If you cannot find a field confidently, set it to null (do NOT guess).
- total must be a number if present; remove currency symbols/commas.
- date should be best-effort in ISO format YYYY-MM-DD when possible; else null.
- vendor_name: prefer merchant/vendor name at top of receipt/invoice; else null.
- doc_type: one of: invoice, receipt, purchase_order, unknown.
"""

USER_PROMPT_TEMPLATE = """Text:
{raw_text}

Deterministic extraction (may be incomplete/wrong):
{deterministic}

Validation errors:
{validation_errors}

Task:
Fill or correct fields to satisfy the schema. Use validation errors as guidance.
Return only the structured JSON output.
"""

def llm_extract_fields(
    raw_text: str,
    deterministic: Dict[str, Any],
    validation_errors: list[str],
    model: str = "gpt-4o-mini",
) -> ExtractedDocument:
    """
    LLM fallback extraction into ExtractedDocument schema.
    Returns a Pydantic model instance.
    """
    llm = ChatOpenAI(model=model, temperature=0)

    # Structured output: the model is forced to return the schema
    llm_structured = llm.with_structured_output(ExtractedDocument)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        raw_text=raw_text[:12000],  # guard: keep prompt bounded
        deterministic=deterministic,
        validation_errors=validation_errors,
    )

    result: ExtractedDocument = llm_structured.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    return result