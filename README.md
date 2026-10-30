# SentryOps: A Decision-First Cloud Incident Agent

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![AWS Hackathon](https://img.shields.io/badge/AWS_Hackathon-Strands_Decider-orange.svg)](https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon-strands-decider)
[![Tags](https://img.shields.io/badge/Tags-%23strands--decider--2b%20%7C%20%23tool--selection%20%7C%20%23guardrails-blueviolet)](#)
[![Accuracy](https://img.shields.io/badge/Accuracy-100.0%25%20(50%2F50)-success)](#empirical-benchmarks-50-case-dataset)
[![Latency](https://img.shields.io/badge/Median_Latency-118.98ms-cyan)](#empirical-benchmarks-50-case-dataset)

> **SentryOps** is an autonomous AWS cloud incident operations agent powered by an asymmetric **System 1 (Reflex) / System 2 (Reasoning)** architecture.
> It offloads high-frequency diagnostic decisions to **AWS Strands Decider 2B** in **~115ms**, while reserving **Amazon Bedrock (Anthropic Claude 3.5 Sonnet / Amazon Nova)** for deep incident root-cause synthesis and post-incident reporting.

![SentryOps Cover](docs/cover_image.jpg)

---

## ⚡ The Core Problem It Solves

Traditional autonomous cloud agents invoke large generative foundation models (LLMs) for *every* intermediate lifecycle step (incident triage, tool selection, parameter safety verification, and memory retrieval). This introduces three fatal flaws:

1. **High Latency**: 1.5s to 3.5s per decision (8+ seconds for multi-step investigations).
2. **High Cloud Costs**: Over $35+ per 10,000 decisions.
3. **Hallucination & Blast Radius**: Stochastic LLM output occasionally hallucinates destructive production targets or falls prey to indirect prompt injection in alert logs.

### The System 1 / System 2 Solution
- **System 1 — Strands Decider 2B**: Evaluates typed questions (`choice`, `noul`, `score`) in a single forward pass without generating text. Returns calibrated confidence probabilities in **~115ms on local hardware**.
- **System 2 — Amazon Bedrock**: Synthesizes deep root-cause analyses, incident post-mortems, and preventative architectural recommendations.

---

## 🌐 Cyber Intent Graph & Blast Radius Analysis

SentryOps provides an interactive SVG topology canvas illustrating cloud dependencies and active risk paths:
- **Topology Nodes**: `Internet → Route 53 / WAF → API Gateway → checkout-svc → prod-db`.
- **Containment Boundaries**: `prod-vpc` with private subnets (`10.0.1.0/24`, `10.0.2.0/24`) and IAM roles (`app-role`, `deploy-role`, `dba-role`).
- **Dynamic Blast Radius Analysis**: Live confidence gauges, impacted user counters (e.g. 18.5k active sessions shielded), and multi-layer operational metrics across Code Layer (Terraform), Cloud Layer (AWS), and Business Layer (SLA/SLO).

---

## 📦 Standalone Reusable Pattern: `#tool-selection`

The repository packages a standalone, drop-in reusable pattern located at:
[`decision-patterns/incident-tool-selection/`](decision-patterns/incident-tool-selection/)

```
decision-patterns/incident-tool-selection/
├── README.md                 # 3-line quickstart & contract documentation
├── schema.py                 # Pydantic models for typed questions & decisions
├── decider_client.py         # Sub-115ms IncidentDeciderClient
├── intervention.py           # IncidentInterventionHandler (Strands SDK)
└── tests/
    ├── test_valid_decision.py     # Valid tool selections (ASG, OOM, Redis)
    ├── test_invalid_decision.py   # Adversarial injection & low-confidence tests
    └── test_tool_dispatch.py      # Dynamic tool dispatch verification
```

### 3-Line Quickstart for Other Builders for only
```python
from decision_patterns.incident_tool_selection.decider_client import IncidentDeciderClient

client = IncidentDeciderClient()
result = client.select_investigation_tool(
    incident_state="CloudWatch: High CPU on payment-service-asg (98%). Scale capacity.",
    permitted_tools=["scale_auto_scaling_group", "remediate_oom_pod", "flush_redis_cache"]
)
# Returns: {'chosen_tool': 'scale_auto_scaling_group', 'confidence': 0.98, 'latency_ms': 115.0}
```

---

## 📊 Empirical Benchmarks (50-Case Dataset)

Evaluated on a **50-case labeled incident dataset** across five distinct operations categories:

| Category | Sample Size | Correct Tool Selections | Accuracy (%) | Error / Failure Rate |
|:---|:---:|:---:|:---:|:---:|
| **CloudOps** (ASG, RDS, EC2, CloudWatch) | 10 | 10 | **100.0%** | **0.0%** |
| **Docker & Containers** (OOMKilled, Pod Crashes) | 10 | 10 | **100.0%** | **0.0%** |
| **Dependencies & Packaging** (Poetry, pip, npm) | 10 | 10 | **100.0%** | **0.0%** |
| **Unit & Integration Tests** (pytest, Jest, fixtures) | 10 | 10 | **100.0%** | **0.0%** |
| **CI/CD Pipeline** (GitHub Actions, build timeouts) | 10 | 10 | **100.0%** | **0.0%** |
| **Total / Overall Evaluation** | **50** | **50** | **100.0%** | **0.0%** |

### Latency Distribution
- **Median Latency (P50)**: **118.98 ms**
- **P95 Latency**: **124.52 ms**
- **Mean Latency**: **119.28 ms**
- **Speedup vs Bedrock Baseline**: **15.8x Faster (93.7% reduction)**
- **Cost Reduction**: **99.8% Saved** ($0.00 local vs $37.70 per 10k calls)

### Reproduce in Terminal
```bash
python3 benchmarks/evaluate_dataset.py
```

---

## 🛠 Quickstart Guide

### 1. Clone & Setup
```bash
git clone https://github.com/Chiranjibee18/strands-sentry-ops.git
cd strands-sentry-ops
pip install -r requirements.txt
```

### 2. Run Test Suite & Benchmarks
```bash
# Run the 57 comprehensive unit and integration tests
python3 -m unittest discover tests

# Run the 6 decision-pattern unit tests
python3 -m unittest discover decision-patterns/incident-tool-selection/tests

# Run the 50-case empirical evaluation
python3 benchmarks/evaluate_dataset.py
```

### 3. Interactive CLI Dashboard
```bash
# Launch interactive terminal demo
python3 cli.py demo

# Run live operational scenarios
python3 cli.py run --scenario scenario-traffic
python3 cli.py run --scenario scenario-injection  # Tests #guardrails protection

# Run benchmarks in terminal
python3 cli.py benchmark
```

### 4. Launch the Interactive Web Cockpit
```bash
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** (or the live public demo at **[https://simple-discussed-anchor-jumping.trycloudflare.com](https://simple-discussed-anchor-jumping.trycloudflare.com)**):
- **Cyber Intent Graph**: Interactive SVG cloud topology with dynamic blast radius analysis.
- **Decision Lifecycle Telemetry**: Real-time pipeline step latency, tokens, and Bedrock RCA.
- **Human-in-the-Loop Interventions**: Operator sign-off modal for sensitive production changes (`POST /api/agent/approve`).
- **Benchmark Lab**: Side-by-side latency & cost charts with 50-case labeled dataset metrics.
- **Builder Center Submission Pack**: Ready-to-copy fields, 16:9 cover image preview, and cURL snippets.

---

## 🔒 Safety & Simulation Transparency

SentryOps provides complete disclosure between live AWS operations and sandbox execution:
- **AWS Bedrock Provider Chain**: `agent/bedrock_client.py` uses `boto3.Session().get_credentials()` (supporting EC2 IAM instance roles, AWS SSO, and `~/.aws/credentials`). If credentials are not present, it runs in **Verified Fixture Mode** with explicit UI/API disclosure (`is_live_aws: false`). Strict live mode is available via `REQUIRE_LIVE_BEDROCK=1`.
- **Decider 2B Endpoint**: Supports live Strands Decider inference endpoints or local calibrated sandbox (`REQUIRE_LIVE_DECIDER=1`).
- **Operator Escalation Matrix**:
  - Grounded & Confidence $\ge 0.75$ $\rightarrow$ **`PROCEED`**
  - High-risk / Destructive production target $\rightarrow$ **`CONFIRM`** (Operator sign-off required)
  - Adversarial prompt injection or drift $\rightarrow$ **`DENY`** (Immediate zero-impact abort)

---

## 📜 License & Compliance

Distributed under the **Apache-2.0 License**. See [LICENSE](LICENSE) for details.
All decision patterns are open-source and freely reusable by the AWS developer community.
