"""
Strands Sentry-Ops Agent Orchestrator
------------------------------------
Orchestrates the hybrid System 1 (Strands Decider 2B) and System 2 (Amazon Bedrock)
autonomous cloud operations lifecycle.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time

from decider_patterns import (
    StrandsDeciderClient,
    DeciderGuardrailHandler,
    DeciderToolSelector,
    DeciderModelRouter,
    DeciderPolicyClassifier,
    DeciderContextScorer,
)
from decider_patterns.guardrails import ToolCallEvent, Proceed, Deny, Confirm, Guide, GuardrailCheckResult
from decider_patterns.tool_selection import ToolDefinition, ToolSelectionResult
from decider_patterns.model_routing import ModelRoutingResult, RoutingTier
from decider_patterns.policy import PolicyClassificationResult
from decider_patterns.context_scorer import ContextChunk, ScoredContextChunk
from .tools import ALL_AVAILABLE_TOOLS, ToolResult
from .bedrock_client import AmazonBedrockClient, BedrockInferenceResult
from .security import redact_secrets, validate_input_log, detect_prompt_injection


class StepTelemetry(BaseModel):
    step_name: str
    component: str  # "Strands Decider 2B" or "Amazon Bedrock" or "Local Tool"
    pattern_tag: Optional[str] = None  # e.g., "#guardrails", "#tool-selection"
    decision_type: str  # "choice", "noul", "score", "generative"
    prediction: Any
    confidence: float
    latency_ms: float
    cost_usd: float
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionReport(BaseModel):
    request_id: str
    user_query: str
    policy: PolicyClassificationResult
    routing: ModelRoutingResult
    tool_selection: ToolSelectionResult
    guardrail: GuardrailCheckResult
    tool_executed: Optional[ToolResult] = None
    bedrock_rca: Optional[BedrockInferenceResult] = None
    status: str  # "SUCCESS", "BLOCKED_BY_GUARDRAIL", "REQUIRES_APPROVAL", "FAILED"
    total_latency_ms: float
    total_cost_usd: float
    equivalent_pure_llm_cost_usd: float
    equivalent_pure_llm_latency_ms: float = 7400.0
    cost_savings_percent: float
    latency_savings_percent: float
    steps: List[StepTelemetry]


class StrandsSentryAgent:
    """
    Autonomous AWS Cloud Operations & CI/CD Security Agent.
    Combines Strands Decider 2B with Amazon Bedrock.
    """

    AVAILABLE_TOOLS = [
        # CI/CD Diagnostic Tools (#tool-selection)
        ToolDefinition(name="inspect_dependencies", description="Inspect missing Python/Node packages or dependency resolution conflicts"),
        ToolDefinition(name="inspect_docker", description="Inspect Dockerfile syntax errors, storage exhaustion, or container image builds"),
        ToolDefinition(name="inspect_tests", description="Inspect test suite AssertionErrors, expectation mismatches, or traceback failures"),
        ToolDefinition(name="inspect_pipeline", description="Inspect CI/CD pipeline definitions, workflow.yaml syntax, or runner permissions"),
        # Cloud Operations & SRE Tools
        ToolDefinition(name="fetch_cloudwatch_metrics", description="Retrieve live CloudWatch alarms and telemetry"),
        ToolDefinition(name="scale_auto_scaling_group", description="Scale EC2 Auto Scaling Group capacity up or down"),
        ToolDefinition(name="flush_redis_cache", description="Evict stale cache keys from ElastiCache Redis cluster"),
        ToolDefinition(name="isolate_compromised_instance", description="Quarantine compromised EC2 instance into security group"),
        ToolDefinition(name="remediate_oom_pod", description="Update Kubernetes pod memory limits on EKS to fix OOMKilled"),
        ToolDefinition(name="terminate_rds_database", description="HIGH RISK: Delete Amazon RDS database instance"),
    ]

    RUNBOOK_CHUNKS = [
        ContextChunk(chunk_id="rb-01", source="EKS-OOM-Runbook", text="When Exit 137 OOMKilled occurs, increase memory limits from 512Mi to 2Gi and perform rolling restart."),
        ContextChunk(chunk_id="rb-02", source="ASG-Scale-Runbook", text="When CPU utilization > 80% for 3 periods, increase ASG desired capacity by +4 instances to absorb traffic burst."),
        ContextChunk(chunk_id="rb-03", source="Redis-Evict-Runbook", text="When Redis P99 latency degrades > 400ms, flush stale DB index keys to prevent fragmentation."),
        ContextChunk(chunk_id="rb-04", source="Security-IR-Runbook", text="When anomalous miner outbound traffic is detected, immediately attach zero-egress forensic quarantine security group."),
        ContextChunk(chunk_id="rb-05", source="Billing-Unrelated", text="Annual corporate discounts apply to reserved instances in eu-central-1."),
    ]

    def __init__(self, decider_client: Optional[StrandsDeciderClient] = None):
        self.decider = decider_client or StrandsDeciderClient()
        self.bedrock = AmazonBedrockClient()

        # Initialize Decision Patterns
        self.policy_classifier = DeciderPolicyClassifier(self.decider)
        self.model_router = DeciderModelRouter(self.decider)
        self.tool_selector = DeciderToolSelector(self.AVAILABLE_TOOLS, self.decider)
        self.context_scorer = DeciderContextScorer(self.decider)
        self.guardrail = DeciderGuardrailHandler(self.decider)

    def handle_request(self, user_query: str, proposed_args: Optional[Dict[str, Any]] = None) -> AgentExecutionReport:
        """
        Executes the full agent loop for an operational or diagnostic request.
        """
        # Step 0: Input Bounds Validation & Secret Redaction
        validated_query, input_meta = validate_input_log(user_query)
        sanitized_query, redactions = redact_secrets(validated_query)
        has_injection, injection_msg = detect_prompt_injection(validated_query)

        t_start = time.perf_counter()
        req_id = f"req-{int(time.time()*1000)}"
        steps: List[StepTelemetry] = []
        total_cost = 0.0

        # Step 1: Policy Classification (#policy) - Strands Decider 2B
        policy_res = self.policy_classifier.classify_event(sanitized_query)
        steps.append(
            StepTelemetry(
                step_name="1. Operational Policy Classification",
                component="Strands Decider 2B",
                pattern_tag="#policy",
                decision_type="choice",
                prediction=policy_res.category.value,
                confidence=policy_res.confidence,
                latency_ms=policy_res.latency_ms,
                cost_usd=0.00000,
                details={"sla_minutes": policy_res.sla_minutes, "pagerduty": policy_res.requires_pagerduty},
            )
        )

        # Step 2: Model Routing (#model-routing) - Strands Decider 2B
        routing_res = self.model_router.route_request(sanitized_query)
        steps.append(
            StepTelemetry(
                step_name="2. Confidence Model Routing",
                component="Strands Decider 2B",
                pattern_tag="#model-routing",
                decision_type="choice",
                prediction=routing_res.selected_tier.value,
                confidence=routing_res.confidence,
                latency_ms=routing_res.latency_ms,
                cost_usd=0.00000,
                details={"target_model_id": routing_res.target_model_id},
            )
        )

        # Step 3: Fast Tool Selection (#tool-selection) - Strands Decider 2B
        tool_res = self.tool_selector.select_tool(sanitized_query)
        steps.append(
            StepTelemetry(
                step_name="3. Deterministic Tool Selection",
                component="Strands Decider 2B",
                pattern_tag="#tool-selection",
                decision_type="choice",
                prediction=tool_res.selected_tool,
                confidence=tool_res.confidence,
                latency_ms=tool_res.latency_ms,
                cost_usd=0.00000,
                details={"probabilities": tool_res.probabilities},
            )
        )

        # Step 4: Context & Memory Scoring (#context-memory) - Strands Decider 2B
        scored_chunks = self.context_scorer.score_chunks(sanitized_query, self.RUNBOOK_CHUNKS)
        injected_chunks = [c for c in scored_chunks if c.is_injected]
        steps.append(
            StepTelemetry(
                step_name="4. Memory & Context Scoring",
                component="Strands Decider 2B",
                pattern_tag="#context-memory",
                decision_type="score",
                prediction=f"{len(injected_chunks)}/{len(scored_chunks)} chunks injected",
                confidence=round(sum(c.confidence for c in scored_chunks) / len(scored_chunks), 2),
                latency_ms=round(sum(c.latency_ms for c in scored_chunks) / len(scored_chunks), 1),
                cost_usd=0.00000,
                details={"injected_sources": [c.chunk.source for c in injected_chunks]},
            )
        )

        # Synthesize tool arguments if not explicitly provided
        args = proposed_args or self._derive_default_args(tool_res.selected_tool, sanitized_query)

        # Step 5: Grounding & Safety Guardrail Check (#guardrails) - Strands Decider 2B
        tool_event = ToolCallEvent(
            tool_name=tool_res.selected_tool,
            tool_args=args,
            user_intent=sanitized_query,
            session_id=req_id,
        )
        guardrail_res = self.guardrail.before_tool_call(tool_event)
        steps.append(
            StepTelemetry(
                step_name="5. Tool Argument Grounding Guardrail",
                component="Strands Decider 2B",
                pattern_tag="#guardrails",
                decision_type="noul",
                prediction=guardrail_res.intervention.action,
                confidence=guardrail_res.confidence,
                latency_ms=guardrail_res.latency_ms,
                cost_usd=0.00000,
                details={
                    "is_grounded": guardrail_res.is_grounded,
                    "args": args,
                    "has_injection_directive": has_injection,
                    "redacted_secrets": redactions,
                },
            )
        )

        # Check Intervention Action & Strict Bounded Execution
        tool_output: Optional[ToolResult] = None
        bedrock_rca: Optional[BedrockInferenceResult] = None
        status = "SUCCESS"

        if tool_res.selected_tool not in ALL_AVAILABLE_TOOLS:
            status = "REJECTED_UNKNOWN_TOOL"
        elif tool_res.confidence < 0.35:
            status = "NEEDS_OPERATOR_REVIEW"
        elif isinstance(guardrail_res.intervention, Deny):
            status = "BLOCKED_BY_GUARDRAIL"
        elif isinstance(guardrail_res.intervention, Confirm):
            status = "REQUIRES_APPROVAL"
        else:
            # Step 6: Tool Execution (Safe, Grounded & Allowlisted!)
            tool_fn = ALL_AVAILABLE_TOOLS.get(tool_res.selected_tool)
            if tool_fn:
                try:
                    tool_output = tool_fn(**args)
                    steps.append(
                        StepTelemetry(
                            step_name=f"6. Execute Tool '{tool_res.selected_tool}'",
                            component="Local AWS Tool Execution",
                            pattern_tag=None,
                            decision_type="execution",
                            prediction=tool_output.message,
                            confidence=1.0,
                            latency_ms=tool_output.execution_time_ms,
                            cost_usd=0.00000,
                            details=tool_output.output,
                        )
                    )
                except Exception as e:
                    status = "FAILED"

            # Step 7: Amazon Bedrock Generative RCA & Post-Mortem (System 2)
            # Only escalate to Bedrock when deep synthesis is required or P1 incident
            if routing_res.selected_tier == RoutingTier.BEDROCK_FRONTIER or policy_res.category.value in [
                "p1_critical_outage", "security_incident"
            ]:
                context_text = "\n".join([f"[{c.chunk.source}]: {c.chunk.text}" for c in injected_chunks])
                bedrock_prompt = (
                    f"User Query: {user_query}\n"
                    f"Action Executed: {tool_res.selected_tool} with {args}\n"
                    f"Result: {tool_output.message if tool_output else 'No output'}\n"
                    f"Reference Runbooks:\n{context_text}\n"
                    "Provide a synthesized root cause analysis, action verification, and post-incident remediation summary."
                )
                bedrock_rca = self.bedrock.invoke_reasoning(bedrock_prompt)
                total_cost += bedrock_rca.cost_usd
                steps.append(
                    StepTelemetry(
                        step_name="7. Amazon Bedrock Generative RCA & Post-Mortem",
                        component="Amazon Bedrock (Claude 3.5 Sonnet)",
                        pattern_tag="#generative-rca",
                        decision_type="generative",
                        prediction=f"Generated {bedrock_rca.output_tokens} tokens of deep RCA report",
                        confidence=0.99,
                        latency_ms=bedrock_rca.latency_ms,
                        cost_usd=bedrock_rca.cost_usd,
                        details={"model_id": bedrock_rca.model_id, "tokens": bedrock_rca.output_tokens},
                    )
                )

        total_latency = (time.perf_counter() - t_start) * 1000.0

        # Comparative Metrics: What if all 5 decisions had been sent to Bedrock?
        pure_llm_cost = (4 * 0.0042) + (total_cost if bedrock_rca else 0.0042)
        pure_llm_latency = (4 * 1850.0) + (bedrock_rca.latency_ms if bedrock_rca else 1850.0)
        
        cost_savings = max(0.0, (pure_llm_cost - total_cost) / pure_llm_cost * 100.0)
        latency_savings = max(0.0, (pure_llm_latency - total_latency) / pure_llm_latency * 100.0)

        return AgentExecutionReport(
            request_id=req_id,
            user_query=sanitized_query,
            policy=policy_res,
            routing=routing_res,
            tool_selection=tool_res,
            guardrail=guardrail_res,
            tool_executed=tool_output,
            bedrock_rca=bedrock_rca,
            status=status,
            total_latency_ms=round(total_latency, 1),
            total_cost_usd=round(total_cost, 6),
            equivalent_pure_llm_cost_usd=round(pure_llm_cost, 6),
            equivalent_pure_llm_latency_ms=round(pure_llm_latency, 1),
            cost_savings_percent=round(cost_savings, 1),
            latency_savings_percent=round(latency_savings, 1),
            steps=steps,
        )

    def execute_confirmed_action(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_query: str,
        operator_note: str = "Authorized by human operator sign-off",
    ) -> AgentExecutionReport:
        """
        Executes an action that was previously pending human confirmation (CONFIRM),
        injecting explicit operator override authorization.
        """
        confirmed_prompt = f"{user_query} [CONFIRMED: {operator_note}]"
        return self.handle_request(user_query=confirmed_prompt, proposed_args=tool_args)

    def _derive_default_args(self, tool_name: str, query: str) -> Dict[str, Any]:
        """Maps operational tool defaults and dynamically parses entities from query text."""
        import re
        q_lower = query.lower()

        if tool_name == "scale_auto_scaling_group":
            asg_match = re.search(r"([a-zA-Z0-9_\-]+(?:-asg|_asg))", query, re.IGNORECASE)
            asg_name = asg_match.group(1) if asg_match else "payment-service-asg"
            cap_match = re.search(r"(?:to|capacity|scale\s+to)\s+(\d+)", query, re.IGNORECASE)
            capacity = int(cap_match.group(1)) if cap_match else 8
            return {"asg_name": asg_name, "desired_capacity": capacity}

        elif tool_name == "flush_redis_cache":
            cluster_match = re.search(r"([a-zA-Z0-9_\-]+(?:-cache|-redis|redis-[a-zA-Z0-9_\-]+))", query, re.IGNORECASE)
            cluster_id = cluster_match.group(1) if cluster_match else "redis-prod-cache-01"
            db_match = re.search(r"db\[?(\d+)\]?", query, re.IGNORECASE)
            db_idx = int(db_match.group(1)) if db_match else 0
            return {"cluster_id": cluster_id, "db_index": db_idx}

        elif tool_name == "isolate_compromised_instance":
            inst_match = re.search(r"(i-[0-9a-fA-F]{8,17})", query)
            instance_id = inst_match.group(1) if inst_match else "i-09a8b7c6d5e4f3210"
            vpc_match = re.search(r"(vpc-[0-9a-fA-F]{8,17})", query)
            vpc_id = vpc_match.group(1) if vpc_match else "vpc-prod-01"
            return {"instance_id": instance_id, "vpc_id": vpc_id}

        elif tool_name == "remediate_oom_pod":
            dep_match = re.search(r"(?:deployment|pod)\s+([a-zA-Z0-9_\-]+)", query, re.IGNORECASE)
            deployment = dep_match.group(1) if dep_match else "checkout-api"
            ns_match = re.search(r"(?:in|namespace)\s+([a-zA-Z0-9_\-]+)(?:\s+namespace)?", query, re.IGNORECASE)
            namespace = ns_match.group(1) if ns_match else "production"
            mem_match = re.search(r"(\d+[MG]i?)", query, re.IGNORECASE)
            mem_limit = mem_match.group(1) if mem_match else "2Gi"
            return {"namespace": namespace, "deployment_name": deployment, "new_memory_limit": mem_limit}

        elif tool_name == "fetch_cloudwatch_metrics":
            svc_match = re.search(r"(?:service|on)\s+([a-zA-Z0-9_\-]+)", query, re.IGNORECASE)
            svc_name = svc_match.group(1) if svc_match else "payment-service"
            metric = "CPUUtilization"
            if "memory" in q_lower:
                metric = "MemoryUtilization"
            elif "latency" in q_lower:
                metric = "TargetResponseTime"
            return {"service_name": svc_name, "metric_name": metric}

        elif tool_name in ["inspect_dependencies", "inspect_docker", "inspect_tests", "inspect_pipeline"]:
            return {"log_text": query}

        elif tool_name == "terminate_rds_database":
            db_match = re.search(r"(?:database|db|rds)\s+([a-zA-Z0-9_\-]+)", query, re.IGNORECASE)
            db_id = db_match.group(1) if db_match else "prod-customer-db"
            return {"db_instance_id": db_id}

        return {}
