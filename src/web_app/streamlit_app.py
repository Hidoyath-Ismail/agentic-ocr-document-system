import base64
import streamlit as st
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import re
import json
import hashlib
import platform
from typing import Optional, Dict, Any
from src.workflow.graph import build_graph
from src.tools.validator import validate_structured_data

OUTPUT_DIR = Path("data/outputs")

# helper function to standardize UTC ISO timestamps
def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def _safe_slug(text: str, max_len: int = 40) -> str:
    """Convert text into a filesystem-safe slug."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_len] if text else "unknown"


def make_document_id(result: Dict[str, Any], source_file_path: str) -> str:
    """
    Deterministic-ish ID:
    vendor + total + short hash of source path + UTC timestamp (seconds).
    If you later add a true file hash, swap the path-hash for file-content hash.
    """
    structured = result.get("structured_data", {}) or {}
    vendor = _safe_slug(str(structured.get("vendor") or structured.get("vendor_name") or "vendor"))
    total = _safe_slug(str(structured.get("total") or structured.get("total_amount") or "total"))

    path_hash = hashlib.sha1(source_file_path.encode("utf-8")).hexdigest()[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    return f"{vendor}_{total}_{path_hash}_{ts}"

APP_VERSION = "0.9C"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 hash of a file (streaming; memory-safe)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def build_audit_package(result: dict, source_file_path: str) -> dict:
    """Create audit package with integrity hash + reviewer metadata."""
    # Hash source file (don’t crash app if hashing fails)
    try:
        source_sha256 = sha256_file(source_file_path)
    except Exception as e:
        source_sha256 = None
        result.setdefault("audit_notes", [])
        result["audit_notes"].append(f"audit_hash: failed ({e})")

    human_review = {
        "reviewer_name": st.session_state.get("reviewer_name") or None,
        "review_notes": st.session_state.get("review_notes") or None,
        "last_applied_fix_utc": st.session_state.get("last_applied_fix"),
    }

    audit_package = {
        "document_id": result.get("document_id"),
        "processed_at_utc": result.get("processed_at_utc") or utc_now_iso(),
        "source_file": source_file_path,
        "source_file_sha256": source_sha256,
        "app": {
            "name": "agentic-ocr-document-system",
            "version": APP_VERSION,
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "validation": {
            "status": result.get("validation_status"),
            "errors": result.get("validation_errors", []),
            "needs_review": result.get("needs_review", False),
            "is_validated": result.get("is_validated", False),
        },
        "structured_data": result.get("structured_data", {}),
        "human_review": human_review,
        "audit_trail": result.get("audit_notes", []),
        "raw_result": result,  # full internal state for trace/debug
    }
    return audit_package


def build_clean_package(audit_package: dict) -> dict:
    """Clean export for sharing/submission (no raw_result)."""
    clean = dict(audit_package)
    clean.pop("raw_result", None)
    # You can also remove environment metadata if you want it super clean:
    # clean.get("app", {}).pop("platform", None)
    # clean.get("app", {}).pop("python", None)
    return clean



def save_validated_result_to_disk(result: Dict[str, Any], source_file_path: str) -> Optional[str]:
    """
    Phase 9C:
    Save TWO artifacts when validation passed and no human review is needed:
      1) Clean validated package (shareable): *_validated.json
      2) Full audit package (internal): *_audit.json

    Returns the CLEAN saved filepath (validated.json) as string, else None.
    """
    validation_status = str(result.get("validation_status", "")).lower()
    needs_review = bool(result.get("needs_review", False))

    # Adjust if your validator uses different pass statuses
    is_pass = validation_status in {"pass", "passed", "valid", "validated", "ok", "true"}

    if not is_pass or needs_review:
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Keep document_id stable across reruns once set
    if not result.get("document_id"):
        result["document_id"] = make_document_id(result, source_file_path)

    document_id = result["document_id"]

    # Build the richer audit package (includes hash + reviewer metadata + app meta)
    audit_package = build_audit_package(result, source_file_path)
    # Ensure document_id is present in the package
    audit_package["document_id"] = document_id

    # Create clean/shareable package (no raw_result)
    clean_package = build_clean_package(audit_package)

    # Paths
    audit_path = OUTPUT_DIR / f"{document_id}_audit.json"
    clean_path = OUTPUT_DIR / f"{document_id}_validated.json"

    # Write files
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_package, f, ensure_ascii=False, indent=2)

    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(clean_package, f, ensure_ascii=False, indent=2)

    # Update runtime state
    result.setdefault("audit_notes", [])
    result["audit_notes"].append(f"persist_output: saved audit -> {str(audit_path)}")
    result["audit_notes"].append(f"persist_output: saved clean -> {str(clean_path)}")

    # Save paths for UI buttons
    result["saved_output_path"] = str(clean_path)   # clean (shareable)
    result["saved_audit_path"] = str(audit_path)    # full (internal)

    return str(clean_path)




def apply_fixes_to_result(result: Dict[str, Any], edited_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge edited fields into result['structured_data'], re-run validation,
    and update validation fields consistently.
    """
    structured = (result.get("structured_data") or {}).copy()

    # Merge only non-empty edits (so blanks don't wipe existing values)
    for k, v in edited_fields.items():
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        structured[k] = v

    # Re-run validation (tuple -> fields)
    status, errors, needs_review = validate_structured_data(structured)

    result["structured_data"] = structured
    result["validation_status"] = status
    result["validation_errors"] = errors
    result["needs_review"] = needs_review

    # Explicit validated flag
    result["is_validated"] = (status == "pass" and (not needs_review) and len(errors) == 0)

    # Audit trail
    result.setdefault("audit_notes", [])
    result["audit_notes"].append(
        f"human_review: applied fixes, revalidated -> {status} ({len(errors)} issues)"
    )

    return result


