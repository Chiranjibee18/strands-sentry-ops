"""
Tests valid incident tool selection decisions.
"""

import unittest
from decision_patterns.incident_tool_selection.decider_client import IncidentDeciderClient
from decision_patterns.incident_tool_selection.schema import ToolDefinition


class TestValidDecision(unittest.TestCase):

    def setUp(self):
        self.client = IncidentDeciderClient(prefer_live_server=False)
        self.tools = [
            ToolDefinition(name="inspect_dependencies", description="Inspect missing dependencies"),
            ToolDefinition(name="inspect_docker", description="Inspect docker build errors"),
            ToolDefinition(name="scale_auto_scaling_group", description="Scale ASG capacity"),
        ]

    def test_dependency_decision(self):
        log = "ModuleNotFoundError: No module named 'django'"
        decision = self.client.select_incident_tool(log, self.tools)
        self.assertEqual(decision.selected_tool, "inspect_dependencies")
        self.assertGreater(decision.confidence, 0.5)
        self.assertFalse(decision.requires_escalation)
        self.assertLess(decision.latency_ms, 200.0)

    def test_asg_scale_decision(self):
        log = "CloudWatch Alarm: High CPU utilization on payment-service-asg (98%). Scale up capacity."
        decision = self.client.select_incident_tool(log, self.tools)
        self.assertEqual(decision.selected_tool, "scale_auto_scaling_group")
        self.assertGreater(decision.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
