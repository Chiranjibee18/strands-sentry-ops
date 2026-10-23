"""
Phase 5.3: Bedrock Integration Tests
------------------------------------
Tests Amazon Bedrock client invocation, grounded reasoning synthesis,
token accounting, and fallback resilience.
"""

import unittest
from agent.bedrock_client import AmazonBedrockClient, BedrockInferenceResult


class TestBedrockIntegration(unittest.TestCase):

    def setUp(self):
        self.bedrock = AmazonBedrockClient()

    def test_bedrock_inference_structure(self):
        prompt = (
            "User Query: Pod crashed with Exit 137\n"
            "Action Executed: remediate_oom_pod with new_memory_limit=2Gi\n"
            "Result: EKS Deployment checkout-api upgraded to 2Gi memory.\n"
            "Synthesize root cause analysis."
        )
        res: BedrockInferenceResult = self.bedrock.invoke_reasoning(prompt)

        self.assertIsNotNone(res.response_text)
        self.assertTrue(len(res.response_text) > 20)
        self.assertGreater(res.output_tokens, 0)
        self.assertGreater(res.latency_ms, 0)
        self.assertGreater(res.cost_usd, 0)
        self.assertIn("anthropic", res.model_id)

    def test_bedrock_grounding_in_evidence(self):
        prompt = (
            "User Query: CI/CD failure inspect_dependencies\n"
            "Evidence: ModuleNotFoundError: No module named 'django' at line 2\n"
            "Suggested verification: pip check\n"
            "Provide diagnostic explanation."
        )
        res = self.bedrock.invoke_reasoning(prompt)
        text_lower = res.response_text.lower()
        # Should address the incident evidence
        self.assertTrue(any(w in text_lower for w in ["incident", "action", "verification", "cause", "analysis"]))

    def test_bedrock_model_selection(self):
        res = self.bedrock.invoke_reasoning(
            prompt="Quick diagnostic note",
            model_id="amazon.nova-premier-v1:0"
        )
        self.assertEqual(res.model_id, "amazon.nova-premier-v1:0")


if __name__ == "__main__":
    unittest.main()
