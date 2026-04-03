# Kubeflow Optimizer (Katib) - Hyperparameter Tuning

> **STATUS**: Stub - Ready for contributors (Phase 2)

This skill guides AI agents through hyperparameter optimization workflows using Kubeflow Katib.

## Overview

Katib automates hyperparameter tuning and neural architecture search. It runs multiple training trials with different parameter combinations to find optimal configurations.

## Planned Tools

| Tool | Description |
|------|-------------|
| `create_optimization_job` | Create a hyperparameter optimization experiment |
| `list_optimization_jobs` | List all optimization experiments |
| `get_optimization_job` | Get experiment status and details |
| `get_optimization_logs` | View trial logs |
| `get_optimization_events` | Debug scheduling issues |
| `get_best_hyperparameters` | Get optimal parameters from completed experiment |
| `wait_for_optimization` | Wait for experiment completion |
| `delete_optimization_job` | Delete an experiment |

## Workflow (When Implemented)

```
1. Define search space → create_optimization_job(objective="accuracy", search_space={...})
2. Monitor progress   → get_optimization_job(job_id)
3. View trial logs    → get_optimization_logs(job_id, trial="trial-1")
4. Get best params    → get_best_hyperparameters(job_id)
5. Clean up           → delete_optimization_job(job_id)
```

## Search Algorithms

- **random**: Random sampling (fast, good baseline)
- **grid**: Exhaustive grid search (thorough, expensive)
- **bayesian**: Bayesian optimization (efficient for expensive evaluations)
- **hyperband**: Early stopping of poor trials (efficient)
- **tpe**: Tree-structured Parzen Estimator (good for complex spaces)

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for implementation guide.

TODO: Implement OptimizerClient tools
