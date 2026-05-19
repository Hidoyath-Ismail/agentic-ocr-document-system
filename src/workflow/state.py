# src/workflow/state.py
from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    """
    Shared state passed across LangGraph nodes for the OCR Document Intake pipeline.
    total=False lets nodes add fields progressively.
    """

    # --- UI / conversation (for future use) ---
    # messages: List[Dict[str, Any]]

    # --- Document identity & metadata ---
    document_id: str
    file_name: str
    file_path: str
    file_type: str  # "pdf" or "image"

    # --- Text extraction & OCR ---
    extracted_text: str
    text_source: str  # "pypdf" or "ocr" or "none"

    # --- Classification & structured output ---
    doc_type: str  # "invoice" | "receipt" | "purchase_order" | "unknown"
    structured_data: Dict[str, Any] 

    # --- Validation ---
    validation_status: str  # "pass" | "fail"
    validation_errors: List[str]
    needs_review: bool

    # --- Audit trail ---
    audit_notes: List[str]

    llm_structured_data: Dict[str, Any]  
    llm_used: bool