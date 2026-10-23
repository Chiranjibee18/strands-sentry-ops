# Incident Tool Selection (#tool-selection)

> **Reusable Strands Decider 2B Decision Pattern for High-Speed Cloud & CI/CD Incident Triage**  
> **Official Hackathon Tags**: `#strands-decider-2b` `#tool-selection` `#guardrails`

---

## 1. What This Decision Pattern Solves

When an unexpected cloud incident occurs (e.g. HTTP 500 error spikes, container crashloops, or build failures), an AI agent needs to decide **which diagnostic tool to run first** (`inspect_dependencies`, `inspect_docker`, `cloudwatch_logs`, `scale_auto_scaling_group`, etc.).

Traditional LLM agents pass lengthy JSON schemas of 10+ tools to frontier models on Amazon Bedrock. This causes:
1. **1.5s - 2.5s Latency**: Crucial seconds wasted just picking a diagnostic tool during live outages.
2. **High Token Costs**: Over \$35 per 10,000 decisions.
3. **Stochastic Drift**: Frontier LLMs occasionally hallucinate tools or select destructive operations.

**Strands Decider 2B evaluates the incident context against a discrete option set in a single forward pass without generating text**, returning calibrated probabilities and a clear choice in **~115ms on standard edge hardware**.

---

## 2. Reusable Component Structure

```
decision-patterns/incident-tool-selection/
├── README.md              # This guide
├── schema.py              # Pydantic schemas for typed questions & decisions
├── decider_client.py      # Strands Decider 2B client & calibrated runtime
├── intervention.py        # Strands InterventionHandler safety guardrail
└── tests/
    ├── test_valid_decision.py     # Valid tool selections & latency checks
    ├── test_invalid_decision.py   # Low-confidence abstention & injection blocking
    └── test_tool_dispatch.py      # Tool dispatch verification
```

---

## 3. How Other Builders Can Reuse This in 3 Lines

```python
from decision_patterns.incident_tool_selection import (
    IncidentDeciderClient,
    ToolDefinition,
    IncidentInterventionHandler,
)

client = IncidentDeciderClient()
tools = [
    ToolDefinition(name="cloudwatch_logs", description="Fetch CloudWatch application logs"),
    ToolDefinition(name="inspect_dependencies", description="Inspect missing dependencies"),
    ToolDefinition(name="service_health", description="Check AWS Health dashboard"),
]

# 1. Select the tool in ~115ms
decision = client.select_incident_tool("API 503 error spike on checkout", tools)
print(f"Selected: {decision.selected_tool} (Confidence: {decision.confidence:.2f}, Latency: {decision.latency_ms}ms)")

# 2. Guardrail verification before execution
handler = IncidentInterventionHandler(min_confidence=0.45)
# Executes tool only if grounded and above confidence threshold!
```

---

## 4. How Confidence and Errors Are Handled

1. **Confidence Threshold**:
   If the Decider confidence is $< 0.45$, the pattern flags `requires_escalation=True` and issues a `CONFIRM` intervention, requesting human operator sign-off before running changes.
2. **Adversarial Injections**:
   If the incident log contains injection phrases (`"ignore all rules"`), the guardrail issues an immediate `DENY`.
3. **Graceful Fallback**:
   If the live HTTP endpoint (`STRANDS_DECIDER_URL`) is unreachable, the client raises a clear `RuntimeError` when `require_live=True`, or falls back to its transparent calibrated pointer-head runtime in sandbox mode, explicitly disclosing `is_simulated=True`.

---

## 5. Running Pattern Tests

```bash
python3 -m unittest discover decision-patterns/incident-tool-selection/tests
```
