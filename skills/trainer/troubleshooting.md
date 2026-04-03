---
name: Troubleshooting Training Jobs
description: Guide for diagnosing and resolving common training job failures
globs:
  - "src/kubeflow_mcp/trainer/api/*.py"
---

# Troubleshooting Training Jobs

Guide for diagnosing and resolving common training job failures.

## Diagnostic Workflow

When a job fails or gets stuck:

```
1. get_training_job(name) → Check status
2. get_training_events(name) → Check K8s events
3. get_training_logs(name) → Read container logs
```

## Job Status Reference

| Status | Meaning | Action |
|--------|---------|--------|
| `Pending` | Waiting for resources | Check events for scheduling issues |
| `Running` | Training in progress | Check logs for errors |
| `Succeeded` | Completed successfully | Done |
| `Failed` | Training crashed | Check logs for error |
| `Suspended` | Manually paused | Use `resume_training_job()` |

## Common Issues

### No GPUs Available

**Symptom**: Job stuck in `Pending`

**Diagnosis**:
```python
get_cluster_resources()
# Returns: {gpu_total: 0, ...}
```

**Solutions**:
1. Wait for GPU nodes to become available
2. Request GPU nodes from cluster admin
3. Use smaller model that fits on available resources
4. Try CPU training: `gpu_per_node=0`

### Insufficient GPU Memory (OOMKilled)

**Symptom**: Job fails with `OOMKilled` in events

**Diagnosis**:
```python
get_training_events(name="my-job")
# Shows: {reason: "OOMKilled", message: "Container killed due to OOM"}
```

**Solutions**:

1. **Reduce batch size**:
   ```python
   fine_tune(..., batch_size=2, ...)  # Instead of 4
   ```

2. **Use gradient accumulation** (custom training):
   ```python
   # Effective batch = batch_size * accumulation_steps
   accumulation_steps = 4
   ```

3. **Enable gradient checkpointing** (custom training):
   ```python
   model.gradient_checkpointing_enable()
   ```

4. **Use quantization** (QLoRA):
   Currently requires custom training with bitsandbytes

### Image Pull Failed

**Symptom**: `ErrImagePull` or `ImagePullBackOff` in events

**Diagnosis**:
```python
get_training_events(name="my-job")
# Shows: {reason: "Failed", message: "Failed to pull image..."}
```

**Solutions**:

1. **Check image name**:
   ```python
   # Correct
   run_container_training(image="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime")
   
   # Wrong - typo
   run_container_training(image="pytoch/pytorch:2.2.0")
   ```

2. **Private registry**: Ensure imagePullSecrets configured in namespace

3. **Rate limiting**: Docker Hub has pull limits; use authenticated pulls

### Runtime Not Found

**Symptom**: Error "runtime 'torch-tune' not found"

**Diagnosis**:
```python
list_runtimes()
# Returns: {runtimes: [{name: "torch-distributed"}, ...]}
```

**Solutions**:

1. **Use available runtime**:
   ```python
   fine_tune(..., runtime="torch-distributed", ...)
   ```

2. **Install missing runtime**: Ask cluster admin to install ClusterTrainingRuntime

### NCCL Timeout (Multi-Node)

**Symptom**: Job hangs, then fails with NCCL timeout

**Diagnosis**:
```python
get_training_logs(name="my-job")
# Shows: "NCCL WARN Timeout waiting for connection"
```

**Solutions**:

1. **Check network**: Nodes must communicate on NCCL ports
2. **Increase timeout** (env variable):
   ```python
   fine_tune(..., env=[{"name": "NCCL_TIMEOUT", "value": "1800"}], ...)
   ```
3. **Use single node**: If network issues persist

### Permission Denied (Gated Models)

**Symptom**: "401 Unauthorized" or "Access denied" in logs

**Diagnosis**:
```python
get_training_logs(name="my-job")
# Shows: "You need to agree to the terms..."
```

**Solutions**:

1. **Accept model license** on HuggingFace
2. **Provide HF token**:
   ```python
   fine_tune(..., hf_token="hf_xxxxx", ...)
   ```
3. **Check token permissions**: Token needs `read` scope

### Script Validation Failed

**Symptom**: Error "Script validation failed: Dangerous pattern"

**Cause**: Security check blocked dangerous imports

**Solutions**:

1. **Remove dangerous imports**:
   ```python
   # Not allowed
   import os
   import subprocess
   
   # Use alternatives
   from pathlib import Path  # Instead of os.path
   ```

2. **Use container training** for full system access:
   ```python
   run_container_training(image="your-image", ...)
   ```

### Pod Stuck in ContainerCreating

**Symptom**: Job stuck, events show "ContainerCreating"

**Diagnosis**:
```python
get_training_events(name="my-job")
# Shows: {reason: "FailedMount", message: "Unable to mount volumes..."}
```

**Solutions**:

1. **PVC not found**: Check PVC exists in namespace
2. **PVC bound**: Ensure PVC is not bound to another pod
3. **Storage class**: Check storage class supports ReadWriteMany if multi-node

### Training Loss Not Decreasing

**Symptom**: Job runs but loss stays constant

**Diagnosis**:
```python
get_training_logs(name="my-job")
# Shows: "Epoch 1: loss=2.5, Epoch 2: loss=2.5, Epoch 3: loss=2.5"
```

**Solutions**:

1. **Learning rate too low**: Increase LR
2. **Learning rate too high**: Decrease LR (loss might be NaN)
3. **Data issue**: Check dataset format
4. **Frozen weights**: Ensure LoRA is actually training

## Recovery Actions

### Delete and Retry

```python
delete_training_job(name="failed-job")

# Fix the issue, then resubmit
fine_tune(..., confirmed=True)
```

### Suspend and Resume

For temporary resource issues (uses direct K8s API, not SDK):

```python
suspend_training_job(name="my-job")
# Wait for resources...
resume_training_job(name="my-job")
```

Note: These tools patch the TrainJob CRD directly via Kubernetes API since the SDK doesn't expose suspend/resume methods.

### Check Multiple Steps

Training jobs have multiple containers (init, trainer):

```python
# Check different steps
get_training_logs(name="my-job", step="node-0")
get_training_logs(name="my-job", step="model-initializer")
get_training_logs(name="my-job", step="dataset-initializer")
```

## Event Reference

| Event Reason | Meaning |
|--------------|---------|
| `Scheduled` | Pod assigned to node |
| `Pulling` | Pulling container image |
| `Pulled` | Image pulled successfully |
| `Created` | Container created |
| `Started` | Container started |
| `Killing` | Container being terminated |
| `FailedScheduling` | No suitable node found |
| `FailedMount` | Volume mount failed |
| `OOMKilled` | Out of memory |
| `BackOff` | Container crash loop |

## Getting Help

If issues persist:

1. **Collect diagnostics**:
   ```python
   get_training_job(name="my-job")
   get_training_events(name="my-job")
   get_training_logs(name="my-job")
   ```

2. **Check cluster status**:
   ```python
   get_cluster_resources()
   list_runtimes()
   ```

3. **Report issue** with:
   - Job configuration (from preview)
   - Events and logs
   - Cluster resource status
