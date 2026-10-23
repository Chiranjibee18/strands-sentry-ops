"""
Strands Decider 2B Reusable Decision Patterns Package
------------------------------------------------------
A production-ready library of System 1 decision patterns powered by Strands Decider 2B,
designed for high-frequency, ultra-low latency (sub-115ms), calibrated agentic workflows.
Compatible with the Strands Agents SDK and Amazon Bedrock.

Tags: #strands-decider-2b #guardrails #tool-selection #model-routing #policy #context-memory
"""

__version__ = "1.0.0"

from .client import StrandsDeciderClient, DeciderDecision, DeciderAnswer, NoulQuestion, ChoiceQuestion, ScoreQuestion
from .guardrails import (
    DeciderGuardrailHandler,
    GuardrailCheckResult,
    ToolCallEvent,
    Proceed,
    Deny,
    Confirm,
    Guide,
    InterventionHandler,
)
from .tool_selection import DeciderToolSelector, ToolSelectionResult, ToolDefinition
from .model_routing import DeciderModelRouter, RoutingTier, ModelRoutingResult
from .policy import DeciderPolicyClassifier, PolicyCategory, PolicyClassificationResult
from .context_scorer import DeciderContextScorer, ScoredContextChunk, ContextChunk

__all__ = [
    "StrandsDeciderClient",
    "DeciderDecision",
    "DeciderAnswer",
    "NoulQuestion",
    "ChoiceQuestion",
    "ScoreQuestion",
    "DeciderGuardrailHandler",
    "GuardrailCheckResult",
    "ToolCallEvent",
    "Proceed",
    "Deny",
    "Confirm",
    "Guide",
    "InterventionHandler",
    "DeciderToolSelector",
    "ToolSelectionResult",
    "ToolDefinition",
    "DeciderModelRouter",
    "RoutingTier",
    "ModelRoutingResult",
    "DeciderPolicyClassifier",
    "PolicyCategory",
    "PolicyClassificationResult",
    "DeciderContextScorer",
    "ScoredContextChunk",
    "ContextChunk",
]
