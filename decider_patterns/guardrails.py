"""
Reusable Decision Pattern: #guardrails
----------------------------------------
Pattern Name: Decider 2B Tool Argument Grounding & Safety Guardrail
Tag: #guardrails, #strands-decider-2b

Problem:
Large Language Models (System 2) frequently suffer from hallucinated arguments,
scope creep, or prompt-injection attacks where an agent attempts destructive
actions (e.g., dropping production tables, terminating active database instances,
or exposing secrets) that the human user never authorized.
Running another heavy Bedrock LLM call to verify every tool call adds 1,800ms+ latency
and inflates costs dramatically.

Solution:
Strands Decider 2B (System 1) intercepts every tool call via an InterventionHandler.
In ~115ms, it evaluates the tool name, arguments, and original user intent using
a typed 'noul' (grounded/not grounded) question and calibrated confidence score.
If confidence is below threshold (<0.75) or grounded == False:
  - It triggers Deny() or escalates to Confirm() with human-in-the-loop!
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import json
from .client import StrandsDeciderClient, NoulQuestion, DeciderAnswer


# Standard Strands Intervention Lifecycle Action Classes
class Proceed(BaseModel):
    action: str = "PROCEED"
    reason: Optional[str] = None


class Deny(BaseModel):
    action: str = "DENY"
    reason: str


class Confirm(BaseModel):
    action: str = "CONFIRM"
    message: str
    requires_human_approval: bool = True


class Guide(BaseModel):
    action: str = "GUIDE"
    guidance: str


InterventionResult = Union[Proceed, Deny, Confirm, Guide]


class ToolCallEvent(BaseModel):
    """Represents an agent's intended tool invocation event."""
    tool_name: str
    tool_args: Dict[str, Any]
    user_intent: str
    session_id: Optional[str] = "default-session"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GuardrailCheckResult(BaseModel):
    """Evaluation output returned by DeciderGuardrailHandler."""
    tool_name: str
    is_grounded: bool
    confidence: float
    probability: float
    intervention: InterventionResult
    latency_ms: float
    state_prompt: str


class DeciderGuardrailHandler:
    """
    Drop-in Strands InterventionHandler powered by Strands Decider 2B.
    Inspects tool calls before execution to verify arguments are grounded in user intent.

    How to use in your agent:
    -------------------------
    guardrail = DeciderGuardrailHandler(confidence_threshold=0.75)
    decision = guardrail.before_tool_call(ToolCallEvent(
        tool_name="aws_terminate_rds",
        tool_args={"db_instance_id": "prod-orders-db"},
        user_intent="Please restart the staging cache"
    ))
    if isinstance(decision.intervention, Deny):
        print("Blocked:", decision.intervention.reason)
    """

    name = "strands-decider-grounding-guardrail"

    def __init__(
        self,
        client: Optional[StrandsDeciderClient] = None,
        confidence_threshold: float = 0.75,
        strict_destructive_mode: bool = True,
    ):
        self.client = client or StrandsDeciderClient()
        self.confidence_threshold = confidence_threshold
        self.strict_destructive_mode = strict_destructive_mode

    def before_tool_call(self, event: ToolCallEvent) -> GuardrailCheckResult:
        """
        Intercepts the tool call before execution.
        Evaluates argument grounding and intent alignment with Decider 2B.
        """
        state = self._build_state_representation(event)

        # Typed Question passed to Decider 2B
        questions = {
            "is_grounded": NoulQuestion(
                type="noul",
                instructions=(
                    "Are the intended tool and all arguments strictly grounded in and "
                    "directly authorized by the user's explicit request? "
                    "Answer false if arguments drift, target unmentioned production resources, "
                    "or perform unrequested destructive actions."
                ),
                criteria={
                    "true": "The tool call and arguments match user intent with no drift.",
                    "false": "The arguments are hallucinated, ungrounded, or malicious.",
                },
            )
        }

        # Query Decider 2B (sub-115ms)
        decision = self.client.ask(state=state, questions=questions)
        answer = decision.answers.get("is_grounded")

        if not answer:
            # Safe default fallback
            return GuardrailCheckResult(
                tool_name=event.tool_name,
                is_grounded=False,
                confidence=0.5,
                probability=0.5,
                intervention=Deny(reason="Guardrail failed to obtain decision from Decider 2B"),
                latency_ms=decision.latency_ms,
                state_prompt=state,
            )

        is_grounded = bool(answer.prediction)
        confidence = answer.confidence
        prob = answer.probability if answer.probability is not None else (0.9 if is_grounded else 0.1)

        # Determine Intervention Action based on Calibrated Confidence
        if not is_grounded:
            intervention = Deny(
                reason=(
                    f"Blocked by Decider 2B: Action '{event.tool_name}' with args {event.tool_args} "
                    f"is not grounded in user request '{event.user_intent}' (P={prob:.2f}, Confidence={confidence:.2f})"
                )
            )
        elif confidence < self.confidence_threshold:
            # Low confidence grounding -> Require human confirmation
            intervention = Confirm(
                message=(
                    f"Decider 2B calibrated confidence ({confidence:.2f}) is below threshold ({self.confidence_threshold}). "
                    f"Confirm execution of '{event.tool_name}' on target resource?"
                ),
                requires_human_approval=True,
            )
        else:
            intervention = Proceed(
                reason=f"Verified grounded by Decider 2B (P={prob:.2f}, Confidence={confidence:.2f})"
            )

        return GuardrailCheckResult(
            tool_name=event.tool_name,
            is_grounded=is_grounded,
            confidence=confidence,
            probability=prob,
            intervention=intervention,
            latency_ms=decision.latency_ms,
            state_prompt=state,
        )

    def _build_state_representation(self, event: ToolCallEvent) -> str:
        """Serializes the tool call context into a clean state text for Decider 2B."""
        return (
            f"User Intent: {event.user_intent}\n"
            f"Proposed Tool: {event.tool_name}\n"
            f"Arguments: {json.dumps(event.tool_args, separators=(',', ':'))}"
        )
