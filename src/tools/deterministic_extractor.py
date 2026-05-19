from __future__ import annotations

import re
from src.schemas.extraction import ExtractedDocument

def _first_match(pattern: str, text: str, flags: int = 0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None



def classify_doc_type(text: str) -> str:
    t = text.lower()

    # Receipt signals (strong)
    if "amount paid" in t or "payment history" in t or "payment method" in t or "paid on" in t:
        return "receipt"

    # PO signals
    if "purchase order" in t or re.search(r"\bpo\b", t):
        return "po"

    # Invoice signals
    if "invoice" in t:
        return "invoice"

    # Fallback
    if "receipt" in t:
        return "receipt"

    return "unknown"




def extract_fields_deterministic(text: str) -> ExtractedDocument:
    # normalize OCR weirdness
    cleaned = text.replace("\x00", " ")

    doc_type = classify_doc_type(cleaned)

    # Date (e.g., "December 16, 2025")
    date = _first_match(r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b", cleaned)

    # Total / Amount paid
    total = None
    total_str = _first_match(
        r"\bTotal\s+\$?\s*([0-9,]+\.\d{2})\b",
        cleaned,
        flags=re.IGNORECASE,
    )
    if total_str:
        total = float(total_str.replace(",", ""))
    else:
        paid_str = _first_match(
            r"\bAmount paid\s+\$?\s*([0-9,]+\.\d{2})\b",
            cleaned,
            flags=re.IGNORECASE,
        )
        if paid_str:
            total = float(paid_str.replace(",", ""))

    # Vendor name (best-effort)
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    vendor_name = None

    for ln in lines[:15]:
        low = ln.lower()

        if low in {"receipt", "invoice"}:
            continue

        if low.startswith("page ") and " of " in low:
            continue

        if re.fullmatch(r"page\s*\d+\s*of\s*\d+", low):
            continue

        if re.search(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            ln,
            flags=re.IGNORECASE,
        ):
            continue

        vendor_name = ln
        break

    return ExtractedDocument(
        doc_type=doc_type,
        vendor_name=vendor_name,
        date=date,
        total=total,
    )