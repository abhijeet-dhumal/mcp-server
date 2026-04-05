# Kubeflow MCP Server - Release Checklist

This document tracks the project's readiness for official Kubeflow release. Use checkboxes to mark items as complete.

## Near-term goal: Trainer-only production baseline

| Goal | Detail |
|------|--------|
| **Scope** | **`TrainerClient` only** — use `--clients trainer`. Optimizer/hub stubs are **not** part of this baseline. |
| **Outcome** | Secure HTTP path, identity tied to `TrainerClient`, honest docs, observability, CI smoke on a cluster — then **onboard** to Kubeflow. |
| **After onboarding** | Phase 3+ items (Katib, registry, agents, UI) are **contributor backlog**, not blockers for baseline. |

**Work order** (same as [ROADMAP.md — Prioritized backlog](ROADMAP.md#prioritized-backlog--trainer-baseline-strict-order)):

1. HTTP: bearer (or gateway auth doc), audit, rate limits, bind/TLS docs  
2. Identity → `KubernetesBackendConfig` / `TrainerClient`  
3. Docs: `run_custom_training` host risk; `wait_for_training` transport + prompt/tool timeout alignment  
4. `estimate_resources` hardening (HF timeout, cache, user params)  
5. Observability (OTel, Prometheus, logs)  
6. Reliability (timeouts, graceful HTTP shutdown)  
7. CI: kind/cluster smoke + optional release automation  
8. SECURITY.md impersonation snippet when (2) ships  

---

## Phase 1: Core Stability (Complete)

### Infrastructure & CI/CD

- [x] GitHub workflows (lint, test, docker, publish, docs)
- [x] PR title checker (conventional commits)
- [x] Welcome new contributors workflow
- [x] Makefile automation (20+ targets)
- [x] Docker/GHCR image builds (`ghcr.io/kubeflow/mcp-server`)
- [x] PyPI publishing workflow
- [x] ReadTheDocs integration

### Documentation

- [x] README.md with badges, ToC, examples
- [x] CONTRIBUTING.md (setup, PR process, DCO, code style)
- [x] ARCHITECTURE.md (system design and modules)
- [x] SECURITY.md (vulnerability reporting, deployment practices)
- [x] ROADMAP.md (phased feature roadmap)
- [x] docs/DEVELOPMENT.md (detailed dev guide)
- [x] Sphinx docs with Furo theme (aligned with Kubeflow SDK)
- [x] Quickstart guide (local + container configs)
- [x] API reference docs (auto-generated)
- [x] FAQ/Troubleshooting page
- [x] KEP-936 reference linked
- [x] Roadmap links [KEP-936 PR #937](https://github.com/kubeflow/community/pull/937) for review-driven backlog

### TrainJob / SDK alignment (Kubeflow Trainer v2)

- [x] Suspend/resume use `trainer.kubeflow.org` / `v1alpha1` / `trainjobs` (SDK constants)
- [x] Namespace for lifecycle tools matches `TrainerClient` / Kubernetes backend
- [x] Suspend/resume use SDK `CustomObjectsApi` when on Kubernetes backend
- [x] `list_training_jobs(runtime=...)` resolves name via `get_runtime` → `list_jobs(runtime=Runtime)`
- [x] Discovery tools return MCP-safe `runtime: {"name": ...}` (not raw SDK object)
- [x] `get_training_events` maps SDK `Event` fields (`involved_object_*`, `reason`, `message`, `event_time`)
- [x] TrainJob status vocabulary (`Complete` vs pod `Succeeded`) reflected in constants, prompts, resources
- [x] `pyproject.toml`: `legacy_training` extra vs Trainer SDK `all` bundle clarified
- [x] `SECURITY.md` RBAC example uses `trainer.kubeflow.org` API group

### Code Quality

- [x] Unit tests (161+ passing)
- [x] Linting (ruff) configured
- [x] Type checking (mypy) with full coverage
- [x] Pre-commit checks (`make pre-commit`)
- [x] Apache 2.0 license headers on all source files
- [x] Input validation/sanitization (Pydantic models)
- [x] K8s API timeouts (5s strict, centralized)
- [x] Agent implementation optimized (in-process tools)

### Governance & Community

- [x] Apache 2.0 LICENSE file
- [x] OWNERS file (WG ML Experience leads)
- [x] Issue templates (bug, feature) - YAML-based
- [x] PR template with checklist
- [x] Slack channel reference (`#kubeflow-ml-experience`)
- [x] DCO sign-off requirement documented
- [x] Prow commands documented

### Core Features

- [x] 16 training tools (planning, training, discovery, monitoring, lifecycle)
- [x] Token-efficient modes (progressive, semantic) - 91-92% reduction
- [x] Tool annotations (readOnlyHint, destructiveHint, etc.)
- [x] MCP prompts (5 workflows)
- [x] MCP resources (4 URIs)
- [x] Persona-based access control (4 personas)
- [x] Health check tool
- [x] Circuit breaker for cascade failure prevention

---

## Phase 2: Production Readiness — Trainer baseline (in progress)

Checklists follow the **same order** as the **Work order** at the top of this file. Subsections map to steps 1–8.

### Step 1 — HTTP edge security

- [ ] Bearer token auth (`--auth-token` flag + env var) **or** documented **gateway-only** pattern
- [ ] Audit logging middleware (JSONL format)
- [ ] Rate limiting (in-memory + optional Redis)
- [ ] Document bind address, TLS, and defaults for `--transport http`

### Step 2 — Identity → TrainerClient

- [ ] Implement **AuthContext** (or equivalent) end-to-end: gateway/JWT or headers → **`KubernetesBackendConfig`** / **`TrainerClient`**
- [ ] Document **ServiceAccount**, optional **impersonation**, and **OIDC** paths (KEP “three deployment modes”)
- [ ] Expand **SECURITY.md** with impersonator **ClusterRole** when impersonation is implemented

### Step 3 — Safety + transport (Trainer tools)

- [ ] **SECURITY.md** + user docs: **`run_custom_training`** — module-level code runs on **MCP host** at import/load time
- [ ] Reconcile **prompt** defaults for **`wait_for_training`** vs tool (e.g. 3600 vs 600); document **HTTP vs stdio** / proxy timeouts

### Step 4 — Planning (`estimate_resources`)

- [ ] HuggingFace Hub **timeouts**, **caching**, **`user_provided_params`** (or equivalent) for air-gapped clusters

### Step 5 — Observability

- [ ] OpenTelemetry spans
- [ ] Prometheus metrics (`/metrics` endpoint)
- [ ] Structured JSON logging polish (correlation IDs — done in `logging.py`)

### Step 6 — Reliability

- [ ] Configurable per-tool timeouts (where still needed)
- [ ] Graceful shutdown (SIGTERM) for HTTP

### Step 7 — CI / release

- [x] DCO check workflow (enforce signed commits)
- [ ] Integration / smoke tests (kind or real cluster — Trainer tools)
- [ ] E2E tests (full workflow validation) — optional stricter gate after smoke
- [ ] Release automation (tag-triggered PyPI)
- [ ] Optional: **mcp-tef** (or equivalent) when tooling is stable — not blocking baseline

### Step 8 — SECURITY.md depth (after identity lands)

- [ ] Impersonation **ClusterRole** snippet in **SECURITY.md** (when Step 2 ships)
- [ ] **Gateway-only** auth recipe documented (complements Step 1 bearer-or-gateway story)
- [ ] OAuth 2.1 + PKCE (if in scope) **or** “gateway terminates OIDC” only — can trail baseline

---

## KEP-936 / community #937 (cross-reference)

Items above are derived from [kubeflow/community#937](https://github.com/kubeflow/community/pull/937). **Deferred** for baseline (contributors / post-onboarding):

- [ ] **File-backed** workflow playbooks
- [ ] **mcp-optimizer** / client-side docs only

---

## Phase 3+: Post-onboarding contributor backlog

**Not required** for Trainer-only production baseline or Kubeflow onboarding milestone.

### New tool modules (non-Trainer)

- [ ] **Katib (OptimizerClient)** — hyperparameter tuning tools
- [ ] **Model Registry (Hub)** — model versioning tools
- [ ] **Pipelines** — pipeline management tools
- [ ] **Notebooks** — notebook server tools

### Further Trainer enhancements

- [ ] `get_training_metrics` — fetch loss/accuracy from job
- [ ] `scale_training_job` — dynamic worker scaling
- [ ] `checkpoint_training` — save/restore checkpoints
- [ ] Async job status (SEP-1686 pattern)
- [ ] Multi-cluster support

---

## Phase 4: Enterprise Features (Future / contributors)

- [ ] Multi-tenancy (namespace isolation per user)
- [ ] K8s RBAC integration for tool permissions (beyond baseline identity wiring)
- [ ] Cost estimation for training jobs
- [ ] Quota management and enforcement
- [ ] SSO integration (SAML/OIDC federation) — if not covered by Step 8

---

## Phase 5: Agent & UX (Future / contributors)

- [ ] Claude API agent
- [ ] OpenAI API agent
- [ ] Web UI dashboard (React/Next.js)
- [ ] VS Code extension
- [ ] Slack bot notifications

---

## Summary

| Area | Status |
|------|--------|
| Phase 1: Core stability | Complete |
| TrainJob / TrainerClient v2 alignment | Complete (trainer tools) |
| Phase 2: Trainer production baseline | **In progress** — follow steps 1–8 in order |
| KEP #937 themes | Covered by Phase 2 steps + deferred list |
| Phase 3+ | **Post-onboarding** — contributors |

**Rule:** Finish Phase 2 steps **in order**; onboard to Kubeflow; then open Phase 3+ for community.

Canonical ordered list: [ROADMAP.md — Prioritized backlog](ROADMAP.md#prioritized-backlog--trainer-baseline-strict-order).

---

## References

- [KEP-936: Kubeflow MCP Server](https://github.com/kubeflow/community/tree/master/proposals/936-kubeflow-mcp-server)
- [KEP-936 community PR #937](https://github.com/kubeflow/community/pull/937) (discussion and review threads)
- [MCP Specification](https://modelcontextprotocol.io/specification)
- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/)
- [ROADMAP.md](ROADMAP.md) - Detailed feature roadmap
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
