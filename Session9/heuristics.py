"""
heuristics_simple.py

Lightweight heuristic module for an Agentic AI bot using MCP registry.
Implements validation, safety, and recovery checks without Pydantic dependencies.

Integrate with: main.py (orchestrator), perception.py (intent detection),
memory.py (user context), and MCP tool registry.

Author: Rashi’s Agentic Bot
"""

import re
import time
import random
import difflib
import logging


# ---------------------------------------------------------------------------
# Simple Config + Result Classes
# ---------------------------------------------------------------------------

class HeuristicConfig:
    """Configuration thresholds for heuristic logic."""

    def __init__(
        self,
        max_input_length=2000,
        max_retry_attempts=3,
        embedding_distance_threshold=0.75,
        confidence_threshold=0.65,
        transient_error_signatures=None
    ):
        self.max_input_length = max_input_length
        self.max_retry_attempts = max_retry_attempts
        self.embedding_distance_threshold = embedding_distance_threshold
        self.confidence_threshold = confidence_threshold
        self.transient_error_signatures = transient_error_signatures or ["timeout", "503", "rate limit"]


class HeuristicResult:
    """Lightweight structure for returning heuristic outcomes."""

    def __init__(self, passed, message, severity="info", next_action=None):
        self.passed = passed
        self.message = message
        self.severity = severity
        self.next_action = next_action

    def to_dict(self):
        """Return as dictionary (for JSON logging or response)."""
        return {
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
            "next_action": self.next_action
        }


# ---------------------------------------------------------------------------
# Heuristic Functions
# ---------------------------------------------------------------------------

