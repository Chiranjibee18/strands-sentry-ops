"""
Reusable Decision Pattern: #tool-selection
-------------------------------------------
Pattern Name: Decider 2B Fast Tool Selector
Tag: #tool-selection, #strands-decider-2b

Problem:
Standard agent harnesses send the full list of tool JSON schemas to a large
language model (e.g., Claude 3.5 Sonnet on Amazon Bedrock) on every turn.
The LLM must parse schemas, reason, and generate structured output tokens,
resulting in 1,500ms - 2,500ms latency and high token inference cost just to
determine which tool to call.

Solution:
Strands Decider 2B evaluates the user input against a discrete set of available
tool names in a single forward pass (~115ms) without generating text.
It returns the chosen tool along with calibrated probability distribution across
all options. If confidence is below threshold, it falls back to Bedrock for
ambiguous multi-tool synthesis.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .client import StrandsDeciderClient, ChoiceQuestion


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


class ToolSelectionResult(BaseModel):
    selected_tool: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
    should_escalate_to_llm: bool = False
    state_prompt: str


class DeciderToolSelector:
    """
    Sub-115ms Tool Selector powered by Strands Decider 2B.
    
    How to use in your agent:
    -------------------------
    selector = DeciderToolSelector(tools=[
        ToolDefinition(name="fetch_cloudwatch_metrics", description="Retrieve CPU/memory alarms"),
        ToolDefinition(name="isolate_compromised_instance", description="Quarantine EC2 instance"),
        ToolDefinition(name="scale_auto_scaling_group", description="Scale ASG capacity up or down"),
        ToolDefinition(name="flush_redis_cache", description="Evict stale cache keys")
    ])
    result = selector.select_tool("High CPU alarm on payment service ASG! Traffic doubled.")
    print("Selected Tool:", result.selected_tool)
    """

    def __init__(
        self,
        tools: List[ToolDefinition],
        client: Optional[StrandsDeciderClient] = None,
        confidence_threshold: float = 0.65,
    ):
        self.tools = tools
        self.tool_names = [t.name for t in tools]
        self.tool_map = {t.name: t for t in tools}
        self.client = client or StrandsDeciderClient()
        self.confidence_threshold = confidence_threshold

    def select_tool(self, user_intent: str, context: Optional[str] = None) -> ToolSelectionResult:
        """
        Determines the most appropriate tool to handle user_intent in ~115ms.
        """
        state = f"User Request: {user_intent}"
        if context:
            state += f"\nContext: {context}"

        # Build typed choice question
        questions = {
            "chosen_tool": ChoiceQuestion(
                type="choice",
                instructions="Which operational tool should be executed to address this request?",
                options=self.tool_names,
            )
        }

        decision = self.client.ask(state=state, questions=questions)
        answer = decision.answers.get("chosen_tool")

        if not answer:
            return ToolSelectionResult(
                selected_tool=self.tool_names[0] if self.tool_names else "none",
                confidence=0.0,
                probabilities={},
                latency_ms=decision.latency_ms,
                should_escalate_to_llm=True,
                state_prompt=state,
            )

        selected = str(answer.prediction)
        confidence = answer.confidence
        probabilities = answer.probabilities or {selected: confidence}
        should_escalate = confidence < self.confidence_threshold

        return ToolSelectionResult(
            selected_tool=selected,
            confidence=confidence,
            probabilities=probabilities,
            latency_ms=decision.latency_ms,
            should_escalate_to_llm=should_escalate,
            state_prompt=state,
        )
