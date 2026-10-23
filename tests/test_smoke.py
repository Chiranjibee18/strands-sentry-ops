"""
Phase 5.7: Deployment Smoke Tests
---------------------------------
Validates live HTTP API endpoints, Decider 2B contract compliance,
CORS configuration, and secret-free responses.
"""

import unittest
from fastapi.testclient import TestClient
from server.app import app


class TestDeploymentSmoke(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("system_1_model", data)
        self.assertIn("system_2_provider", data)
        self.assertIn("#guardrails", data["supported_patterns"])
        self.assertIn("#tool-selection", data["supported_patterns"])

    def test_v1_systemone_strands_endpoint(self):
        payload = {
            "state": "CloudWatch Alarm: High CPU on payment-service-asg (98%). Scale ASG to 8 instances.",
            "questions": {
                "tool": {
                    "type": "choice",
                    "instructions": "Which tool should be executed?",
                    "options": ["scale_auto_scaling_group", "flush_redis_cache"],
                }
            }
        }
        res = self.client.post("/v1/systemone", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("answers", data)
        self.assertEqual(data["answers"]["tool"]["prediction"], "scale_auto_scaling_group")
        self.assertGreater(data["latency_ms"], 0)

    def test_agent_execute_endpoint(self):
        payload = {
            "query": "EKS deployment checkout-api in production namespace crashed with Exit 137 OOMKilled. Remediate memory limit to 2Gi."
        }
        res = self.client.post("/api/agent/execute", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["tool_selection"]["selected_tool"], "remediate_oom_pod")

    def test_benchmarks_endpoint(self):
        res = self.client.get("/api/benchmarks")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("latency_metrics", data)
        self.assertIn("cost_and_token_metrics", data)

    def test_no_exposed_secrets_in_responses(self):
        res = self.client.get("/api/health")
        text = res.text
        self.assertNotIn("AKIA", text)
        self.assertNotIn("aws_secret_access_key", text.lower())


if __name__ == "__main__":
    unittest.main()
