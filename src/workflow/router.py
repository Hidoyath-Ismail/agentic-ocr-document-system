# src/workflow/router.py
def route_query(user_input: str) -> str:
    """
    Decide which agent should handle the query.
    """
    text = user_input.lower()

    if any(word in text for word in ["portfolio", "allocation", "holdings"]):
        return "portfolio"

    if any(word in text for word in ["price", "market", "stock", "ticker"]):
        return "market"

    if any(word in text for word in ["goal", "plan", "retire", "target"]):
        return "goals"

    return "finance_qa"