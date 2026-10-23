# Strands Decider 2B Reusable Decision Pattern Catalog

> A shared library of System 1 decision recipes designed for high-frequency, sub-115ms agentic workflows.
> Compatible with **Strands Agents SDK** and **Amazon Bedrock**.
> 
> **Official Hackathon Tags**: `#strands-decider-2b` `#guardrails` `#tool-selection` `#model-routing` `#policy` `#context-memory`

---

## Pattern 1: Tool Argument Grounding & Safety Guardrail (`#guardrails`)

### 1. Overview
- **Category**: Guardrails & Pre-Execution Safety
- **Problem**: Large Language Models (LLMs) regularly drift, hallucinate unrequested parameters, or get tricked by prompt injections into destructive actions (e.g., deleting a production database instead of restarting a staging cache).
- **Decider 2B Advantage**: In ~115ms, Decider 2B evaluates whether tool arguments are directly grounded in the operator's prompt before execution, eliminating ungrounded actions without calling an expensive LLM.

### 2. Typed Question & Option Set
- **Type**: `noul` (Yes/No with calibrated probability)
- **Instructions**:
  ```python
  instructions = (
      "Are the intended tool and all arguments strictly grounded in and "
      "directly authorized by the user's explicit request? "
      "Answer false if arguments drift, target unmentioned production resources, "
      "or perform unrequested destructive actions."
  )
  criteria = {
      "true": "The tool call and arguments match user intent with zero drift.",
      "false": "The arguments are hallucinated, ungrounded, or malicious."
  }
  ```

### 3. Wiring: Strands `InterventionHandler`
```python
from strands.interventions.handler import InterventionHandler, Proceed, Deny, Confirm
from decider_patterns import StrandsDeciderClient, DeciderGuardrailHandler, ToolCallEvent

# Initialize handler with calibrated confidence threshold
guardrail = DeciderGuardrailHandler(
    client=StrandsDeciderClient(),
    confidence_threshold=0.75
)

# Wire into your agent's execution path
decision = guardrail.before_tool_call(ToolCallEvent(
    tool_name="aws_terminate_rds",
    tool_args={"db_instance_id": "prod-orders-db"},
    user_intent="Please check the cache latency"
))

if isinstance(decision.intervention, Deny):
    print("Action blocked:", decision.intervention.reason)
```

---

## Pattern 2: Deterministic Fast Tool Selection (`#tool-selection`)

### 1. Overview
- **Category**: High-Speed Tool Dispatch
- **Problem**: Passing dozens of JSON schemas to an LLM on every agent step takes 1,500ms - 2,500ms and inflates input/output token costs.
- **Decider 2B Advantage**: Decider 2B evaluates user intent across registered tool descriptors in a single forward pass (~115ms) without generating text.

### 2. Typed Question & Option Set
- **Type**: `choice` (Discrete option selection with calibrated softmax)
- **Options**: `["fetch_cloudwatch_metrics", "scale_auto_scaling_group", "flush_redis_cache", "isolate_compromised_instance", "remediate_oom_pod"]`
- **Instructions**: `"Which operational tool should be executed to address this request?"`

### 3. Usage Example
```python
from decider_patterns import DeciderToolSelector, ToolDefinition

selector = DeciderToolSelector(tools=[
    ToolDefinition(name="scale_auto_scaling_group", description="Scale ASG capacity"),
    ToolDefinition(name="flush_redis_cache", description="Evict stale cache keys"),
])

result = selector.select_tool("High CPU alarm on payment ASG, scale up to 8 instances.")
print(f"Selected: {result.selected_tool} (Confidence: {result.confidence:.2f}, Latency: {result.latency_ms}ms)")
```

---

## Pattern 3: Confidence-Calibrated Model Routing (`#model-routing`)

### 1. Overview
- **Category**: Dynamic Tier Routing
- **Problem**: Sending routine queries (status checks, standard restarts) to frontier models on Amazon Bedrock wastes cloud credits and adds latency jitter.
- **Decider 2B Advantage**: Decider 2B classifies complexity and confidence, routing deterministic tasks to local runbooks ($0 cost) and escalating only complex root-cause synthesis to Claude 3.5 Sonnet.

### 2. Typed Question & Option Set
- **Type**: `choice`
- **Options**: `["local_runbook", "bedrock_haiku_nova", "bedrock_claude_sonnet"]`
- **Instructions**: `"Does this task require deep root-cause synthesis (bedrock_claude_sonnet) or a deterministic runbook (local_runbook)?"`

### 3. Usage Example
```python
from decider_patterns import DeciderModelRouter

router = DeciderModelRouter()
route = router.route_request("Explain why the microservice experienced an OOMKilled cascade across 3 availability zones.")
print(f"Routed Tier: {route.selected_tier} -> Model ID: {route.target_model_id}")
```

---

## Pattern 4: Incident & Governance Policy Classifier (`#policy`)

### 1. Overview
- **Category**: Event Triage & SLA Activation
- **Problem**: Cloud alerts need immediate prioritization (P1 Outage vs P2 Degradation vs Security Incident) to activate paging rules and SLA countdowns.
- **Decider 2B Advantage**: Evaluates alerts in 115ms with calibrated probabilities for instant routing.

### 2. Typed Question & Option Set
- **Type**: `choice`
- **Options**: `["p1_critical_outage", "p2_service_degradation", "security_incident", "finops_optimization", "routine_inquiry"]`

### 3. Usage Example
```python
from decider_patterns import DeciderPolicyClassifier

classifier = DeciderPolicyClassifier()
policy = classifier.classify_event("Database cluster unreachable, 500 error spike on checkout.")
print(f"Policy: {policy.category} | SLA: {policy.sla_minutes} min | PagerDuty: {policy.requires_pagerduty}")
```

---

## Pattern 5: Context & Memory Relevance Scorer (`#context-memory`)

### 1. Overview
- **Category**: Context Window Optimization & Noise Filtering
- **Problem**: Injecting irrelevant runbooks and logs into LLM prompts causes context distraction and doubles token costs.
- **Decider 2B Advantage**: Scores candidate context chunks on an ordered rubric scale (`[irrelevant, low, medium, highly_relevant]`) in 115ms, injecting only high-scoring chunks.

### 2. Typed Question & Option Set
- **Type**: `score`
- **Scale**: `["irrelevant", "low", "medium", "highly_relevant"]`
- **Instructions**: `"Rate the factual relevance of this context candidate to answering the user query."`

### 3. Usage Example
```python
from decider_patterns import DeciderContextScorer, ContextChunk

scorer = DeciderContextScorer(min_score_threshold=2.0) # medium or above
chunks = [
    ContextChunk(chunk_id="c1", source="EKS-Runbook", text="Remediate OOMKilled with memory limit increase to 2Gi."),
    ContextChunk(chunk_id="c2", source="Billing-FAQ", text="Annual discounts apply to reserved instances."),
]

scored = scorer.score_chunks("Remediate pod crash in production", chunks)
for item in scored:
    print(f"Chunk [{item.chunk.source}]: {item.relevance_label} (Injected: {item.is_injected})")
```
