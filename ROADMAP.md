# Kubeflow MCP Server Roadmap

This document outlines planned features and improvements. Contributors are welcome to pick up any item!

## Context & Design

This project implements [KEP-936: Kubeflow MCP Server](https://github.com/kubeflow/community/tree/master/proposals/936-kubeflow-mcp-server) - a Model Context Protocol server for AI-assisted Kubeflow operations.

## Near-term goal: Trainer-only production baseline

**Until Kubeflow onboarding, scope is intentionally narrow:**

1. **`TrainerClient` only** — ship and harden the **`trainer`** client module (`--clients trainer`). Stubs for `optimizer` / `hub` stay out of the critical path.
2. **Production-ready baseline** — HTTP hardening, identity wired to `TrainerClient`, honest docs for risky paths, observability, CI smoke against a real cluster, and reliable planning tools (`estimate_resources`).
3. **Then onboard** under Kubeflow and **delegate** Katib, Model Registry, Pipelines, Notebooks, extra agents, and Web UI to **contributors** (see *Deferred* below).

The **ordered todo list** in the next section is the single source of priority for that baseline. Everything in *Deferred* is explicitly **after** onboarding unless someone champions it earlier.

**Key References:**
- [KEP-936 Proposal](https://github.com/kubeflow/community/tree/master/proposals/936-kubeflow-mcp-server) - Original design document
- [KEP-936 PR discussion](https://github.com/kubeflow/community/pull/937) - Review threads (security, scalability, transport) — **action items are tracked below**
- [MCP Specification](https://modelcontextprotocol.io/specification) - Protocol specification
- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/) - Backend integration

---

## Prioritized backlog — Trainer baseline (strict order)

Do these **in sequence** for a reliable Trainer-only release. Later rows depend on earlier clarity (e.g. identity after HTTP contract).

| Step | Focus | Work |
|------|--------|------|
| **1** | HTTP edge | Bearer token (or document **gateway-only** auth), **audit** log (JSONL), **rate limits** for `--transport http`; document bind address, TLS, insecure defaults |
| **2** | Identity → `TrainerClient` | Replace `core/auth.py` placeholder: map SA / optional impersonation / gateway identity → `KubernetesBackendConfig` so **every tool uses one kube context** ([KEP #937](https://github.com/kubeflow/community/pull/937)) |
| **3** | Safety + transport docs | **`run_custom_training`**: SECURITY + user docs — **module-level code runs on MCP host** at load time; **`wait_for_training`**: **stdio vs HTTP** (proxy timeouts); align **prompt** timeouts with **tool** defaults |
| **4** | Planning | **`estimate_resources`**: HF Hub **timeouts**, **caching**, **user-supplied params** for air-gapped / private models |
| **5** | Observability | OpenTelemetry, **Prometheus** `/metrics`, JSON log polish (correlation IDs exist) |
| **6** | Reliability | Per-tool / global timeouts where still gaps; **graceful shutdown** for HTTP |
| **7** | CI baseline | **kind** or real-cluster **smoke**: health, list/get job, lifecycle sanity; optional **tag → PyPI** automation |
| **8** | SECURITY.md depth | Impersonation **ClusterRole** snippet when step 2 lands; gateway-only auth recipe |

**Optional / when tooling exists:** mcp-tef (or equivalent) for tool distinguishability — not blocking onboarding.

### Deferred — after Kubeflow onboarding (contributor backlog)

**Not part of the Trainer baseline:** Katib (`OptimizerClient`), Model Registry / hub, Pipelines, Notebooks modules; Claude/OpenAI/cloud agents; Web UI / VS Code extension; Slack bot; file-backed playbook repo (unless a contributor drives it early); **mcp-optimizer** integration (document-only reference is enough). Those stay in Phase 3+ sections below for tracking only.

### KEP / review items already reflected in code (do not duplicate work)

- TrainJob API **group/version/plural** (`trainer.kubeflow.org` / `v1alpha1`) for suspend/resume; `list_jobs(runtime=)` via **Runtime**; **event** fields aligned with SDK; **namespace** aligned with `TrainerClient`; **JobStatus** vocabulary (**Complete** vs pod **Succeeded**); **`[project.optional-dependencies] legacy_training`** vs Trainer SDK **`all`** extra; **SECURITY.md** RBAC apiGroup; **DCO** CI workflow.

---

## Ecosystem and platform integrations

This project is one MCP server in a larger stack. The sections below list common **companions** (not dependencies) and how we think about **native** support.

### MCP hosts and clients

| Integration | Role | Native in this repo |
|-------------|------|---------------------|
| Cursor, Claude Desktop, other MCP-capable IDEs | Launch `kubeflow-mcp` over **stdio** | Yes — document configs only |
| MCP Inspector | Debug stdio / HTTP | Yes — documented |
| Custom HTTP clients | **streamable-http** transport | Yes — server flag; TLS/auth usually at **ingress** |

### Agent and orchestration stacks

| Integration | Role | Native in this repo |
|-------------|------|---------------------|
| LlamaIndex, LangChain / LangGraph, etc. | Spawn MCP client or load tools | Partial — in-process + `kubeflow-mcp agent` (Ollama); more backends roadmap |
| Automation (CI, runners) | Call tools headless | Compose — use HTTP + token or stdio with fixed kube identity |
| Other MCP servers (Git, Jira, Slack, …) | Multi-server fan-out in the **host** | No — host/client concern |

### Kubernetes and “platform” integrations

These tools **do not speak MCP**. They govern **cluster identity, policy, and traffic**. Compatibility means: the resources our tools create (e.g. TrainJobs) satisfy your policies, and the **kube identity** used by the MCP process has appropriate RBAC.

| Integration | Role | Native in this repo |
|-------------|------|---------------------|
| **Kyverno**, **OPA Gatekeeper**, PSA | Admission policy on CRDs / Pods | No direct integration — **compose**; failures surface as normal API errors |
| **RBAC**, **ServiceAccount**, workload identity | Who can call the Kubernetes API | Compose — document recommended Roles |
| **Ingress / API gateway** (Envoy, Kong, nginx, cloud LB) | TLS, JWT/OIDC, rate limits for **HTTP MCP** | Compose — primary pattern for production HTTP |
| **Secrets** (Vault, ESO, cloud secrets) | Kubeconfig, pull secrets, tokens | Compose — MCP should not store cluster credentials |
| **GitOps** (Argo CD, Flux) | Change control vs direct writes | Optional workflow — org policy |
| **Service mesh** (Istio, Linkerd) | Pod traffic | Indirect — affects training workloads more than the MCP API client path |
| **Observability** (OpenTelemetry, Prometheus, Loki) | Traces, metrics, logs | Roadmap in Phase 2 — **hooks in-repo**, backends **compose** |

### Should we natively support “all of these”?

**No.** Goals:

1. **Standards-first MCP** — tools, prompts, resources, stdio + HTTP as defined by the ecosystem.
2. **Thin security and ops surface** — a small set of server features (e.g. optional bearer token, audit stream, metrics) where the process **must** participate; everything else belongs at **ingress**, **identity provider**, or **cluster policy**.
3. **Documentation and examples** — Helm/Kustomize snippets, “golden paths” for ingress + OIDC + Kyverno-safe TrainJobs, rather than embedding Kyverno, Vault, or mesh.

Trying to natively integrate every gateway, mesh, and policy engine would duplicate platform features, increase CVE and maintenance surface, and drift from how enterprises already run Kubernetes.

### What we need to do (directional)

Use the **Prioritized backlog** table at the top of this file as the main todo list; the rows below are older phase groupings of the same themes.

| Item | Where |
|------|--------|
| HTTP hardening: optional bearer token, audit log, rate limits | Phase 2 |
| Structured logs / correlation IDs (partially done); JSON logs polish | Phase 2 |
| OpenTelemetry + Prometheus | Phase 2 |
| OAuth / OIDC for the MCP HTTP server (or document gateway-only auth) | Phase 2–4 |
| Runbooks: ingress + TLS, kube SA + least-privilege RBAC, Kyverno expectations | Docs / examples (ongoing) |
| Optional: richer admission error messages (dry-run / Status hints) | Phase 3 (training tools) |
| More agent backends (OpenAI, Anthropic) | Phase 5 |

---

## Phase 1: Core Stability (Current)

| Feature | Status | Notes |
|---------|--------|-------|
| 16 training tools | ✅ Done | Core functionality |
| Unit tests (160+) | ✅ Done | SDK contract tests |
| Token-efficient modes | ✅ Done | Progressive, semantic |
| CI/CD pipelines | ✅ Done | Lint, test, Docker, PyPI |
| Tool annotations | ✅ Done | readOnlyHint, etc. |
| Makefile automation | ✅ Done | Developer experience |

---

## Phase 2: Production Readiness

### Security

| Feature | Status | Description |
|---------|--------|-------------|
| Bearer token auth | 🔲 TODO | Add `--auth-token` flag for API key validation |
| OAuth 2.1 + PKCE | 🔲 TODO | Full OAuth flow for enterprise deployments |
| Audit logging | 🔲 TODO | Structured logs for all tool invocations |
| Input sanitization | ✅ Done | Prevent injection attacks |
| Identity → TrainerClient | 🔲 TODO | Replace `AuthContext` stub; connect impersonation / OIDC headers to `KubernetesBackendConfig` (KEP [#937](https://github.com/kubeflow/community/pull/937)) |
| Custom script host execution | 🔲 TODO | SECURITY + user docs: module-level code runs on MCP host before pod (`run_custom_training`) |

### Observability

| Feature | Status | Description |
|---------|--------|-------------|
| OpenTelemetry spans | 🔲 TODO | Distributed tracing for tool calls |
| Prometheus metrics | 🔲 TODO | `/metrics` endpoint with counters/histograms |
| Health endpoint | ✅ Done | `get_server_health()` tool |
| Structured logging | 🔲 TODO | JSON logs polish (correlation IDs exist in `core/logging.py`) |

### Reliability

| Feature | Status | Description |
|---------|--------|-------------|
| Circuit breaker | ✅ Done | Prevent cascade failures |
| Rate limiting | 🔲 TODO | Per-user/per-tool limits |
| Request timeouts | 🔲 TODO | Configurable per-tool timeouts |
| Graceful shutdown | 🔲 TODO | Drain connections on SIGTERM |

---

## Phase 3: Feature expansion (post-onboarding — contributors)

**Out of scope** until the Trainer baseline ships and the project is onboarded to Kubeflow. Pick up via issues/OWNERS after that.

### New tool modules (not TrainerClient)

| Module | Status | Description |
|--------|--------|-------------|
| **Katib (Optimizer)** | 🔲 Later | Hyperparameter tuning tools |
| **Model Registry (Hub)** | 🔲 Later | Model versioning tools |
| **Pipelines** | 🔲 Later | Pipeline management tools |
| **Notebooks** | 🔲 Later | Notebook server tools |

#### Katib Tools (Stub Ready)

```
katib/
├── create_experiment        # Create HP tuning experiment
├── list_experiments         # List experiments
├── get_experiment           # Get experiment status
├── get_optimal_trial        # Get best hyperparameters
├── delete_experiment        # Clean up
└── suggest_search_space     # AI-suggested HP ranges
```

#### Model Registry Tools

```
hub/
├── register_model           # Register trained model
├── list_models              # Browse model registry
├── get_model_version        # Get model metadata
├── deploy_model             # Deploy to KServe
└── compare_models           # Compare model metrics
```

### Trainer enhancements (may follow baseline; some can stay contributor-owned)

| Feature | Status | Description |
|---------|--------|-------------|
| `estimate_resources` (HF hardening) | 🔲 Baseline | In **Prioritized backlog** step 4 — not optional for production realism |
| `get_training_metrics` | 🔲 Later | Fetch loss/accuracy from job |
| `scale_training_job` | 🔲 Later | Dynamic worker scaling |
| `checkpoint_training` | 🔲 Later | Save/restore checkpoints |
| Async job status | 🔲 Later | SEP-1686 long-running pattern |
| Multi-cluster support | 🔲 Later | Train across clusters |

---

## Phase 4: Enterprise Features

| Feature | Status | Description |
|---------|--------|-------------|
| Multi-tenancy | 🔲 TODO | Namespace isolation per user |
| RBAC integration | 🔲 TODO | K8s RBAC for tool permissions |
| Cost estimation | 🔲 TODO | Estimate training cost |
| Quota management | 🔲 TODO | Enforce resource quotas |
| SSO integration | 🔲 TODO | SAML/OIDC federation |

---

## Phase 5: Agent & UX (post-onboarding — contributors)

| Feature | Status | Description |
|---------|--------|-------------|
| Claude agent | 🔲 Later | Anthropic API agent |
| OpenAI agent | 🔲 Later | GPT-4 API agent |
| Web UI dashboard | 🔲 Later | Browser-based chat UI |
| VS Code extension | 🔲 Later | Native VS Code integration |
| Slack bot | 🔲 Later | Training notifications |

---

## Upcoming integrations (contributor / later phases)

### 1. Katib Integration

**Goal**: Add hyperparameter tuning capabilities via Katib tools using Kubeflow SDK's OptimizerClient.

**Deliverables**:
- 6+ new tools for Katib experiment management
- Suggest optimal search spaces using LLM reasoning
- Integration with training workflow
- Full test coverage and documentation

**Skills**: Python, Kubernetes, ML optimization

### 2. Model Registry Integration

**Goal**: Connect training to model versioning.

**Deliverables**:
- 5+ tools for model registry operations
- Automatic model registration after training
- Model comparison capabilities
- Documentation and examples

**Skills**: Python, ML workflow

### 3. Observability Dashboard (175 hours)

**Goal**: Production monitoring for MCP server.

**Deliverables**:
- Prometheus metrics export
- Grafana dashboard templates
- OpenTelemetry tracing
- Alerting rules

**Skills**: Python, Prometheus, observability

### 4. Web UI for Training (350 hours)

**Goal**: Browser-based interface for kubeflow-mcp.

**Deliverables**:
- React/Next.js web application
- Chat interface with tool visualization
- Job monitoring dashboard
- Responsive design

**Skills**: TypeScript, React, WebSockets

---

## How to Contribute

1. **Pick an item** from this roadmap
2. **Open an issue** to discuss approach
3. **Submit a PR** with implementation
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

## Prioritization

**Single rule:** finish the **Trainer-only baseline** table (steps 1–8) above; then onboard to Kubeflow and use Phase 3+ for **contributor-owned** work (Katib, hub, agents, UI). Order is aligned with [KEP #937](https://github.com/kubeflow/community/pull/937) where it touches Trainer security and ops.

Want to influence priorities? Open a discussion on GitHub!
