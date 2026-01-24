# src/workflow/graph.py
from langgraph.graph import StateGraph, END

from src.workflow.state import AgentState


def ingest_document(state: AgentState) -> AgentState:
    """
    Placeholder node. We'll implement real ingestion next.
    """
    state["audit_notes"] = state.get("audit_notes", [])
    state["audit_notes"].append("ingest_document: placeholder")
    return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("ingest_document", ingest_document)
    graph.set_entry_point("ingest_document")
    graph.add_edge("ingest_document", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"messages": []})
    print(result)
