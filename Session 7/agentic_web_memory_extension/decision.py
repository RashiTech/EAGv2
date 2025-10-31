from typing import Literal

ActionType = Literal["store_page", "find_relevant_page", "highlight_text"]


def decide_action(intent: str) -> ActionType:
    """Map high-level intent to an action."""
    if intent == "store":
        return "store_page"
    return "find_relevant_page"


