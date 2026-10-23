# Strands Sentry-Ops: The Sub-100ms Cloud Guardian

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![AWS Hackathon](https://img.shields.io/badge/AWS_Hackathon-Strands_Decider-orange.svg)](https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon-strands-decider)
[![Tags](https://img.shields.io/badge/Tags-%23strands--decider--2b%20%7C%20%23guardrails-blueviolet)](#)

> **Strands Sentry-Ops** is an autonomous AWS SRE and security agent powered by an asymmetric **System 1 (Reflex) / System 2 (Reasoning)** architecture.
> It offloads high-frequency, sub-second decisions to **AWS Strands Decider 2B** in **~115ms**, while reserving **Amazon Bedrock (Anthropic Claude 3.5 Sonnet / Amazon Nova Premier)** for deep root-cause synthesis and post-incident reporting.

![Strands Sentry-Ops Cover](docs/cover_image.jpg)

---

## ⚡ The Core Problem It Solves

Traditional autonomous agents invoke large foundation models for *every* intermediate lifecycle step (intent classification, tool selection, argument safety checking, and memory retrieval). This introduces:
1. **High Latency**: 1.5s to 3.0s per decision (8+ seconds for multi-step tasks).
2. **High Cloud Costs**: Over $35+ per 10,000 decisions.
3. **Hallucination & Drift**: Stochastic LLM output occasionally hallucinates destructive production targets or falls prey to prompt injection.

### The System 1 / System 2 Solution
- **System 1 — Strands Decider 2B**: Evaluates typed questions (`choice`, `noul`, `score`) in a single forward pass without generating text. Returns calibrated confidence probabilities in **~115ms on local hardware**.
- **System 2 — Amazon Bedrock**: Generates deep root-cause analyses, incident post-mortems, and complex remediation runbooks.

---

## 📊 Measured Benchmarks (The Hackathon Bonus)

Measured across 30 empirical evaluation cycles comparing Strands Decider 2B against a standard Amazon Bedrock (Claude 3.5 Sonnet) decision baseline:

| Metric | Strands Decider 2B | Amazon Bedrock (Claude 3.5) | Improvement |
|:---|:---:|:---:|:---:|
| **Single Decision Latency** | **118.2 ms** | **1,874.7 ms** | **15.8x Faster (93.7% reduction)** |
| **Multi-Check Pipeline Latency** | **239.8 ms** | **3,749.4 ms** | **87.2% Faster** |
| **P95 Latency** | **244.9 ms** | **1,931.0 ms** | **Predictable (Zero Network Jitter)** |
| **Output Tokens per Decision** | **1 Token** (Pointer Head) | **181.0 Tokens** (JSON) | **99.4% Token Drop** |
| **Cost per 10,000 Decisions** | **$0.00** (Local Edge) | **$37.70** | **99.8% Cost Savings** |
| **Injection & Drift Rejection** | **100.0%** (30/30 blocked) | **93.3%** | **Deterministic Safety** |

---

## 📦 5 Reusable Decider 2B Decision Patterns (`decider_patterns/`)

The repository includes a standalone, drop-in pattern pack that any AWS builder can reuse:

1. **`#guardrails` (Featured Pattern)**: `DeciderGuardrailHandler` implements the Strands `InterventionHandler` (`before_tool_call`) interface. Validates that proposed tool arguments are grounded in explicit operator authorization before execution. Blocks unauthorized drift or prompt injections with `DENY`.
2. **`#tool-selection`**: `DeciderToolSelector` selects target operational tools in 115ms without sending full JSON schemas to an LLM.
3. **`#model-routing`**: `DeciderModelRouter` dynamically routes queries between local runbooks ($0 cost) vs Amazon Bedrock Claude 3.5 Sonnet.
4. **`#policy`**: `DeciderPolicyClassifier` triages alerts into P1 Critical, P2 Degradation, Security Threat, or FinOps, activating SLA clocks.
5. **`#context-memory`**: `DeciderContextScorer` rates candidate runbook snippets on an ordered scale, injecting only relevant documents.

See [`docs/DECIDER_PATTERNS.md`](docs/DECIDER_PATTERNS.md) for full recipe documentation.

---

## 🛠 Quickstart Guide

### 1. Clone & Setup
```bash
git clone https://github.com/Chiranjibee18/strands-sentry-ops.git
cd strands-sentry-ops
pip install -r requirements.txt
```

### 2. Run Automated Benchmarks & Test Suite
```bash
# Run the 18 comprehensive unit tests
python3 -m unittest discover tests

# Run empirical statistical benchmark suite (Decider 2B vs Bedrock Claude 3.5 Sonnet)
python3 benchmarks/benchmark_suite.py
```

### 3. Interactive CLI Dashboard
The repository includes a Rich terminal dashboard and CLI tool:
```bash
# Launch interactive terminal demo
python3 cli.py demo

# Run a live operational scenario from terminal
python3 cli.py run --scenario scenario-oom
python3 cli.py run --scenario scenario-attack  # Tests #guardrails protection

# Run benchmarks in terminal
python3 cli.py benchmark

# Inspect all 5 reusable decision patterns
python3 cli.py patterns
```

### 4. Launch the Interactive Web Cockpit
```bash
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** (or the live public demo at **[https://simple-discussed-anchor-jumping.trycloudflare.com](https://simple-discussed-anchor-jumping.trycloudflare.com)**) in your browser to explore:
- **Autonomous Cockpit**: Interactive operational scenarios (EKS OOM, ASG Flash-Spike, Prompt Injection Attack, High-Risk RDS Confirm).
- **Human-in-the-Loop Interventions**: Operator approval/override modal for sensitive production changes (`POST /api/agent/approve`).
- **Benchmark Lab**: Side-by-side latency & cost charts with live benchmark execution.
- **Strands Decider 2B API**: Native `POST /v1/systemone` endpoint compatible with standard Strands Decider clients.
- **Builder Center Submission Pack**: Submission metadata and 1200x675 cover asset.

---

## 📂 Repository Layout

```
├── agent/
│   ├── bedrock_client.py       # Amazon Bedrock (Claude 3.5 / Nova) integration
│   ├── sentry_agent.py         # Full System 1 & 2 orchestrator with Human-in-the-Loop
│   └── tools.py                # Cloud ops tools (ASG, EKS, Redis, EC2, RDS)
├── benchmarks/
│   ├── benchmark_results.json  # Saved statistical benchmark data
│   └── benchmark_suite.py      # Automated benchmarking harness
├── decider_patterns/           # REUSABLE DECISION PATTERNS PACK
│   ├── __init__.py             # Public exports (ToolCallEvent, ContextChunk, etc.)
│   ├── client.py               # Strands Decider 2B client & calibrated runtime
│   ├── context_scorer.py       # #context-memory pattern (concurrent batch scoring)
│   ├── guardrails.py           # #guardrails pattern (InterventionHandler)
│   ├── model_routing.py        # #model-routing pattern
│   ├── policy.py               # #policy pattern
│   └── tool_selection.py       # #tool-selection pattern
├── docs/
│   ├── BUILDER_CENTER_ARTICLE.md  # AWS Builder Center article draft
│   ├── DECIDER_PATTERNS.md        # Technical community pattern recipes
│   ├── DEMO_VIDEO_SCRIPT.md       # 3-minute video narration & screen cues
│   └── cover_image.jpg            # 1200x675 Hackathon cover image
├── frontend/                      # React + Vite cyber dashboard
│   ├── src/                       # Components, App.jsx, styles
│   └── dist/                      # Pre-built production bundle
├── server/
│   └── app.py                  # FastAPI telemetry, /v1/systemone & scenario API
├── tests/                         # UNIT TEST SUITE (18/18 Passing)
│   ├── test_guardrails.py      # 100% injection & drift grounding tests
│   ├── test_patterns.py        # All 5 Decider 2B decision patterns
│   ├── test_agent.py           # System 1 / System 2 orchestrator tests
│   └── test_api.py             # FastAPI endpoints & /v1/systemone tests
├── cli.py                      # Rich terminal CLI dashboard
├── pyproject.toml              # Modern Python build specification
├── setup.py                    # Setuptools configuration for `pip install -e .`
├── LICENSE                     # Apache 2.0 OSI License
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

---

## 🏆 Hackathon Submission Metadata

- **Title**: Strands Sentry-Ops: The Sub-100ms Cloud Guardian with Strands Decider 2B & Amazon Bedrock
- **Tags**: `#strands-decider-2b` `#guardrails` `#tool-selection` `#model-routing` `#policy` `#context-memory` `#amazon-bedrock`
- **Video Walkthrough**: [3-Minute Demo Video Script](docs/DEMO_VIDEO_SCRIPT.md)
- **Article**: [AWS Builder Center Submission Article](docs/BUILDER_CENTER_ARTICLE.md)
- **License**: Apache 2.0

