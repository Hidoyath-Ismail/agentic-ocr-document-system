# src/workflow/graph.py
from langgraph.graph import StateGraph, END

from src.workflow.state import AgentState
from src.tools.pdf_text_extractor import extract_text_from_pdf


def ingest_document(state: AgentState) -> AgentState:
    """
    Initialize document-related fields.
    (Placeholder: UI will fill these later.)
    """
    state["audit_notes"] = state.get("audit_notes", [])
    state["audit_notes"].append("ingest_document: started")

    # Temporary hardcoded values for now
    state["file_path"] = "data/uploads/Receipt-2398-4319.pdf"
    state["file_name"] = "Receipt-2398-4319.pdf"
    state["file_type"] = "pdf"

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

def ocr_placeholder(state: AgentState) -> AgentState:
    """
    Placeholder for OCR path (Phase 5).
    """
    state["audit_notes"].append("ocr_placeholder: OCR would run here")
    state["text_source"] = "ocr"
    return state


def route_after_text_extraction(state: AgentState) -> str:
    """
    If no extracted text, route to OCR. Otherwise finalize.
    """
    text = state.get("extracted_text", "")
    return "ocr_placeholder" if not text else "finalize"


def finalize(state: AgentState) -> AgentState:
    state["audit_notes"].append("finalize: done")
    return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("ingest_document", ingest_document)
    graph.add_node("extract_text_if_possible", extract_text_if_possible)
    graph.add_node("ocr_placeholder", ocr_placeholder)   
    graph.add_node("finalize", finalize) 

    graph.set_entry_point("ingest_document")
    graph.add_edge("ingest_document", "extract_text_if_possible")
    #graph.add_edge("extract_text_if_possible", END)
    graph.add_conditional_edges(
        "extract_text_if_possible",
        route_after_text_extraction,
        {
            "ocr_placeholder": "ocr_placeholder",
            "finalize": "finalize",
        },
    )

    graph.add_edge("ocr_placeholder", "finalize")
    graph.add_edge("finalize", END)


    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"messages": []})
    print(result)
