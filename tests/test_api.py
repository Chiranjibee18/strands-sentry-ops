"""
API Integration Tests: FastAPI Endpoints & Strands /v1/systemone API
"""

import unittest
from fastapi.testclient import TestClient
from server.app import app


class TestServerAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["agent"], "Strands Sentry-Ops")
        self.assertIn("#guardrails", data["supported_patterns"])
        self.assertIn("strands_api", data["endpoints"])

    def test_strands_systemone_api_endpoint(self):
        """Tests the official /v1/systemone Decider 2B inference endpoint."""
        payload = {
            "state": "User Intent: Scale payment-service-asg to 8\nTool: scale_auto_scaling_group\nArgs: {\"asg_name\": \"payment-service-asg\", \"desired_capacity\": 8}",
            "questions": {
                "is_grounded": {
                    "type": "noul",
                    "instructions": "Are the tool and arguments strictly grounded in user authorization?",
                }
            },
            "model": "StrandsAgents/strands-decider-2B-qwen3.5-v1-2610",
        }
        resp = self.client.post("/v1/systemone", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("answers", data)
        self.assertIn("is_grounded", data["answers"])
        answer = data["answers"]["is_grounded"]
        self.assertTrue(answer["prediction"])
        self.assertGreaterEqual(answer["confidence"], 0.75)
        self.assertLess(data["latency_ms"], 250.0)

    def test_get_scenarios(self):
        resp = self.client.get("/api/agent/scenarios")
        self.assertEqual(resp.status_code, 200)
        scenarios = resp.json()
        self.assertGreaterEqual(len(scenarios), 5)
        scenario_ids = [s["id"] for s in scenarios]
        self.assertIn("scenario-traffic", scenario_ids)
        self.assertIn("scenario-injection", scenario_ids)
        self.assertIn("scenario-confirm", scenario_ids)

    def test_agent_execute_endpoint(self):
        payload = {
            "query": "High CPU utilization alarm on payment-service-asg (98%). Traffic doubled. Scale ASG capacity to 8 instances."
        }
        resp = self.client.post("/api/agent/execute", json=payload)
        self.assertEqual(resp.status_code, 200)
        report = resp.json()
        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["tool_selection"]["selected_tool"], "scale_auto_scaling_group")
        self.assertGreater(report["total_latency_ms"], 0)
        self.assertGreater(report["equivalent_pure_llm_latency_ms"], 0)

    def test_agent_approve_endpoint(self):
        payload = {
            "request_id": "req-test-approval",
            "tool_name": "scale_auto_scaling_group",
            "tool_args": {"asg_name": "payment-service-asg", "desired_capacity": 10},
            "user_query": "Scale payment-service-asg to 10 instances",
            "operator_note": "Manual approval by SRE Lead",
        }
        resp = self.client.post("/api/agent/approve", json=payload)
        self.assertEqual(resp.status_code, 200)
        report = resp.json()
        self.assertEqual(report["status"], "SUCCESS")
        self.assertIsNotNone(report["tool_executed"])


if __name__ == "__main__":
    unittest.main()
