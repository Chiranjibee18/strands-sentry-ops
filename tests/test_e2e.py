"""
Phase 5.4: End-to-End Pipeline Tests
------------------------------------
Tests complete autonomous lifecycle:
Log Ingest -> Policy Triage -> Model Routing -> Tool Selection -> Memory Scoring
-> Guardrail -> Tool Execution -> Generative Synthesis
"""

import unittest
from agent.sentry_agent import StrandsSentryAgent, AgentExecutionReport


class TestEndToEndPipeline(unittest.TestCase):

    def setUp(self):
        self.agent = StrandsSentryAgent()

    def test_e2e_dependency_failure(self):
        log = "Traceback (most recent call last):\n  File 'manage.py', line 10\nModuleNotFoundError: No module named 'django'"
        report: AgentExecutionReport = self.agent.handle_request(log)

        self.assertEqual(report.status, "SUCCESS")
        self.assertEqual(report.tool_selection.selected_tool, "inspect_dependencies")
        self.assertIsNotNone(report.tool_executed)
        self.assertEqual(report.tool_executed.tool_name, "inspect_dependencies")
        self.assertIn("django", report.tool_executed.output["missing_items"])
        self.assertTrue(len(report.steps) >= 5)

    def test_e2e_docker_build_failure(self):
        log = "Step 3/8 : RUN apk update\nfailed to solve: Dockerfile parse error line 14: unknown instruction"
        report: AgentExecutionReport = self.agent.handle_request(log)

        self.assertEqual(report.status, "SUCCESS")
        self.assertEqual(report.tool_selection.selected_tool, "inspect_docker")
        self.assertIsNotNone(report.tool_executed)
        self.assertEqual(report.tool_executed.tool_name, "inspect_docker")

    def test_e2e_test_assertion_failure(self):
        log = "pytest FAILED tests/test_api.py::test_checkout - AssertionError: expected 200 got 500"
        report: AgentExecutionReport = self.agent.handle_request(log)

        self.assertEqual(report.status, "SUCCESS")
        self.assertEqual(report.tool_selection.selected_tool, "inspect_tests")
        self.assertIsNotNone(report.tool_executed)
        self.assertEqual(report.tool_executed.tool_name, "inspect_tests")

    def test_e2e_pipeline_failure(self):
        log = "workflow.yaml: mapping values are not allowed here at line 24 column 7"
        report: AgentExecutionReport = self.agent.handle_request(log)

        self.assertEqual(report.status, "SUCCESS")
        self.assertEqual(report.tool_selection.selected_tool, "inspect_pipeline")
        self.assertIsNotNone(report.tool_executed)
        self.assertEqual(report.tool_executed.tool_name, "inspect_pipeline")

    def test_e2e_cloud_ops_scaling(self):
        query = "CloudWatch Alarm: High CPU utilization on payment-service-asg (98%). Scale ASG capacity to 8 instances."
        report: AgentExecutionReport = self.agent.handle_request(query)

        self.assertEqual(report.status, "SUCCESS")
        self.assertEqual(report.tool_selection.selected_tool, "scale_auto_scaling_group")
        self.assertIsNotNone(report.tool_executed)
        self.assertEqual(report.tool_executed.output["new_desired_capacity"], 8)
        self.assertIsNotNone(report.bedrock_rca)


if __name__ == "__main__":
    unittest.main()
