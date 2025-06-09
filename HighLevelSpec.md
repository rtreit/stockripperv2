# Multi-Agent MCP / A2A / LangGraph MVP — Delivery Spec
# (Copy-paste directly into the root of the coordination repo; share with each
# OpenAI Codex coding-agent that will own one or more tasks.)

###############################################################################
# 0.  TL;DR
#
# Build three cooperating Python agents—Researcher, Strategist, Messenger—each
# running in its own container on Kubernetes.  They communicate peer-to-peer
# with **A2A v0.1** JSON-RPC﻿ :contentReference[oaicite:0]{index=0}, invoke external
# tools through **MCP servers** ﻿ :contentReference[oaicite:1]{index=1}, and model their
# control-flow in **LangGraph** ﻿ :contentReference[oaicite:2]{index=2}.
#
# Success = the end-to-end integration test sends a real e-mail (via Gmail MCP)
# summarising fresh market research and a recommended trade that emulates a
# paper order on Alpaca.﻿

###############################################################################
# 1.  High-Level Requirements
#
# | KPI                               | Target/Definition                              |
# |-----------------------------------|-----------------------------------------------|
# | Agents per Helm release           | 3 pods, 1 per agent                           |
# | Protocol compliance               | A2A v0.1 (signed JSON-RPC over HTTP)          |
# | External tools                    | ≥2 MCP servers (Alpaca + Gmail)               |
# | Python dependency install         | `uv pip install --system …` ﻿ :contentReference[oaicite:3]{index=3} |
# | Integration test                  | `pytest` exit 0 with Kind CI cluster          |
# | Deployment pipeline               | GitHub Actions + `setup-kind`  ﻿ :contentReference[oaicite:4]{index=4} |

###############################################################################
# 2.  Reference Architecture

## 2.1  Cluster Layout
# - Helm umbrella chart with sub-charts per agent & shared ConfigMap
# - Namespace: `mcp-a2a-agents`
# - Optional sidecars: `qdrant` (vector-db) for memory; `prometheus-agent`
# - Ingress (Traefik/NGINX) with mTLS if Internet exposure required
#   (Helm sub-chart patterns follow Helm docs) ﻿ :contentReference[oaicite:5]{index=5}

## 2.2  Protocol Adapters
# - MCP client libs generated from each server’s OpenAPI description
#   • Alpaca MCP (paper trading default) ﻿ :contentReference[oaicite:6]{index=6}
#   • Gmail MCP (AutoAuth)              ﻿ :contentReference[oaicite:7]{index=7}
# - A2A envelope: {id,from,to,action,payload,isoTimestamp,signature}

## 2.3  Agents
# ┌────────────┐        ┌─────────────┐        ┌────────────┐
# │ Researcher │––A2A––▶│  Strategist │––A2A––▶│ Messenger  │
# └────────────┘        └─────────────┘        └────────────┘
#
#  • **Researcher**  – queries Alpaca MCP for latest price, news, fundamentals;
#                      emits `research.completed`
#  • **Strategist**  – waits for research, applies simple rule engine,
#                      emits `strategy.completed`
#  • **Messenger**   – converts strategy → e-mail; uses Gmail MCP to send;
#                      emits `notification.sent`

###############################################################################
# 3.  Repository Skeleton
#
# .
# ├─ agents/
# │   ├─ researcher/        # Python, LangGraph workflow, Dockerfile
# │   ├─ strategist/        # Python, LangGraph workflow, Dockerfile
# │   └─ messenger/         # Python, LangGraph workflow, Dockerfile
# ├─ helm/                  # umbrella + sub-charts
# ├─ tests/
# │   └─ e2e/               # failing first
# ├─ ci.yaml                # GitHub Actions pipeline
# └─ README.md
#
# Each agent directory **owns**:
#   Dockerfile, pyproject.toml, LangGraph graph, A2A client/server wrapper.

###############################################################################
# 4.  Coding Standards

