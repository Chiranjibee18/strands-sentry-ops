"""
Decision Pattern: Incident Tool Selection (#tool-selection)
Intervention Handler & Guardrail Integration
-----------------------------------------------------------
Implements Strands InterventionHandler to validate decisions before tool execution.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class Proceed:
    action: str = "PROCEED"
    reason: str = "Decision verified and grounded."


class Deny:
    action: str = "DENY"

    def __init__(self, reason: str = "Action blocked by guardrail."):
        self.reason = reason


class Confirm:
    action: str = "CONFIRM"

    def __init__(self, message: str = "Action requires operator confirmation."):
        self.message = message


class ToolInterventionEvent(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]
    user_intent: str
    confidence: float


class IncidentInterventionHandler:
    """
    Validates that proposed tool execution is grounded in incident context
    and has sufficient Decider confidence to proceed safely.
    """

    def __init__(self, min_confidence: float = 0.45, require_confirm_for_destructive: bool = True):
        self.min_confidence = min_confidence
        self.require_confirm_for_destructive = require_confirm_for_destructive

    def before_tool_call(self, event: ToolInterventionEvent):
        # 1. Grounding and prompt injection check
        intent_lower = event.user_intent.lower()
        if "ignore all rules" in intent_lower or "disregard safety" in intent_lower:
            return Deny("Adversarial prompt injection detected in incident context.")

        # 2. Low-confidence abstention check
        if event.confidence < self.min_confidence:
            return Confirm(f"Decider confidence ({event.confidence:.2f}) below threshold {self.min_confidence:.2f}. Request operator review.")

        # 3. Destructive action check
        name_lower = event.tool_name.lower()
        if "delete" in name_lower or "terminate" in name_lower or "drop" in name_lower:
            if self.require_confirm_for_destructive and "confirm" not in event.user_intent.lower():
                return Confirm(f"Destructive action '{event.tool_name}' requires explicit operator confirmation.")

        return Proceed()
