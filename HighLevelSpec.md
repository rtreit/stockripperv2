# Multi-Agent MCP / A2A / LangGraph MVP – Development Spec
_Ready for copy-paste into your repo.  Uses TDD, Helm-based deployment, and `uv` for Python packaging._

---

## 1  Purpose & Success Criteria

| KPI                                   | Target                                            |
|---------------------------------------|---------------------------------------------------|
| Containers per agent                  | ≥ 1 (single Helm release)                         |
| Inter-agent comms                     | A2A v0.1 JSON-RPC over HTTP(S)                    |
| Tool access via MCP servers           | ≥ 2 (Alpaca + Gmail for the MVP)                  |
| End-to-end integration test           | `pytest` suite exits 0                            |
| Python package install method         | `uv pip install`, no legacy `pip install`         |

---

## 2  Reference Architecture

### 2.1  Cluster Layout
* **Helm umbrella chart** with one sub-chart per agent.  
* **Namespace:** `mcp-a2a-agents`.  
* Optional *sidecars*: `vector-db` (e.g. Qdrant) or `prometheus-agent`.  
* **Ingress controller** (Traefik / NGINX) with mTLS if external access is required.

### 2.2  Protocols
* **MCP** – external tool invocations described by OpenAPI / JSON schema.  
* **A2A** – signed envelope `{ id, from, to, action, payload, isoTimestamp }`, HTTP JSON-RPC transport (upgradeable to WebSocket).  
* **LangGraph** – deterministic workflow engine embedded in each Python agent.

### 2.3  Reference Agents (Python 3.11 + `uv`)

| Agent            | Responsibilities                                    | MCP Servers | A2A Topics                         |
|------------------|------------------------------------------------------|-------------|------------------------------------|
| **MarketAnalyst**| Fetch quotes, news, fundamentals; publish insights   | Alpaca      | `market-insight`                   |
| **Planner**      | Consume insights, decide trades, request notification| Alpaca + Gmail | `trade-plan`, `email-notify`    |
| **Mailer**       | Build summary email, send via Gmail                  | Gmail       | `email-notify`                     |

Agents are language-agnostic black boxes to one another; any future agent just speaks A2A.

---

## 3  Development Conventions

### 3.1  Repo Layout
/agents
/market-analyst
/planner
/mailer
/helm
/tests
/e2e
ci.yaml


### 3.2  Python Dockerfile Snippet
    FROM python:3.11-slim
    RUN curl -Ls https://astral.sh/uv/install.sh | sh
    COPY pyproject.toml requirements.txt ./
    RUN uv pip install -r requirements.txt --system

---

## 4  Test-Driven Development (Fail-First)

### 4.1  Tooling
* **pytest** + `pytest-asyncio` for functional tests.  
* **Kind** (Kubernetes-in-Docker) for local CI cluster; Testkube optional.  
* Optional BDD layer: `pytest-bdd` for readable feature specs.

### 4.2  Canonical Failing Test
    def test_end_to_end_trade_flow(client):
        """
        GIVEN all three agents running in the cluster
        WHEN  MarketAnalyst publishes an insight on `market-insight`
        THEN  Planner emits a `trade-plan` AND
              Mailer sends an email via Gmail MCP
        """
        insight = client.post("/a2a/publish", json=sample_insight)
        plan   = client.wait_for("trade-plan",  timeout=30)
        email  = client.wait_for("email-notify", timeout=30)
        assert plan["status"] == "READY"
        assert email["sent"] is True

Commit this test first; CI should fail red until implementation is complete.

---

## 5  CI/CD Pipeline

1. Unit tests  
2. Docker build (cache `uv` layer)  
3. Kind deploy  
4. E2E tests  
5. Helm package → push to OCI registry  
6. Promotion gates

---

## 6  Work Breakdown (Autonomous Coding Agents)

| Task ID | Agent                | Deliverable                                       |
|---------|----------------------|---------------------------------------------------|
| A-01    | **InfraBot**         | Helm umbrella chart + Kind harness                |
| A-02    | **MarketAnalystBot** | LangGraph workflow, Alpaca MCP client, Dockerfile |
| A-03    | **PlannerBot**       | LangGraph decision logic, rule-based trades       |
| A-04    | **MailerBot**        | Gmail MCP adapter, HTML email templating          |
| A-05    | **QA-Bot**           | pytest-bdd suite, cluster bootstrap scripts       |
| A-06    | **CI-Bot**           | GitHub Actions pipeline integrating Kind + Helm   |

Each bot opens PRs, triggers review via A2A, and watches its assigned path.

---

## 7  Acceptance Checklist

- [ ] `helm install mvp ./helm` deploys three healthy pods.  
- [ ] `pytest tests/e2e` passes locally and in CI.  
- [ ] `kubectl logs` for each pod shows ≥ 1 successful MCP call.  
- [ ] Code lint: `ruff`, type check: `mypy --strict` clean.  
- [ ] README documents secret handling (API keys via `Secret` manifests).

---

## 8  Future Extensions

* Add non-Python agents (Rust, Go) to prove language independence.  
* Distributed state backend in LangGraph for shared memory.  
* Swap HTTP transport for gRPC/Kafka when A2A 0.2 formalizes streams.  
* Add additional MCP servers (Redis-MCP, Stripe-MCP, etc.).