## 4.1  Python Dockerfile snippet (import into each agent)
#   FROM python:3.11-slim
#   RUN curl -Ls https://astral.sh/uv/install.sh | sh
#   COPY pyproject.toml requirements.txt ./
#   RUN uv pip install -r requirements.txt --system
#   CMD ["python", "-m", "agent.main"]

## 4.2  LangGraph conventions
#   • Each node ≈ LangChain Runnable
#   • Register outbound A2A publish as a Tool in the graph
#   • Handle graceful shutdown (SIGTERM) for k8s

###############################################################################
# 5.  Work Breakdown — Independent Codex Tasks

| ID   | Owner-Bot         | Deliverable |
|------|-------------------|-------------|
| **T-Infra** | InfraBot | Helm umbrella chart; Kind bootstrap script |
| **T-Res**   | ResearcherBot | Alpaca MCP client; LangGraph; unit tests |
| **T-Strat** | StrategistBot | Strategy rules; A2A listener/emit; unit tests |
| **T-Msg**   | MessengerBot | Gmail MCP adapter; HTML template; unit tests |
| **T-QA**    | QABot | Pytest-bdd E2E spec & harness (uses Kind) |
| **T-CI**    | CIBot | GitHub Actions: build, Kind deploy, run tests, helm-push |

###############################################################################
# 6.  Test-Driven Development Guidelines

## 6.1  Canonical failing E2E (tests/e2e/test_flow.py)
def test_trade_flow(cluster):
    """
    GIVEN all three agents running in Kind
    WHEN  Researcher publishes research.completed
    THEN  Strategist publishes strategy.completed AND
          Messenger publishes notification.sent (Gmail MCP)
    """
    cluster.publish("research.requested", sample_request)
    strategy = cluster.wait_for("strategy.completed", 30)
    email    = cluster.wait_for("notification.sent", 30)
    assert strategy["status"] == "BUY"          # simple rule
    assert email["success"] is True

# Commit the above first; CI must fail red.

## 6.2  Unit tests
# • Researcher: mock Alpaca MCP server → verify JSON schema
# • Strategist: feed fixture data → expect rule output
# • Messenger: stub Gmail MCP server → ensure send() called

###############################################################################
# 7.  CI/CD Pipeline (ci.yaml sketch)

# name: mvp
# on:  push
# jobs:
#   build:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v4
#       - uses: docker/setup-buildx-action@v3
#       - run: docker build -t agent-${{ matrix.app }} -f agents/${{ matrix.app }}/Dockerfile .
#   test:
#     needs: build
#     runs-on: ubuntu-latest
#     steps:
#       - uses: engineerd/setup-kind@v0  # KinD cluster ﻿ :contentReference[oaicite:8]{index=8}
#       - run: helm install mvp ./helm
#       - run: pytest tests/e2e

###############################################################################
# 8.  Acceptance Criteria

# [ ] `helm install mvp ./helm` → 3 pods healthy, 0 restarts
# [ ] E2E test passes both locally & in CI
# [ ] `kubectl logs messenger` shows Gmail MCP 200 OK
# [ ] `ruff` lint passes, `mypy --strict` passes
# [ ] README documents secret injection (k8s Secret → env vars)

###############################################################################
# 9.  Future Work (non-blocking)

# • Add Rust or Go agent to prove language independence
# • Introduce shared Qdrant vector store sidecar
# • Switch A2A transport to gRPC stream once spec 0.2 lands
# • Roll out cost-aware auto-scaling via KEDA

###############################################################################
# References (inline citations):
#  turn0search0 – MCP spec
#  turn0search1 – Google A2A announcement
#  turn0search2 – LangGraph blog
#  turn0search3 – Alpaca MCP GitHub
#  turn0search4 – Gmail MCP GitHub
#  turn0search5 – Reddit uv discussion
#  turn0search6 – Helm sub-charts doc
#  turn0search7 – setup-kind action
#  turn0search8 – Anthropic MCP article
#  turn0search9 – Medium A2A deep dive
#  turn0search10 – LangGraph official docs
#  turn0search11 – Alternate Alpaca MCP repo