def get_json_download_bytes(result: dict) -> bytes:
    """
    Convert the current result (or the audit package) to downloadable JSON bytes.
    Prefer the persisted audit JSON if saved_output_path exists.
    """
    saved_path = result.get("saved_output_path")
    if saved_path: # if the file is already saved, it downloads that exact file.
        try:
            with open(saved_path, "rb") as f:
                return f.read()
        except Exception:
            # fall back to in-memory serialization below
            pass

    # Fallback: serialize current in-memory result 
    return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")


# -------------------------
# App config
# -------------------------
st.set_page_config(page_title="Agentic OCR Document Intake", layout="wide")

st.title("📄 Agentic OCR Document Intake System")
st.write(
    "Upload a document to extract structured data using deterministic OCR "
    "with a controlled LLM fallback."
)

# -------------------------
# 1) Upload
# -------------------------
st.header("1️⃣ Upload document")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

file_path = None

if uploaded_file is not None:
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / uploaded_file.name

    # ✅ Step 2 placement: clear previous outputs when a *different* file is uploaded
    # Use (name + size) as a simple file identity key
    new_file_key = f"{uploaded_file.name}::{uploaded_file.size}"

    if st.session_state.get("current_file_key") != new_file_key:
        st.session_state["current_file_key"] = new_file_key
        st.session_state.pop("result", None)
        st.session_state.pop("edited_fields", None)
        st.session_state.pop("last_applied_fix", None)

    # Save upload
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File uploaded successfully: {uploaded_file.name}")
    st.write(f"Saved to: `{file_path}`")

    # ---- PDF preview ----
    with st.expander("📄 Document preview (click to expand)", expanded=False):
        with open(file_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="75%"
            height="400"
            type="application/pdf">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)

else:
    st.info("Please upload a PDF document to proceed.")

# -------------------------
# 2) Run extraction
# -------------------------
if uploaded_file is not None and file_path is not None:
    st.header("2️⃣ Run extraction pipeline")

    if st.button("Run extraction"):
        with st.spinner("Running OCR and extraction..."):
            app = build_graph()
            result = app.invoke({"file_path": str(file_path)})

        st.session_state["result"] = result
        st.session_state.pop("edited_fields", None)
        st.session_state.pop("last_applied_fix", None)

        st.success("Extraction completed successfully.")

