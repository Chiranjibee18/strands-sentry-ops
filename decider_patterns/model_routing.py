"""
Reusable Decision Pattern: #model-routing
------------------------------------------
Pattern Name: Decider 2B Confidence-Calibrated Model Router
Tag: #model-routing, #strands-decider-2b

Problem:
Sending every incoming request directly to a frontier foundation model on Amazon Bedrock
(e.g., Anthropic Claude 3.5 Sonnet or Amazon Nova Premier) wastes substantial cloud credits
and adds 1.5s - 3s latency for straightforward operational commands, status queries,
or known runbook actions.

Solution:
Strands Decider 2B evaluates the incoming state in ~115ms and classifies the routing tier:
1. 'local_runbook': Fast, automated local execution (0ms Bedrock cost, 115ms total latency)
2. 'bedrock_haiku_nova': Lightweight Bedrock model for summarization/formatting
3. 'bedrock_claude_sonnet': Frontier Bedrock model for complex RCA and multi-step synthesis
"""

from typing import Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field
from .client import StrandsDeciderClient, ChoiceQuestion


class RoutingTier(str, Enum):
    LOCAL_RUNBOOK = "local_runbook"
    BEDROCK_HAIKU = "bedrock_haiku_nova"
    BEDROCK_FRONTIER = "bedrock_claude_sonnet"


class ModelRoutingResult(BaseModel):
    selected_tier: RoutingTier
    target_model_id: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
    estimated_cost_usd: float
    state_prompt: str


class DeciderModelRouter:
    """
    Sub-115ms Model Router powered by Strands Decider 2B.
    Routes queries to the most cost-effective and latency-optimal model tier.
    """

    MODEL_ID_MAP = {
        RoutingTier.LOCAL_RUNBOOK: "local:strands-runbook-engine",
        RoutingTier.BEDROCK_HAIKU: "amazon.nova-micro-v1:0",
        RoutingTier.BEDROCK_FRONTIER: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    }

    ESTIMATED_COSTS = {
        RoutingTier.LOCAL_RUNBOOK: 0.0000,
        RoutingTier.BEDROCK_HAIKU: 0.0004,
        RoutingTier.BEDROCK_FRONTIER: 0.0065,
    }

    def __init__(
        self,
        client: Optional[StrandsDeciderClient] = None,
        frontier_escalation_threshold: float = 0.60,
    ):
        self.client = client or StrandsDeciderClient()
        self.frontier_escalation_threshold = frontier_escalation_threshold

    def route_request(self, user_prompt: str, telemetry_context: Optional[str] = None) -> ModelRoutingResult:
        """
        Evaluates prompt complexity and returns the optimal model tier.
        """
        state = f"Task: {user_prompt}"
        if telemetry_context:
            state += f"\nTelemetry Context: {telemetry_context}"

        options = [
            RoutingTier.LOCAL_RUNBOOK.value,
            RoutingTier.BEDROCK_HAIKU.value,
            RoutingTier.BEDROCK_FRONTIER.value,
        ]

        questions = {
            "routing_tier": ChoiceQuestion(
                type="choice",
                instructions=(
                    "Does this task require deep root-cause synthesis and creative reasoning (bedrock_claude_sonnet), "
                    "light text formatting (bedrock_haiku_nova), or can it be resolved via a deterministic operational runbook (local_runbook)?"
                ),
                options=options,
            )
        }

        decision = self.client.ask(state=state, questions=questions)
        answer = decision.answers.get("routing_tier")

        if not answer:
            tier = RoutingTier.BEDROCK_FRONTIER
            conf = 0.5
            probs = {}
        else:
            tier = RoutingTier(answer.prediction)
            conf = answer.confidence
            probs = answer.probabilities or {tier.value: conf}

        return ModelRoutingResult(
            selected_tier=tier,
            target_model_id=self.MODEL_ID_MAP[tier],
            confidence=conf,
            probabilities=probs,
            latency_ms=decision.latency_ms,
            estimated_cost_usd=self.ESTIMATED_COSTS[tier],
            state_prompt=state,
        )
