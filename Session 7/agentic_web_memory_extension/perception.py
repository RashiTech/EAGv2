from typing import Dict

from utils.llm_interface import LLMInterface


def parse_query(llm: LLMInterface, query: str) -> Dict[str, str]:
    """Extract a topic and intent from the user's query using Gemini.

    Returns a dict with keys: {"intent", "topic"}
    """
    prompt = (
        "You are classifying a user's search query.\n"
        "Return two short fields: intent (store or search) and topic (3-6 words).\n"
        f"Query: {query}\n"
        "Respond as: intent: <store|search>\n"
        "topic: <short topic>\n"
    )
    result = llm.reason(prompt)
    intent = "search"
    topic = query.strip()[:60]
    for line in result.splitlines():
        line = line.strip().lower()
        if line.startswith("intent:"):
            v = line.split(":", 1)[1].strip()
            if v in {"store", "search"}:
                intent = v
        if line.startswith("topic:"):
            topic = line.split(":", 1)[1].strip()
    return {"intent": intent, "topic": topic}


