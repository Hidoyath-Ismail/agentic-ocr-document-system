from typing import Dict, Any, List, Tuple


REQUIRED_FIELDS = ["doc_type", "date"]


def validate_structured_data(
    structured_data: Dict[str, Any]
) -> Tuple[str, List[str], bool]:
    """
    Validate extracted structured data.
    This's the deterministic gate that decides if the extraction is good enough or if it needs human review.

    Returns:
        validation_status: "pass" | "fail"
        validation_errors: list[str]
        needs_review: bool
    """

    errors: List[str] = []

    for field in REQUIRED_FIELDS:
        value = structured_data.get(field)
        if not value or value == "unknown":
            errors.append(f"{field} is missing or unknown")

    total = structured_data.get("total")
    if total is not None:
        try:
            float(total)
        except (ValueError, TypeError):
            errors.append("total is not a valid number")

    if errors:
        return "fail", errors, True

    return "pass", [], False
