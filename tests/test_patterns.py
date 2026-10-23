"""
Unit Tests: Strands Decider 2B Reusable Decision Patterns
---------------------------------------------------------
Tests #tool-selection, #model-routing, #policy, and #context-memory.
"""

import unittest
from decider_patterns import (
    StrandsDeciderClient,
    DeciderToolSelector,
    ToolDefinition,
    DeciderModelRouter,
    RoutingTier,
    DeciderPolicyClassifier,
    PolicyCategory,
    DeciderContextScorer,
    ContextChunk,
)


class TestReusablePatterns(unittest.TestCase):

    def setUp(self):
        self.client = StrandsDeciderClient(prefer_local_server=False)

    def test_tool_selection_pattern(self):
        """Pattern #tool-selection: Chooses appropriate tool in sub-120ms without LLM prompt."""
        tools = [
            ToolDefinition(name="fetch_cloudwatch_metrics", description="CloudWatch alarms"),
            ToolDefinition(name="scale_auto_scaling_group", description="Scale ASG capacity"),
            ToolDefinition(name="flush_redis_cache", description="Evict Redis cache"),
            ToolDefinition(name="isolate_compromised_instance", description="Quarantine EC2"),
            ToolDefinition(name="remediate_oom_pod", description="Fix EKS OOM pod"),
        ]
        selector = DeciderToolSelector(tools=tools, client=self.client)

        # 1. ASG test
        r1 = selector.select_tool("High CPU spike on payment-asg. Scale to 8.")
        self.assertEqual(r1.selected_tool, "scale_auto_scaling_group")
        self.assertGreater(r1.confidence, 0.6)
        self.assertLess(r1.latency_ms, 250.0)

        # 2. Redis test
        r2 = selector.select_tool("Redis cluster redis-prod latency degraded. Flush stale cache keys.")
        self.assertEqual(r2.selected_tool, "flush_redis_cache")

        # 3. Security test
        r3 = selector.select_tool("GuardDuty miner communication on instance i-09a8b7c6d5e4f3210. Isolate.")
        self.assertEqual(r3.selected_tool, "isolate_compromised_instance")

        # 4. EKS OOM test
        r4 = selector.select_tool("Pod checkout-api crashed with Exit 137 OOMKilled in production.")
        self.assertEqual(r4.selected_tool, "remediate_oom_pod")

    def test_model_routing_pattern(self):
        """Pattern #model-routing: Routes deterministic tasks to runbook vs Bedrock Claude 3.5."""
        router = DeciderModelRouter(client=self.client)

        # Simple operational task -> local runbook ($0 cost)
        r_simple = router.route_request("Scale payment-service-asg to 8 instances.")
        self.assertEqual(r_simple.selected_tier, RoutingTier.LOCAL_RUNBOOK)
        self.assertEqual(r_simple.estimated_cost_usd, 0.0)

        # Deep root-cause analysis -> Bedrock Claude 3.5 Sonnet
        r_complex = router.route_request(
            "Synthesize multi-region root cause analysis across DynamoDB and ECS cascading failures with executive post-mortem."
        )
        self.assertEqual(r_complex.selected_tier, RoutingTier.BEDROCK_FRONTIER)
        self.assertIn("claude", r_complex.target_model_id)

    def test_policy_classifier_pattern(self):
        """Pattern #policy: Categorizes events into operational governance tiers with calibrated probabilities."""
        classifier = DeciderPolicyClassifier(client=self.client)

        # P1 Critical Outage
        p1 = classifier.classify_event("Critical EKS service outage down 500 errors across all availability zones.")
        self.assertEqual(p1.category, PolicyCategory.P1_CRITICAL_OUTAGE)
        self.assertTrue(p1.requires_pagerduty)
        self.assertEqual(p1.sla_minutes, 5)

        # Security Incident
        p_sec = classifier.classify_event("GuardDuty anomaly: unauthorized cryptominer breach detected.")
        self.assertEqual(p_sec.category, PolicyCategory.SECURITY_INCIDENT)
        self.assertTrue(p_sec.requires_pagerduty)

        # P2 Degradation
        p2 = classifier.classify_event("Cache latency warning: Redis response time degraded to 420ms.")
        self.assertEqual(p2.category, PolicyCategory.P2_SERVICE_DEGRADATION)
        self.assertFalse(p2.requires_pagerduty)

    def test_context_scorer_pattern(self):
        """Pattern #context-memory: Injects only relevant runbooks and rejects noisy/unrelated chunks."""
        scorer = DeciderContextScorer(client=self.client, min_score_threshold=2.0)
        chunks = [
            ContextChunk(chunk_id="rb-oom", source="EKS-OOM-Runbook", text="When Exit 137 OOMKilled occurs, increase memory limit to 2Gi."),
            ContextChunk(chunk_id="rb-billing", source="Billing-Unrelated", text="Annual corporate discounts apply to reserved instances in eu-central-1."),
        ]

        results = scorer.score_chunks("EKS deployment checkout-api crashed with Exit 137 OOMKilled", chunks)
        res_by_id = {c.chunk.chunk_id: c for c in results}

        # OOM runbook must be injected
        self.assertTrue(res_by_id["rb-oom"].is_injected)
        self.assertIn(res_by_id["rb-oom"].relevance_label, ["medium", "highly_relevant"])

        # Billing runbook must be filtered out
        self.assertFalse(res_by_id["rb-billing"].is_injected)
        self.assertEqual(res_by_id["rb-billing"].relevance_label, "irrelevant")


if __name__ == "__main__":
    unittest.main()
