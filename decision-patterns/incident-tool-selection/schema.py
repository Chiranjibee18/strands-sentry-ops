"""
Decision Pattern: Incident Tool Selection (#tool-selection)
Schema Definitions
-----------------------------------------------------------
Defines typed request and response schemas for Strands Decider 2B.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    risk_level: str = "read_only"  # "read_only", "remediation", "destructive"
    parameters: Optional[Dict[str, Any]] = None


class ChoiceQuestion(BaseModel):
    type: str = "choice"
    instructions: str
    options: List[str]


class NoulQuestion(BaseModel):
    type: str = "noul"
    instructions: str
    criteria: Dict[str, str] = Field(
        default_factory=lambda: {
            "true": "The tool call and arguments match user intent with zero drift.",
            "false": "The arguments are ungrounded, malicious, or drift out of scope.",
        }
    )


class DeciderAnswer(BaseModel):
    type: str
    prediction: Any
    confidence: float
    probability: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    reasoning_summary: Optional[str] = None


class ToolSelectionDecision(BaseModel):
    selected_tool: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
    requires_escalation: bool
    incident_state: str
