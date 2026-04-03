# Kubeflow Model Registry (Hub) - Model Versioning

> **STATUS**: Stub - Ready for contributors (Phase 3)

This skill guides AI agents through model registration and versioning workflows using Kubeflow Model Registry.

## Overview

The Model Registry provides centralized model artifact management with versioning, metadata tracking, and deployment integration.

## Planned Tools

| Tool | Description |
|------|-------------|
| `register_model` | Register a trained model with metadata |
| `list_models` | List all registered models |
| `get_model` | Get model details and metadata |
| `list_model_versions` | List all versions of a model |
| `get_model_version` | Get specific version details |
| `get_model_artifact` | Get artifact storage location |
| `update_model` | Update model metadata or labels |

## Workflow (When Implemented)

```
1. After training   → register_model(name="llama-finetuned", version="v1.0", artifact_uri="s3://...")
2. Browse models    → list_models()
3. Get details      → get_model(name="llama-finetuned")
4. List versions    → list_model_versions(name="llama-finetuned")
5. Update metadata  → update_model(name="llama-finetuned", labels={"stage": "production"})
```

## Integration with Training

After a training job completes:

```
User: "Register the trained model from job ft-llama-123"

Agent:
1. get_training_job("ft-llama-123") → Get artifact location
2. register_model(
     name="llama-finetuned",
     version="v1.0",
     artifact_uri="s3://bucket/ft-llama-123/checkpoint",
     description="Fine-tuned on alpaca dataset",
     labels={"base_model": "llama-3.2-1b", "dataset": "alpaca"}
   )
```

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for implementation guide.

TODO: Implement ModelRegistryClient tools