class HeuristicEngine:
    """Core heuristic methods for validation, safety, and recovery."""

    def __init__(self, config=None):
        self.config = config or HeuristicConfig()

    # ---------------------------
    # A. Input Validation Heuristics
    # ---------------------------

    def validate_input_semantics(self, text):
        """Ensure input has coherent structure (intent + content)."""
        if len(text.split()) < 2:
            return HeuristicResult(False, "Input too short or unclear — specify clearer intent.", "warning", "ask_user")
        return HeuristicResult(True, "Semantic validation passed.")

    def validate_input_format(self, input_type, value):
        """Validate input format (e.g., URL, string, number)."""
        if input_type == "url" and not re.match(r"^https?://", str(value)):
            return HeuristicResult(False, "Invalid URL format — must start with http(s)://", "warning", "ask_user")
        return HeuristicResult(True, "Format validation passed.")

    def validate_length(self, text):
        """Ensure input length within safe range."""
        if len(text) > self.config.max_input_length:
            return HeuristicResult(
                False,
                f"Input exceeds {self.config.max_input_length} chars. Consider summarizing.",
                "warning",
                "truncate"
            )
        return HeuristicResult(True, "Length validation passed.")

    def validate_logical_consistency(self, fields):
        """Check for logical consistency between fields."""
        if "start_date" in fields and "end_date" in fields and fields["start_date"] > fields["end_date"]:
            return HeuristicResult(False, "Invalid date range: start_date > end_date.", "critical", "ask_user")
        return HeuristicResult(True, "Field consistency valid.")

    def detect_context_drift(self, distance):
        """Detect when new input diverges from conversation context."""
        if distance > self.config.embedding_distance_threshold:
            return HeuristicResult(False, "Context drift detected — treating as new topic.", "info", "reset_context")
        return HeuristicResult(True, "Context alignment OK.")

    # ---------------------------
    # B. Safety and MCP Tool Compliance
    # ---------------------------

    def check_sensitive_data(self, text):
        """Block potential sensitive or credential data."""
        if re.search(r"(api[_-]?key|password|token|secret|ssn)", text, re.I):
            return HeuristicResult(False, "Sensitive data detected — execution blocked.", "critical", "abort")
        return HeuristicResult(True, "No sensitive data detected.")

    def check_mcp_tool_registry(self, tool_name, registry):
        """
        Validate that a tool exists in the MCP registry (list of dicts).
        Each dict should include at least 'name' and 'permissions'.
        """
        tool_names = [t["name"] for t in registry]
        for t in registry:
            if t["name"] == tool_name:
                return HeuristicResult(True, f"Tool '{tool_name}' found in MCP registry.")
        suggestion = difflib.get_close_matches(tool_name, tool_names, n=1)
        hint = f" Did you mean '{suggestion[0]}'?" if suggestion else ""
        return HeuristicResult(False, f"Tool '{tool_name}' not found in registry.{hint}", "warning", "ask_user")

    def check_tool_permission(self, tool_name, registry, required_permission):
        """Ensure the tool has the correct permission level."""
        for t in registry:
            if t["name"] == tool_name:
                if required_permission in t.get("permissions", []):
                    return HeuristicResult(True, f"Permission '{required_permission}' validated for tool '{tool_name}'.")
                else:
                    return HeuristicResult(False, f"Tool '{tool_name}' lacks '{required_permission}' permission.", "warning", "ask_user")
        return HeuristicResult(False, f"Tool '{tool_name}' not found — cannot validate permission.", "critical", "abort")

    def validate_llm_response_sanity(self, response):
        """Ensure LLM response is safe and coherent."""
        if any(term in response.lower() for term in ["ignore safety", "exploit", "harmful"]):
            return HeuristicResult(False, "Unsafe or self-contradictory response detected.", "critical", "ask_user")
        return HeuristicResult(True, "LLM response sanity OK.")

    # ---------------------------
    # C. Recovery and Retry
    # ---------------------------

    def handle_timeout(self, attempt):
        """Handle tool timeout with exponential backoff."""
        if attempt >= self.config.max_retry_attempts:
            return HeuristicResult(False, "Maximum retries exceeded.", "critical", "abort")
        wait_time = 2 ** attempt + random.random()
        logging.warning(f"Timeout — retrying attempt {attempt + 1} after {wait_time:.1f}s")
        time.sleep(wait_time)
        return HeuristicResult(True, f"Retrying attempt {attempt + 1} after {wait_time:.1f}s delay.", "info", "retry")

    def detect_transient_error(self, error_message):
        """Recognize transient network or API errors."""
        for sig in self.config.transient_error_signatures:
            if sig in error_message.lower():
                return HeuristicResult(False, f"Transient error detected: '{error_message}'. Safe to retry.", "info", "retry")
        return HeuristicResult(True, "No transient errors detected.")

    def progressive_simplification(self, failure_count):
        """Simplify request after multiple failures."""
        if failure_count >= 2:
            return HeuristicResult(False, "Multiple failures detected — simplifying task.", "info", "simplify")
        return HeuristicResult(True, "No simplification needed.")

    def explain_and_escalate(self, consecutive_failures):
        """Generate diagnostic summary after repeated failures."""
        if consecutive_failures >= 3:
            return HeuristicResult(False, "Multiple repeated failures — escalating for human review.", "critical", "escalate")
        return HeuristicResult(True, "No escalation required.")

    # ---------------------------
    # D. Meta-Heuristic
    # ---------------------------

    def confidence_gated_action(self, confidence):
        """Block irreversible actions below minimum confidence threshold."""
        if confidence < self.config.confidence_threshold:
            return HeuristicResult(False, f"Confidence {confidence:.2f} below threshold {self.config.confidence_threshold}. User confirmation required.", "warning", "ask_user")
        return HeuristicResult(True, "Confidence sufficient for action.")


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example MCP tool registry stub
    registry = [
        {"name": "fetch_embeddings", "permissions": ["read"]},
        {"name": "search_web", "permissions": ["read"]},
        {"name": "summarize_text", "permissions": ["read"]}
    ]

    engine = HeuristicEngine()

    tests = [
        engine.validate_input_semantics("summarize"),
        engine.check_mcp_tool_registry("fetch_embeddings", registry),
        engine.check_mcp_tool_registry("delete_all", registry),
        engine.confidence_gated_action(0.4),
        engine.handle_timeout(1)
    ]

    for t in tests:
        print(t.to_dict())