# -------------------------
# 3) Results (only if available)
# -------------------------
if "result" in st.session_state:
    st.header("3️⃣ Results (read-only)")
    result = st.session_state["result"]
    # ✅ Ensure is_validated is set for BOTH OCR + non-OCR paths
    errors = result.get("validation_errors") or []
    status = str(result.get("validation_status", "")).lower()
    needs_review = bool(result.get("needs_review", False))

    if "is_validated" not in result:
        result["is_validated"] = (status == "pass" and (not needs_review) and len(errors) == 0)
        st.session_state["result"] = result


    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🧾 Extracted text")
        extracted_text = result.get("extracted_text") or ""
        st.text_area("Extracted text", extracted_text, height=300, label_visibility="collapsed")

        st.subheader("🧩 Audit trail")
        for note in result.get("audit_notes", []):
            st.write("•", note)

    with col2:
        st.subheader("✅ Extraction summary")
        st.write("Text source:", result.get("text_source"))
        st.write("LLM used:", result.get("llm_used", False))
        st.write("Validation status:", result.get("validation_status"))
        st.write("Needs review:", result.get("needs_review"))

        structured = result.get("structured_data") or {}

        # Key fields (read-only)
        st.subheader("📌 Key fields (read-only)")
        st.write("Vendor:", structured.get("vendor_name"))
        st.write("Total:", structured.get("total"))

        # ✅ FIX: correct key name
        errors = result.get("validation_errors") or []
        st.subheader("⚠️ Validation errors")
        if errors:
            for e in errors:
                st.write("•", e)
        else:
            st.success("No validation errors.")

        # Fix required fields (conditional)
        st.subheader("📝 Fix required fields")

        error_text = " ".join(errors).lower()
        fields_to_fix = set()

        if "doc_type" in error_text or "document type" in error_text or "unknown" in error_text:
            fields_to_fix.add("doc_type")
        if "date" in error_text:
            fields_to_fix.add("date")
        if "total" in error_text:
            fields_to_fix.add("total")
        if "vendor" in error_text or "vendor_name" in error_text:
            fields_to_fix.add("vendor_name")

        edited_fields: Dict[str, Any] = {}

        if not fields_to_fix:
            st.info("Nothing to fix right now (validation passed).")
        else:
            if "doc_type" in fields_to_fix:
                edited_fields["doc_type"] = st.text_input(
                    "Document type (needs review)",
                    value=structured.get("doc_type") or ""
                )
            if "date" in fields_to_fix:
                edited_fields["date"] = st.text_input(
                    "Date (needs review)",
                    value=structured.get("date") or ""
                )
            if "total" in fields_to_fix:
                edited_fields["total"] = st.number_input(
                    "Total (needs review)",
                    value=float(structured.get("total") or 0.0),
                    step=0.01
                )
            if "vendor_name" in fields_to_fix:
                edited_fields["vendor_name"] = st.text_input(
                    "Vendor name (needs review)",
                    value=structured.get("vendor_name") or ""
                )

            st.session_state["edited_fields"] = edited_fields

            # Phase 9D-B: Lock edits after validation
            if not result.get("is_validated"):
                if st.button("✅ Apply fixes & re-validate"):
                    updated = apply_fixes_to_result(
                        st.session_state["result"],
                        st.session_state.get("edited_fields", {}) or {}
                    )
                    st.session_state["result"] = updated
                    st.session_state["last_applied_fix"] = datetime.now(timezone.utc).isoformat()
                    st.rerun()
            else:
                st.info("🔒 Approved output is locked. Re-upload a new file to process again.")

        # Final approved output (only when validated)
        if result.get("is_validated"):
            st.success("✅ Validation passed. Document is now validated.")
            st.subheader("✅ Final approved output")
            st.json(result.get("structured_data", {}), expanded=True)

            # Phase 9C: Review metadata (locked after save)
            st.subheader("🧑‍⚖️ Review metadata")

            already_saved = bool(result.get("saved_output_path")) and bool(result.get("saved_audit_path"))

            reviewer_name = st.text_input(
                "Reviewer name",
                value=st.session_state.get("reviewer_name", ""),
                placeholder="e.g., Nisa / QA Reviewer",
                disabled=already_saved,
            )
            review_notes = st.text_area(
                "Review notes (optional)",
                value=st.session_state.get("review_notes", ""),
                placeholder="What was corrected / verified? Any assumptions?",
                height=80,
                disabled=already_saved,
            )

            st.session_state["reviewer_name"] = reviewer_name
            st.session_state["review_notes"] = review_notes

            # Phase 9A: Human sign-off persistence (Finalize & Save)
            if not already_saved:
                if st.button("✅ Finalize & Save (creates audit + validated JSON)"):
                    saved_path = save_validated_result_to_disk(
                        st.session_state["result"],
                        str(file_path)
                    )
                    if saved_path:
                        st.success("💾 Approved output saved to disk")
                        st.rerun()
            else:
                st.success("💾 Approved output already saved to disk")

            # Phase 9B: Download JSON (only after save)
            if result.get("saved_output_path"):
                download_bytes = get_json_download_bytes(st.session_state["result"])

                doc_id = (
                    st.session_state["result"].get("document_id")
                    or Path(str(file_path)).stem
                    or "validated_output"
                )
                filename = f"{doc_id}_validated.json"

                st.download_button(
                    label="⬇️ Download validated JSON",
                    data=download_bytes,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True,
                )

                # New document (always when validated)
                if st.button("🆕 Process a new document"):
                    st.session_state.pop("result", None)
                    st.session_state.pop("reviewer_name", None)
                    st.session_state.pop("review_notes", None)
                    st.session_state.pop("edited_fields", None)
                    st.session_state.pop("last_applied_fix", None)
                    st.rerun()
