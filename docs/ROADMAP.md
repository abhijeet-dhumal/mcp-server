# Kubeflow MCP Server Roadmap

This document outlines planned features and improvements. Contributors are welcome to pick up any item!

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

### Observability

| Feature | Status | Description |
|---------|--------|-------------|
| OpenTelemetry spans | 🔲 TODO | Distributed tracing for tool calls |
| Prometheus metrics | 🔲 TODO | `/metrics` endpoint with counters/histograms |
| Health endpoint | ✅ Done | `get_server_health()` tool |
| Structured logging | 🔲 TODO | JSON logs with correlation IDs |

### Reliability

| Feature | Status | Description |
|---------|--------|-------------|
| Circuit breaker | ✅ Done | Prevent cascade failures |
| Rate limiting | 🔲 TODO | Per-user/per-tool limits |
| Request timeouts | 🔲 TODO | Configurable per-tool timeouts |
| Graceful shutdown | 🔲 TODO | Drain connections on SIGTERM |

---

## Phase 3: Feature Expansion

### New Tool Modules

| Module | Status | Description |
|--------|--------|-------------|
| **Katib (Optimizer)** | 🔲 TODO | Hyperparameter tuning tools |
| **Model Registry (Hub)** | 🔲 TODO | Model versioning tools |
| **Pipelines** | 🔲 TODO | Pipeline management tools |
| **Notebooks** | 🔲 TODO | Notebook server tools |

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

### Training Enhancements

| Feature | Status | Description |
|---------|--------|-------------|
| `get_training_metrics` | 🔲 TODO | Fetch loss/accuracy from job |
| `scale_training_job` | 🔲 TODO | Dynamic worker scaling |
| `checkpoint_training` | 🔲 TODO | Save/restore checkpoints |
| Async job status | 🔲 TODO | SEP-1686 long-running pattern |
| Multi-cluster support | 🔲 TODO | Train across clusters |

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

## Phase 5: Agent & UX

| Feature | Status | Description |
|---------|--------|-------------|
| Claude agent | 🔲 TODO | Anthropic API agent |
| OpenAI agent | 🔲 TODO | GPT-4 API agent |
| Web UI dashboard | 🔲 TODO | Browser-based chat UI |
| VS Code extension | 🔲 TODO | Native VS Code integration |
| Slack bot | 🔲 TODO | Training notifications |

---

## Upcoming Integrations 📦

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
4. See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines

## Prioritization

Current priorities (Q2 2026):
1. Security (bearer token auth, audit logs)
2. Observability (metrics, tracing)
3. Katib integration

Want to influence priorities? Open a discussion on GitHub!
