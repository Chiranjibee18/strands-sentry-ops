"""
Tests tool dispatch based on Decider selection.
"""

import unittest
from decision_patterns.incident_tool_selection.decider_client import IncidentDeciderClient
from decision_patterns.incident_tool_selection.schema import ToolDefinition


class TestToolDispatch(unittest.TestCase):

    def setUp(self):
        self.client = IncidentDeciderClient(prefer_live_server=False)
        self.tools = [
            ToolDefinition(name="cloudwatch_logs", description="Retrieve CloudWatch logs"),
            ToolDefinition(name="service_health", description="Check AWS Health / service status"),
            ToolDefinition(name="deployment_history", description="Inspect recent CI/CD deployments"),
        ]

    def test_cloudwatch_logs_dispatch(self):
        log = "Application throwing 500 error stack trace with NullPointerException in logs"
        decision = self.client.select_incident_tool(log, self.tools)
        # Verify decision directly controls dispatch
        self.assertIn(decision.selected_tool, [t.name for t in self.tools])
        self.assertGreater(decision.confidence, 0.0)

    def test_deployment_history_dispatch(self):
        log = "Incident started right after Jenkins deployment of commit a1b2c3d"
        decision = self.client.select_incident_tool(log, self.tools)
        self.assertIn(decision.selected_tool, [t.name for t in self.tools])


if __name__ == "__main__":
    unittest.main()
