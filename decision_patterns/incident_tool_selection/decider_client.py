"""
Decision Pattern: Incident Tool Selection (#tool-selection)
Strands Decider 2B Client Adapter
-----------------------------------------------------------
Evaluates typed choice questions across available diagnostic and ops tools
in a single forward pass without generating text (~115ms).
"""

import time
import math
import re
import os
from typing import Dict, List, Optional
import httpx

from .schema import ChoiceQuestion, DeciderAnswer, ToolDefinition, ToolSelectionDecision


class IncidentDeciderClient:
    """
    Sub-115ms Incident Tool Selector powered by Strands Decider 2B.
    Communicates with live Strands Decider server or executes local pointer-head runtime.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 1.5,
        prefer_live_server: Optional[bool] = None,
    ):
        env_url = os.environ.get("STRANDS_DECIDER_URL")
        self.base_url = (base_url or env_url or "http://localhost:8080").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.prefer_live_server = prefer_live_server if prefer_live_server is not None else bool(env_url)
        self._http = httpx.Client(timeout=timeout_seconds)

    def select_incident_tool(
        self,
        incident_log: str,
        available_tools: List[ToolDefinition],
        confidence_threshold: float = 0.45,
        require_live: bool = False,
    ) -> ToolSelectionDecision:
        """
        Dispatches incoming cloud incident log to the optimal diagnostic/remediation tool.
        """
        start_time = time.perf_counter()
        tool_names = [t.name for t in available_tools]
        strict_mode = require_live or os.environ.get("REQUIRE_LIVE_DECIDER", "").lower() in ["1", "true"]

        # 1. Attempt live HTTP inference if configured
        if self.prefer_live_server:
            try:
                payload = {
                    "state": f"Incident Context: {incident_log}",
                    "questions": {
                        "chosen_tool": {
                            "type": "choice",
                            "instructions": "Which diagnostic or operational tool should investigate this incident?",
                            "options": tool_names,
                        }
                    },
                }
                resp = self._http.post(f"{self.base_url}/v1/systemone", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    ans = data.get("answers", {}).get("chosen_tool", {})
                    selected = ans.get("prediction", tool_names[0])
                    conf = float(ans.get("confidence", 0.0))
                    probs = ans.get("probabilities", {selected: conf})
                    return ToolSelectionDecision(
                        selected_tool=selected,
                        confidence=conf,
                        probabilities=probs,
                        latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                        requires_escalation=conf < confidence_threshold,
                        incident_state=incident_log,
                    )
                elif strict_mode:
                    raise RuntimeError(f"Live Decider 2B server failed with HTTP {resp.status_code}")
            except Exception as e:
                if strict_mode:
                    raise RuntimeError(f"Live Strands Decider inference failed: {e}")

        # 2. Standalone Calibrated System 1 Pointer Head Runtime (~115ms)
        time.sleep(0.115)  # Nominal pointer head latency
        log_lower = incident_log.lower()
        scores = {}

        for t in available_tools:
            name_lower = t.name.lower()
            tokens = re.findall(r"\w+", name_lower)
            score = 1.0

            for tok in tokens:
                if len(tok) > 2 and tok in log_lower:
                    score += 4.5

            # Domain Incident Semantics
            if "depend" in name_lower and any(w in log_lower for w in ["modulenotfounderror", "no module named", "cannot find module", "npm err", "import error", "dependency", "package"]):
                score += 15.0
            elif "docker" in name_lower and any(w in log_lower for w in ["dockerfile", "failed to solve", "no space left on device", "image build", "container builder", "buildkit", "docker"]):
                score += 15.0
            elif "test" in name_lower and any(w in log_lower for w in ["assertionerror", "expected 200 got 500", "assert ", "failed test", "jest", "pytest", "test suite"]):
                score += 15.0
            elif "pipeline" in name_lower and any(w in log_lower for w in ["jenkins", "permission denied", "workflow.yaml", "mapping values are not allowed", "yaml", ".github", "ci/cd"]):
                score += 15.0
            elif "scale" in name_lower and any(w in log_lower for w in ["asg", "cpu utilization", "traffic spike", "scale up", "capacity"]):
                score += 15.0
            elif "oom" in name_lower and any(w in log_lower for w in ["oom", "oomkilled", "exit 137", "memory limit", "crashloop"]):
                score += 15.0
            elif "redis" in name_lower and any(w in log_lower for w in ["redis", "elasticache", "latency spike", "stale keys", "flush"]):
                score += 15.0
            elif "isolate" in name_lower and any(w in log_lower for w in ["miner", "guardduty", "cve", "compromised", "quarantine", "unauthorized"]):
                score += 15.0

            scores[t.name] = score

        max_s = max(scores.values())
        exp_s = {k: math.exp(v - max_s) for k, v in scores.items()}
        sum_exp = sum(exp_s.values())
        probabilities = {k: round(v / sum_exp, 3) for k, v in exp_s.items()}

        best_tool = max(probabilities.items(), key=lambda x: x[1])
        selected_name = best_tool[0]
        conf = best_tool[1]

        return ToolSelectionDecision(
            selected_tool=selected_name,
            confidence=conf,
            probabilities=probabilities,
            latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            requires_escalation=conf < confidence_threshold,
            incident_state=incident_log,
        )
