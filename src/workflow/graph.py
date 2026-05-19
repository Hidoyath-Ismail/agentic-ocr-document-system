# src/workflow/graph.pystate
from langgraph.graph import StateGraph, END
from numpy import rint
from pathlib import Path

from src.workflow.state import AgentState
from src.tools.pdf_text_extractor import extract_text_from_pdf
from src.tools.ocr_pdf_extractor import extract_text_from_scanned_pdf
from src.tools.deterministic_extractor import extract_fields_deterministic
from src.tools.validator import validate_structured_data
from src.tools.llm_extractor import llm_extract_fields
from src.tools.merge_utils import merge_fill_missing




def ingest_document(state: AgentState) -> AgentState:
    """
    Initialize document-related fields, and starts the audit trail for traceability.
    
    """
    state["audit_notes"] = state.get("audit_notes", [])
    state["audit_notes"].append("ingest_document: started")

    # Temporary hardcoded values for testing (uncomment to use)
    #state["file_path"] = "data/uploads/Receipt-2398-4319.pdf"
    #state["file_path"] = "data/uploads/scanned_test.pdf"
    #state["file_name"] = "Receipt-2398-4319.pdf"
    #state["file_name"] = "scanned_test.pdf"
    #state["file_type"] = "pdf"

    # Expect Streamlit to pass file_path
    file_path = state.get("file_path")
    if not file_path:
        raise ValueError("file_path not provided. Pass {'file_path': '...'} when invoking the graph.")

    p = Path(file_path)
    state["file_path"] = str(p)
    state["file_name"] = p.name
    state["file_type"] = p.suffix.lstrip(".").lower() or "pdf"

    return state


def extract_text_if_possible(state: AgentState) -> AgentState:
    """
    Try extracting text using pypdf.
    """
    text = extract_text_from_pdf(state["file_path"])

    state["extracted_text"] = text
    state["text_source"] = "pypdf" if text else "none"

    state["audit_notes"].append(
        f"extract_text_if_possible: extracted {len(text)} chars"
    )

    return state

def ocr_document(state: AgentState) -> AgentState:
    """
    Run OCR when pypdf extraction returned empty text.
    Converts PDF pages to images (pdf2image/Poppler) and extracts text (PYtesseract + Tesseract).
    """
    pdf_path = state["file_path"]

    ocr_text = extract_text_from_scanned_pdf(pdf_path, dpi=200)

    state["extracted_text"] = ocr_text
    state["text_source"] = "ocr"

    audit = state.get("audit_notes", [])
    audit.append("ocr: done (pdf2image+poppler -> pytesseract+tesseract)")
    state["audit_notes"] = audit

    return state

def extract_structured_data(state: AgentState) -> AgentState:
    """
    Deterministically extract structured fields from extracted_text.
    """
    text = state.get("extracted_text", "")

    extracted = extract_fields_deterministic(text)

    state["structured_data"] = extracted.model_dump()
    state["doc_type"] = extracted.doc_type

    audit = state.get("audit_notes", [])
    audit.append("structured_extraction: deterministic")
    state["audit_notes"] = audit

    return state


def validate_document(state: AgentState) -> AgentState:
    """
    Validate structured_data and set validation_status, validation_errors, needs_review.
    Verifies the extracted text and decides if human review is needed
    """
    structured = state.get("structured_data") or {}

    status, errors, needs_review = validate_structured_data(structured)

    state["validation_status"] = status
    state["validation_errors"] = errors
    state["needs_review"] = needs_review

    audit = state.get("audit_notes", [])
    audit.append(f"validation: {status} ({len(errors)} issues)")
    state["audit_notes"] = audit

    return state

def needs_llm_route(state: AgentState) -> str:
    """ LLM fallback routing """
    needs = state.get("needs_review", False)
    llm_used = state.get("llm_used", False)

    # Only allow ONE LLM attempt
    if needs and not llm_used:
        return "llm"
    return "finalize"



def route_after_text_extraction(state: AgentState) -> str:
    """
    If no extracted text, route to OCR. Otherwise finalize.
    """
    text = state.get("extracted_text", "")
    return "ocr" if not text else "finalize"



def llm_fallback_extraction(state: AgentState) -> AgentState:
    state["audit_notes"].append("llm_fallback_extraction: started")

    raw_text = state.get("raw_text", "")
    deterministic = state.get("structured_data", {}) or {}
    errors = state.get("validation_errors", []) or []

    llm_doc = llm_extract_fields(
        raw_text=raw_text,
        deterministic=deterministic,
        validation_errors=errors,
    )

    llm_data = llm_doc.model_dump()

    state["llm_structured_data"] = llm_data
    state["llm_used"] = True

    merged = merge_fill_missing(deterministic, llm_data)
    state["structured_data"] = merged

    state["audit_notes"].append("llm_fallback_extraction: completed (merged)")

    return state



def finalize(state: AgentState) -> AgentState:
    """ Finalize the state, perform any cleanup if necessary. """
    state["audit_notes"].append("finalize: done")
    return state

# Register the nodes, edges and build the graph
def build_graph():
    graph = StateGraph(AgentState)

    # --- Nodes ---
    graph.add_node("ingest_document", ingest_document)
    graph.add_node("extract_text_if_possible", extract_text_if_possible)
    graph.add_node("ocr", ocr_document)
    graph.add_node("structured_extraction", extract_structured_data)
    graph.add_node("validation", validate_document)
    graph.add_node("finalize", finalize)
    graph.add_node("llm_fallback_extraction", llm_fallback_extraction)


    # --- Entry point ---
    graph.set_entry_point("ingest_document")

    # --- Linear edges ---
    graph.add_edge("ingest_document", "extract_text_if_possible")

    # --- Conditional routing after text extraction ---
    # If pypdf returns empty text -> OCR
    # Else -> go directly to structured extraction
    graph.add_conditional_edges(
        "extract_text_if_possible",
        route_after_text_extraction,
        {
            "ocr": "ocr",
            "finalize": "structured_extraction",
        },
    )

    # After OCR, continue the same pipeline
    graph.add_edge("ocr", "structured_extraction")

    # Structured extraction -> validation -> finalize -> END
    graph.add_edge("structured_extraction", "validation")
    
    # Conditional routing after validation
    graph.add_conditional_edges(
        "validation",
        needs_llm_route,
        {
            "llm": "llm_fallback_extraction",
            "finalize": "finalize",
        },
    )

    graph.add_edge("llm_fallback_extraction", "validation")

    graph.add_edge("finalize", END)

    return graph.compile()



if __name__ == "__main__":
    from pprint import pprint

    app = build_graph()
    result = app.invoke({})

    print("\n================ FULL STATE (pretty) =================\n")
    pprint(result)

    print("\n================ SUMMARY =================\n")
    print("Doc type     :", result.get("doc_type"))
    print("Text source  :", result.get("text_source"))

    sd = result.get("structured_data") or {}
    print("Vendor       :", sd.get("vendor_name"))
    print("Date         :", sd.get("date"))
    print("Total        :", sd.get("total"))

    print("\nAudit trail:")
    for note in result.get("audit_notes", []):
        print(" -", note)

    # Optional: show only first 200 chars of text
    text = result.get("extracted_text") or ""
    print("\nExtracted text (first 200 chars):")
    print(text[:200].replace("\n", " "))
