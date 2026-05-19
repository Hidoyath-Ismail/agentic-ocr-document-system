from typing import Dict, Any

def merge_fill_missing(base: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prefer base fields when they exist.
    Only fill missing (None / empty) values from fallback.
    """
    merged = dict(base)

    for key, value in fallback.items():
        if key not in merged or merged[key] in (None, "", [], {}):
            merged[key] = value

    return merged