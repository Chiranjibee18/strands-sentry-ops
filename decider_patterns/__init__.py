"""
Strands Decider 2B Reusable Decision Patterns Package
------------------------------------------------------
A production-ready library of System 1 decision patterns powered by Strands Decider 2B,
designed for high-frequency, ultra-low latency (sub-115ms), calibrated agentic workflows.
Compatible with the Strands Agents SDK and Amazon Bedrock.

Tags: #strands-decider-2b #guardrails #tool-selection #model-routing #policy #context-memory
"""

__version__ = "1.0.0"

from .client import StrandsDeciderClient, DeciderDecision, DeciderAnswer
from .guardrails import DeciderGuardrailHandler, GuardrailCheckResult
from .tool_selection import DeciderToolSelector, ToolSelectionResult
from .model_routing import DeciderModelRouter, RoutingTier, ModelRoutingResult
from .policy import DeciderPolicyClassifier, PolicyCategory, PolicyClassificationResult
from .context_scorer import DeciderContextScorer, ScoredContextChunk

__all__ = [
    "StrandsDeciderClient",
    "DeciderDecision",
    "DeciderAnswer",
    "DeciderGuardrailHandler",
    "GuardrailCheckResult",
    "DeciderToolSelector",
    "ToolSelectionResult",
    "DeciderModelRouter",
    "RoutingTier",
    "ModelRoutingResult",
    "DeciderPolicyClassifier",
    "PolicyCategory",
    "PolicyClassificationResult",
    "DeciderContextScorer",
    "ScoredContextChunk",
]
