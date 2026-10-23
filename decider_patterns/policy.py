"""
Reusable Decision Pattern: #policy
-----------------------------------
Pattern Name: Decider 2B Incident & Governance Policy Classifier
Tag: #policy, #strands-decider-2b

Problem:
Autonomous cloud agents must rapidly classify incoming events, alerts, and requests
into strict operational policy buckets (P1 Outage, P2 Degradation, Security Threat,
FinOps Optimization, or General Inquiry) to determine SLA, notification routing,
and required approval levels. Doing this with an LLM introduces latency spikes during
active outages.

Solution:
Strands Decider 2B classifies the incoming event into discrete policy categories in ~115ms
with calibrated probabilities, allowing immediate routing and SLA clock activation.
"""

from typing import Optional, Dict
from enum import Enum
from pydantic import BaseModel
from .client import StrandsDeciderClient, ChoiceQuestion


class PolicyCategory(str, Enum):
    P1_CRITICAL_OUTAGE = "p1_critical_outage"
    P2_SERVICE_DEGRADATION = "p2_service_degradation"
    SECURITY_INCIDENT = "security_incident"
    FINOPS_OPTIMIZATION = "finops_optimization"
    ROUTINE_INQUIRY = "routine_inquiry"


class PolicyClassificationResult(BaseModel):
    category: PolicyCategory
    sla_minutes: int
    confidence: float
    probabilities: Dict[str, float]
    requires_pagerduty: bool
    latency_ms: float
    state_prompt: str


class DeciderPolicyClassifier:
    """
    Sub-115ms Policy Classifier powered by Strands Decider 2B.
    """

    SLA_MAP = {
        PolicyCategory.P1_CRITICAL_OUTAGE: 5,
        PolicyCategory.SECURITY_INCIDENT: 10,
        PolicyCategory.P2_SERVICE_DEGRADATION: 30,
        PolicyCategory.FINOPS_OPTIMIZATION: 1440,
        PolicyCategory.ROUTINE_INQUIRY: 480,
    }

    PAGERDUTY_MAP = {
        PolicyCategory.P1_CRITICAL_OUTAGE: True,
        PolicyCategory.SECURITY_INCIDENT: True,
        PolicyCategory.P2_SERVICE_DEGRADATION: False,
        PolicyCategory.FINOPS_OPTIMIZATION: False,
        PolicyCategory.ROUTINE_INQUIRY: False,
    }

    def __init__(self, client: Optional[StrandsDeciderClient] = None):
        self.client = client or StrandsDeciderClient()

    def classify_event(self, event_text: str) -> PolicyClassificationResult:
        state = f"Operational Event: {event_text}"
        options = [c.value for c in PolicyCategory]

        questions = {
            "policy_category": ChoiceQuestion(
                type="choice",
                instructions="Classify this operational event into the most appropriate governance and incident policy category.",
                options=options,
            )
        }

        decision = self.client.ask(state=state, questions=questions)
        answer = decision.answers.get("policy_category")

        if not answer:
            category = PolicyCategory.ROUTINE_INQUIRY
            conf = 0.5
            probs = {}
        else:
            category = PolicyCategory(answer.prediction)
            conf = answer.confidence
            probs = answer.probabilities or {category.value: conf}

        return PolicyClassificationResult(
            category=category,
            sla_minutes=self.SLA_MAP[category],
            confidence=conf,
            probabilities=probs,
            requires_pagerduty=self.PAGERDUTY_MAP[category],
            latency_ms=decision.latency_ms,
            state_prompt=state,
        )
